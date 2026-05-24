"""
patch_yellow_footer.py  (v8.6.9)
전체 화면 합계바/footer 노란 배경 일괄 적용 패치

대상:
  1. sqm-listview.js    — 톤백 리스트 모달 footer 노란 배경
  2. sqm-inventory.js   — Available 합계 tfoot 노란 배경 (2곳)
  3. sqm-allocation.js  — Allocation 합계 tfoot 노란 배경
  4. sqm-picked.js      — Picked 그룹헤더 summary 노란 배경
  5. sqm-logistics.js   — Inbound count 스타일 + Outbound 전체 합계 footer

실행: python scripts/patch_yellow_footer.py
"""
import pathlib, shutil, datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent
JS   = ROOT / "frontend" / "js"
TS   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

# 공통 노란 배경 스타일 상수
YELLOW_BADGE = (
    "display:inline-block;padding:4px 18px;margin-right:10px;"
    "background:#FFD600;border-radius:8px;"
    "font-size:14px;color:#222;font-weight:800;"
    "box-shadow:0 1px 4px rgba(0,0,0,.25);"
)
YELLOW_TFOOT = "background:#FFD600;font-weight:800;color:#222"


def backup(p: pathlib.Path):
    bak = p.with_suffix(p.suffix + f".bak_yfooter_{TS}")
    shutil.copy2(p, bak)
    print(f"  📦 백업: {bak.name}")


def apply(src: str, old: str, new: str, label: str) -> str:
    if old not in src:
        print(f"  ⚠️  [{label}] 패턴 미발견 — 이미 패치됐거나 코드 변경됨")
        return src
    result = src.replace(old, new, 1)
    print(f"  ✅  [{label}] 적용 완료")
    return result


# ─────────────────────────────────────────────────────────────────
# 1. sqm-listview.js — _renderTonbagFooter 노란 배경
# ─────────────────────────────────────────────────────────────────
def patch_listview(src: str) -> str:
    OLD = (
        "  /* -- Tonbag footer totals bar ------------------------------------- */\n"
        "  function _renderTonbagFooter(foot, rows) {\n"
        "    var totalWeight = 0;\n"
        "    rows.forEach(function(r) {\n"
        "      totalWeight += Number(r.weight_kg || 0);\n"
        "    });\n"
        "    var s = 'display:inline-block;padding:2px 14px;margin-right:8px;'\n"
        "          + 'background:rgba(79,195,247,0.13);border-radius:6px;'\n"
        "          + 'font-size:12px;color:var(--accent,#4fc3f7);font-weight:700;';\n"
        "    var hint = 'font-size:11px;color:var(--text-muted);margin-left:6px;';\n"
        "    foot.innerHTML =\n"
        "        '<span style=\"' + s + '\">🎒 톤백 ' + rows.length.toLocaleString('ko-KR') + ' 건</span>'\n"
        "      + '<span style=\"' + s + '\">⚖ 총 중량 ' + totalWeight.toLocaleString('ko-KR', {maximumFractionDigits:2}) + ' kg</span>'\n"
        "      + '<span style=\"' + hint + '\">※ 엑셀 다운로드는 우상단 버튼 사용</span>';\n"
        "  }"
    )
    NEW = (
        "  /* -- Tonbag footer totals bar (v8.6.9: 노란배경) ----------------- */\n"
        "  function _renderTonbagFooter(foot, rows) {\n"
        "    var totalWeight = 0, totalSample = 0, totalRegular = 0;\n"
        "    rows.forEach(function(r) {\n"
        "      totalWeight  += Number(r.weight_kg  || 0);\n"
        "      if (r.is_sample) totalSample++;  else totalRegular++;\n"
        "    });\n"
        "    var s = 'display:inline-block;padding:4px 18px;margin-right:10px;'\n"
        "          + 'background:#FFD600;border-radius:8px;'\n"
        "          + 'font-size:14px;color:#222;font-weight:800;'\n"
        "          + 'box-shadow:0 1px 4px rgba(0,0,0,.25);';\n"
        "    var hint = 'font-size:11px;color:var(--text-muted);margin-left:4px;';\n"
        "    var tbStr = (totalSample > 0)\n"
        "      ? '🧱 ' + totalRegular + '개 + 🧪 샘플 ' + totalSample + '개'\n"
        "      : rows.length.toLocaleString('ko-KR') + ' 건';\n"
        "    foot.innerHTML =\n"
        "        '<span style=\"' + s + '\">🎒 톤백 ' + tbStr + '</span>'\n"
        "      + '<span style=\"' + s + '\">⚖ 총 중량 ' + totalWeight.toLocaleString('ko-KR', {maximumFractionDigits:2}) + ' kg</span>'\n"
        "      + '<span style=\"' + hint + '\">※ 엑셀 다운로드는 우상단 버튼 사용</span>';\n"
        "  }"
    )
    return apply(src, OLD, NEW, "listview: _renderTonbagFooter")


