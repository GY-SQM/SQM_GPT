"""
patch_available_sample_fix.py  (v8.6.9)
Available 화면 샘플 정합성 수정

변경 대상:
  frontend/js/sqm-inventory.js  (1239줄, IIFE → 패치 스크립트 처리)

변경 내용 5가지 (Available 뷰 loadAvailablePage 함수):
  ① sumSampleMt 합산 변수 추가
  ② 헤더 요약 텍스트: '톤백 X MT + 🧪 샘플 Y MT' 분리 표시
  ③ SP 서브행: PRODUCT = product + ' (Sample)' + STATUS = ✅ AVAILABLE 뱃지
  ④ 메인 LOT 행: BALANCE = balance - sample_weight_mt (샘플 제외)
  ⑤ Footer 2행: 📦 톤백 합계(노란) / 🧪 샘플 합계(연노란) 분리

실행: python scripts/patch_available_sample_fix.py
"""
import pathlib, shutil, datetime

ROOT   = pathlib.Path(__file__).resolve().parent.parent
TARGET = ROOT / "frontend" / "js" / "sqm-inventory.js"
TS     = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def backup(p: pathlib.Path):
    bak = p.with_suffix(p.suffix + f".bak_smpfix_{TS}")
    shutil.copy2(p, bak)
    print(f"  📦 백업: {bak.name}")


