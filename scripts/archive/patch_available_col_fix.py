"""
patch_available_col_fix.py  (v8.6.9)
Available 화면 컬럼 정리 + 제품명 형식 수정

변경 대상:
  frontend/js/sqm-inventory.js  (IIFE → 패치 스크립트 처리)

변경 내용 4가지 (Available 뷰 loadAvailablePage):
  ① SP 행 PRODUCT: '(Sample)' → '(SP)'
  ② 헤더: Ship 컬럼 삭제 + Arrival 뒤에 Inbound 컬럼 추가
  ③ SP 행: ship_date td 제거 + arrival 뒤에 inbound(r.date) td 추가
  ④ 메인 LOT 행: ship_date td 제거 + arrival 뒤에 inbound(r.date) td 추가

실행: python scripts/patch_available_col_fix.py
"""
import pathlib, shutil, datetime

ROOT   = pathlib.Path(__file__).resolve().parent.parent
TARGET = ROOT / "frontend" / "js" / "sqm-inventory.js"
TS     = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def backup(p: pathlib.Path):
    bak = p.with_suffix(p.suffix + f".bak_colfx_{TS}")
    shutil.copy2(p, bak)
    print(f"  📦 백업: {bak.name}")


def patch(src: str) -> str:
    total = 0

    # ── ① SP 행 PRODUCT: '(Sample)' → '(SP)' ───────────────────────
    OLD1 = "escapeHtml((r.product||'') + ' (Sample)')"
    NEW1 = "escapeHtml((r.product||'') + ' (SP)')"
    if OLD1 in src:
        src = src.replace(OLD1, NEW1)          # 모든 뷰 일괄 적용
        print("  ✅  [①] PRODUCT '(Sample)' → '(SP)' 수정")
        total += 1
    else:
        print("  ⚠️  [①] (Sample) 패턴 미발견")

    # ── ② 헤더: Ship 삭제 + Inbound 추가 (Available 뷰) ─────────────
    OLD2 = "        + '<th>Ship</th><th>Arrival</th><th>Con Return</th><th>Free</th><th>WH</th>'\n"
    NEW2 = "        + '<th>Arrival</th><th title=\"실제 창고 반입일 (Inbound Date)\" style=\"color:#4fc3f7\">🏭 Inbound</th><th>Con Return</th><th>Free</th><th>WH</th>'\n"
    if OLD2 in src:
        src = src.replace(OLD2, NEW2, 1)
        print("  ✅  [②] 헤더 Ship 삭제 + 🏭 Inbound 추가")
        total += 1
    else:
        print("  ⚠️  [②] 헤더 Ship/Arrival 패턴 미발견")

    # ── ③ SP 행: ship_date 제거 + arrival 뒤에 inbound(r.date) 추가 ─
    OLD3 = (
        "            '<td class=\"mono-cell\" style=\"color:#94a3b8\">' + escapeHtml((r.ship_date||'').slice(0,10)) + '</td>' +\n"
        "            '<td class=\"mono-cell\" style=\"color:#94a3b8\">' + escapeHtml((r.arrival_date||'').slice(0,10)) + '</td>' +\n"
        "            '<td class=\"mono-cell\" style=\"color:#94a3b8\">' + escapeHtml((r.con_return||'').slice(0,10)) + '</td>' +\n"
    )
    NEW3 = (
        "            '<td class=\"mono-cell\" style=\"color:#94a3b8\">' + escapeHtml((r.arrival_date||'').slice(0,10)) + '</td>' +\n"
        "            '<td class=\"mono-cell\" style=\"color:#4fc3f7;font-weight:600\">' + (escapeHtml((r.date||'').slice(0,10)) || '-') + '</td>' +\n"
        "            '<td class=\"mono-cell\" style=\"color:#94a3b8\">' + escapeHtml((r.con_return||'').slice(0,10)) + '</td>' +\n"
    )
    if OLD3 in src:
        src = src.replace(OLD3, NEW3, 1)
        print("  ✅  [③] SP 행 ship_date 제거 + Inbound(r.date) td 추가")
        total += 1
    else:
        print("  ⚠️  [③] SP 행 ship/arrival 패턴 미발견")

    # ── ④ 메인 LOT 행: ship_date 제거 + arrival 뒤에 inbound(r.date) 추가 ─
    OLD4 = (
        "          + '<td class=\"mono-cell\">' + escapeHtml((r.ship_date||'').slice(0,10)) + '</td>'\n"
        "          + '<td class=\"mono-cell\">' + escapeHtml((r.arrival_date||'').slice(0,10)) + '</td>'\n"
        "          + '<td class=\"mono-cell\">' + escapeHtml((r.con_return||'').slice(0,10)) + '</td>'\n"
    )
    NEW4 = (
        "          + '<td class=\"mono-cell\">' + escapeHtml((r.arrival_date||'').slice(0,10)) + '</td>'\n"
        "          + '<td class=\"mono-cell\" style=\"color:#4fc3f7;font-weight:600\">' + (escapeHtml((r.date||'').slice(0,10)) || '-') + '</td>'\n"
        "          + '<td class=\"mono-cell\">' + escapeHtml((r.con_return||'').slice(0,10)) + '</td>'\n"
    )
    if OLD4 in src:
        src = src.replace(OLD4, NEW4, 1)
        print("  ✅  [④] 메인 LOT 행 ship_date 제거 + Inbound(r.date) td 추가")
        total += 1
    else:
        print("  ⚠️  [④] 메인 LOT 행 ship/arrival 패턴 미발견")

    print(f"\n  📊 총 {total}/4 패치 적용")
    return src


def main():
    print("\n=== patch_available_col_fix.py 시작 ===\n")
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