# ─────────────────────────────────────────────────────────────────
# 2. sqm-inventory.js — tfoot 노란 배경 (Available + Sold 2곳)
# ─────────────────────────────────────────────────────────────────
def patch_inventory(src: str) -> str:
    OLD1 = "html += '</tbody><tfoot><tr style=\"background:var(--panel);font-weight:700\">';"
    NEW1 = f"html += '</tbody><tfoot><tr style=\"{YELLOW_TFOOT}\">';"

    # 두 곳 모두 동일한 패턴 → replace_all 방식
    if OLD1 not in src:
        print("  ⚠️  [inventory: tfoot] 패턴 미발견")
        return src
    count = src.count(OLD1)
    result = src.replace(OLD1, NEW1)
    print(f"  ✅  [inventory: tfoot 노란배경] {count}곳 적용 완료")
    return result


# ─────────────────────────────────────────────────────────────────
# 3. sqm-allocation.js — tfoot 노란 배경
# ─────────────────────────────────────────────────────────────────
def patch_allocation(src: str) -> str:
    OLD = (
        "    tfoot.innerHTML =\n"
        "      '<tr style=\"background:var(--panel);font-weight:700\">' +"
    )
    NEW = (
        "    tfoot.innerHTML =\n"
        f"      '<tr style=\"{YELLOW_TFOOT}\">' +"
    )
    return apply(src, OLD, NEW, "allocation: tfoot 노란배경")


# ─────────────────────────────────────────────────────────────────
# 4. sqm-picked.js — 그룹헤더 summary 노란 배지 스타일
# ─────────────────────────────────────────────────────────────────
def patch_picked(src: str) -> str:
    OLD = (
        "        + '<span style=\"font-size:12px;color:var(--text-muted)\">' + lots.length + ' LOT · ' + sumBags + ' Bags · ' + fmtN(sumKg) + ' kg</span>'\n"
        "        + '<span style=\"font-size:11px;color:var(--text-muted);margin-left:auto\">'\n"
        "        + '<span style=\"color:#22c55e\">A ' + sumAvail + '</span> · '\n"
        "        + '<span style=\"color:#3b82f6\">R ' + sumReserved + '</span> · '\n"
        "        + '<span style=\"color:#f59e0b\">P ' + sumPacked + '</span>'\n"
        "        + '</span>'"
    )
    NEW = (
        "        + '<span style=\"display:inline-block;padding:3px 14px;margin-right:6px;"
        "background:#FFD600;border-radius:6px;font-size:13px;color:#222;font-weight:800;"
        "box-shadow:0 1px 3px rgba(0,0,0,.2);\">'\n"
        "        + lots.length + ' LOT · ' + sumBags + ' Bags · ' + fmtN(sumKg) + ' kg</span>'\n"
        "        + '<span style=\"font-size:11px;color:var(--text-muted);margin-left:auto\">'\n"
        "        + '<span style=\"color:#22c55e;font-weight:700\">A ' + sumAvail + '</span> · '\n"
        "        + '<span style=\"color:#3b82f6;font-weight:700\">R ' + sumReserved + '</span> · '\n"
        "        + '<span style=\"color:#f59e0b;font-weight:700\">P ' + sumPacked + '</span>'\n"
        "        + '</span>'"
    )
    return apply(src, OLD, NEW, "picked: 그룹헤더 노란배지")