def patch(src: str) -> str:
    total = 0

    # ── ① sumSampleMt 합산 변수 추가 ───────────────────────────────
    OLD1 = "      var sumBal = 0, sumNet = 0, sumIni = 0, sumOb = 0;\n"
    NEW1 = "      var sumBal = 0, sumNet = 0, sumIni = 0, sumOb = 0, sumSampleMt = 0;\n"
    if OLD1 in src:
        src = src.replace(OLD1, NEW1, 1)
        print("  ✅  [①] sumSampleMt 변수 추가")
        total += 1
    else:
        print("  ⚠️  [①] sumBal 초기화 패턴 미발견")

    # ── ① 루프 안에서 sumSampleMt 누적 ─────────────────────────────
    OLD1b = (
        "        if (r.outbound_weight != null) sumOb  += Number(r.outbound_weight);\n"
        "      });\n"
        "      var html = '<section"
    )
    NEW1b = (
        "        if (r.outbound_weight != null) sumOb  += Number(r.outbound_weight);\n"
        "        if (r.sample_weight_mt != null && !isNaN(Number(r.sample_weight_mt))) sumSampleMt += Number(r.sample_weight_mt);\n"
        "      });\n"
        "      var html = '<section"
    )
    if OLD1b in src:
        src = src.replace(OLD1b, NEW1b, 1)
        print("  ✅  [①b] sumSampleMt 누적 추가")
        total += 1
    else:
        print("  ⚠️  [①b] sumOb 누적 패턴 미발견")

    # ── ② 헤더 요약: 'Balance X MT' → '톤백 X MT + 🧪 샘플 Y MT' ──
    OLD2 = (
        "        + '<span style=\"font-size:12px;color:var(--text-muted)\">' + rows.length + ' LOT · Balance ' + fmtN(sumBal) + ' MT</span>'\n"
    )
    NEW2 = (
        "        + '<span style=\"font-size:12px;color:var(--text-muted)\">' + rows.length + ' LOT · 📦 ' + fmtN(sumBal - sumSampleMt) + ' MT'"
        " + (sumSampleMt > 0 ? ' + 🧪 샘플 ' + fmtN(sumSampleMt) + ' MT' : '') + '</span>'\n"
    )
    if OLD2 in src:
        src = src.replace(OLD2, NEW2, 1)
        print("  ✅  [②] 헤더 요약 텍스트 분리")
        total += 1
    else:
        print("  ⚠️  [②] 헤더 요약 패턴 미발견")

    # ── ③ SP 서브행: PRODUCT + STATUS 동시 수정 ─────────────────────
    # Available 뷰의 SP 행 (공백 있는 ' + escapeHtml 스타일)
    OLD3 = (
        "            '<td><span class=\"tag\" style=\"background:rgba(234,179,8,0.2);color:#eab308\">' + escapeHtml(r.product||'') + '</span></td>' +\n"
        "            '<td style=\"color:#eab308;font-weight:600\">SAMPLE</td>' +\n"
    )
    NEW3 = (
        "            '<td><span class=\"tag\" style=\"background:rgba(234,179,8,0.2);color:#eab308\">' + escapeHtml((r.product||'') + ' (Sample)') + '</span></td>' +\n"
        "            '<td><span class=\"tag\" style=\"background:rgba(34,197,94,0.15);color:#22c55e;font-weight:700\">✅ AVAILABLE</span></td>' +\n"
    )
    if OLD3 in src:
        src = src.replace(OLD3, NEW3, 1)
        print("  ✅  [③] SP 행 PRODUCT(Sample) + STATUS(AVAILABLE 뱃지) 수정")
        total += 1
    else:
        print("  ⚠️  [③] SP 행 PRODUCT/STATUS 패턴 미발견")

    # ── ④ 메인 LOT 행 BALANCE: balance → balance - sample_weight_mt ─
    OLD4 = (
        "          + '<td class=\"mono-cell\" style=\"text-align:right\">' + (r.balance!=null?fmtN(r.balance):'-') + '</td>'\n"
        "          + '<td title=\"앞=가용 중량(MT, 바로 배분 가능) / 뒤=예약(RESERVED) 중량.  예: 3.000/▲2.000 → 총 5MT 중 2MT 예약·3MT 배분 가능\" class=\"mono-cell\" style=\"text-align:right\">'\n"
    )
    NEW4 = (
        "          + '<td class=\"mono-cell\" style=\"text-align:right\">' + (r.balance!=null?fmtN((r.balance||0)-(r.sample_weight_mt||0)):'-') + '</td>'\n"
        "          + '<td title=\"앞=가용 중량(MT, 바로 배분 가능) / 뒤=예약(RESERVED) 중량.  예: 3.000/▲2.000 → 총 5MT 중 2MT 예약·3MT 배분 가능\" class=\"mono-cell\" style=\"text-align:right\">'\n"
    )
    if OLD4 in src:
        src = src.replace(OLD4, NEW4, 1)
        print("  ✅  [④] 메인 LOT BALANCE = balance - sample_weight_mt")
        total += 1
    else:
        print("  ⚠️  [④] 메인 BALANCE 패턴 미발견")

    # ── ⑤ Footer tfoot: 1행 → 2행 (톤백/샘플 분리) ─────────────────
    OLD5 = (
        "      html += '</tbody><tfoot><tr style=\"background:#FFD600;font-weight:800;color:#222\">';\n"
        "      html += '<td colspan=\"7\" style=\"text-align:right;padding:8px 10px\">합계 (' + rows.length + ' LOT)</td>';\n"
        "      html += '<td class=\"mono-cell\" style=\"text-align:right\">' + fmtN(sumBal) + '</td>';\n"
        "      html += '<td></td>';\n"
        "      html += '<td class=\"mono-cell\" style=\"text-align:right\">' + fmtN(sumNet) + '</td>';\n"
        "      html += '<td colspan=\"9\"></td>';\n"
        "      html += '<td class=\"mono-cell\" style=\"text-align:right\">' + fmtN(sumIni) + '</td>';\n"
        "      html += '<td colspan=\"2\"></td>';\n"
        "      html += '</tr></tfoot></table></div></section>';\n"
    )
    NEW5 = (
        "      var sumRegBal = Math.max(0, (sumBal||0) - (sumSampleMt||0));\n"
        "      html += '</tbody><tfoot>';\n"
        "      html += '<tr style=\"background:#FFD600;font-weight:800;color:#222\">';\n"
        "      html += '<td colspan=\"7\" style=\"text-align:right;padding:8px 10px\">📦 톤백 합계 (' + rows.length + ' LOT)</td>';\n"
        "      html += '<td class=\"mono-cell\" style=\"text-align:right\">' + fmtN(sumRegBal) + '</td>';\n"
        "      html += '<td></td>';\n"
        "      html += '<td class=\"mono-cell\" style=\"text-align:right\">' + fmtN(sumNet) + '</td>';\n"
        "      html += '<td colspan=\"9\"></td>';\n"
        "      html += '<td class=\"mono-cell\" style=\"text-align:right\">' + fmtN(sumIni) + '</td>';\n"
        "      html += '<td colspan=\"2\"></td>';\n"
        "      html += '</tr>';\n"
        "      if (sumSampleMt > 0) {\n"
        "        html += '<tr style=\"background:#FFF9C4;font-weight:800;color:#92400e\">';\n"
        "        html += '<td colspan=\"7\" style=\"text-align:right;padding:6px 10px\">🧪 샘플 합계</td>';\n"
        "        html += '<td class=\"mono-cell\" style=\"text-align:right\">' + fmtN(sumSampleMt) + '</td>';\n"
        "        html += '<td colspan=\"12\"></td>';\n"
        "        html += '</tr>';\n"
        "      }\n"
        "      html += '</tfoot></table></div></section>';\n"
    )
    if OLD5 in src:
        src = src.replace(OLD5, NEW5, 1)
        print("  ✅  [⑤] Footer 2행 분리 (톤백/샘플)")
        total += 1
    else:
        print("  ⚠️  [⑤] Footer tfoot 패턴 미발견")

    print(f"\n  📊 총 {total}/6 패치 적용")
    return src


def main():
    print("\n=== patch_available_sample_fix.py 시작 ===\n")
    print(f"[{TARGET.name}]")
    src = TARGET.read_text(encoding="utf-8")
    backup(TARGET)
    patched = patch(src)
    if patched != src:
        TARGET.write_text(patched, encoding="utf-8")
        print("  💾  저장 완료")
    else:
        print("  ℹ️   변경 없음")
    print("\n=== 패치 완료 ===")


if __name__ == "__main__":
    main()