# ─────────────────────────────────────────────────────────────────
# 5. sqm-logistics.js
#    (A) Inbound count 텍스트 → 노란 배지 스타일
#    (B) Outbound tbody 렌더 후 전체 합계 tfoot 추가
# ─────────────────────────────────────────────────────────────────
def patch_logistics(src: str) -> str:

    # 5-A: inbound-count 스타일 강화
    OLD_A = (
        "    if (count) count.textContent = filtered.length + ' / ' + _inboundAllRows.length + '건';"
    )
    NEW_A = (
        "    if (count) {\n"
        "      count.style.cssText = 'display:inline-block;padding:3px 14px;'\n"
        "        + 'background:#FFD600;border-radius:6px;font-size:13px;'\n"
        "        + 'color:#222;font-weight:800;box-shadow:0 1px 3px rgba(0,0,0,.2);';\n"
        "      count.textContent = '📦 ' + filtered.length + ' / ' + _inboundAllRows.length + ' 건';\n"
        "    }"
    )
    src = apply(src, OLD_A, NEW_A, "logistics: inbound-count 노란배지")

    # 5-B: Outbound tbody 렌더 후 합계 tfoot 추가
    OLD_B = (
        "      document.getElementById('outbound-table').style.display = '';\n"
        "      dbgLog('📤','outbound-page','rows='+rows.length,'#4caf50');"
    )
    NEW_B = (
        "      /* v8.6.9: 전체 합계 tfoot */\n"
        "      var _outTbl = document.getElementById('outbound-table');\n"
        "      var _outTfoot = _outTbl ? _outTbl.querySelector('tfoot') : null;\n"
        "      if (_outTbl && !_outTfoot) {\n"
        "        var _sumTb = 0, _sumKg = 0;\n"
        "        rows.forEach(function(r) {\n"
        "          _sumTb += Number(r.tonbag_count || 0);\n"
        "          _sumKg += Number(r.total_kg     || 0);\n"
        "        });\n"
        "        var _tf = document.createElement('tfoot');\n"
        "        _tf.innerHTML = '<tr style=\"" + YELLOW_TFOOT + ";font-size:13px\">'\n"
        "          + '<td colspan=\"4\" style=\"text-align:right;padding:6px 10px\">'\n"
        "          + '합계 ' + rows.length + ' LOT</td>'\n"
        "          + '<td></td><td></td>'\n"
        "          + '<td class=\"mono-cell\" style=\"text-align:right;padding:6px 8px\">'\n"
        "          + _sumTb.toLocaleString('ko-KR') + ' 개</td>'\n"
        "          + '<td class=\"mono-cell\" style=\"text-align:right;padding:6px 8px\">'\n"
        "          + fmtN(_sumKg) + ' kg</td>'\n"
        "          + '<td></td></tr>';\n"
        "        _outTbl.appendChild(_tf);\n"
        "      }\n"
        "      _outTbl.style.display = '';\n"
        "      dbgLog('📤','outbound-page','rows='+rows.length,'#4caf50');"
    )
    src = apply(src, OLD_B, NEW_B, "logistics: outbound 전체 합계 tfoot")

    return src


# ─────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────
def main():
    print("\n=== patch_yellow_footer.py 시작 ===\n")

    jobs = [
        (JS / "sqm-listview.js",   patch_listview,   "sqm-listview.js"),
        (JS / "sqm-inventory.js",  patch_inventory,  "sqm-inventory.js"),
        (JS / "sqm-allocation.js", patch_allocation, "sqm-allocation.js"),
        (JS / "sqm-picked.js",     patch_picked,     "sqm-picked.js"),
        (JS / "sqm-logistics.js",  patch_logistics,  "sqm-logistics.js"),
    ]

    for path, fn, label in jobs:
        print(f"[{label}]")
        src = path.read_text(encoding="utf-8")
        backup(path)
        patched = fn(src)
        if patched != src:
            path.write_text(patched, encoding="utf-8")
            print(f"  💾  저장 완료\n")
        else:
            print(f"  ℹ️   변경 없음\n")

    print("=== 패치 완료 ===")


if __name__ == "__main__":
    main()
