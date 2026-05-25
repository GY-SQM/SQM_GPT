#!/usr/bin/env python3
"""
patch_footer_logistics.py
=========================
sqm-logistics.js — 3개 변경 (v8.6.9)

변경 1 (Sold):   기존 tfoot font-size:13px → font-size:19px
변경 2 (Return): tfoot 없음 → 노란 합계 tfoot 삽입 (Balance(MT) 합계, 16컬럼)
변경 3 (Move):   tfoot 없음 → 노란 합계 tfoot 삽입 (Qty(MT) 합계, 8컬럼)

대상: frontend/js/sqm-logistics.js (IIFE, ABSOLUTE EDIT BAN)
방식: bytes 레벨 find & replace (3회)
"""
import sys, os, shutil, subprocess
from datetime import datetime

BASE   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(BASE, 'frontend', 'js', 'sqm-logistics.js')

# ── 패치 1: Sold tfoot font-size 13→19 ───────────────────────────────
P1_OLD = b"        _tf.innerHTML = '<tr style=\"background:#FFD600;font-weight:800;color:#222;font-size:13px\">'\n"
P1_NEW = b"        _tf.innerHTML = '<tr style=\"background:#FFD600;font-weight:800;color:#222;font-size:19px\">'\n"

# ── 패치 2: Return tfoot 삽입 ─────────────────────────────────────────
# 앵커: html += '</tbody>...</section>'; container.innerHTML = html;
P2_OLD = (
    b"    html += '</tbody></table></div></section>';\n"
    b"    container.innerHTML = html;\n"
    b"  }\n"
    b"\n"
    b"  /* \xeb\xb0\x98\xed\x92\x88 \xea\xb2\x80\xec\x82\xac\xec\x99\x84\xeb\xa3\x8c"
    b" \xe2\x86\x92 AVAILABLE \xec\xa0\x84\xed\x99\x98 */\n"
)

P2_NEW = (
    b"    // v8.6.9 \xeb\x85\xb8\xeb\x9e\x80 tfoot \xed\x95\xa9\xea\xb3\x84 (Return)\n"
    b"    html += '<tfoot>'\n"
    b"      + '<tr style=\"background:#FFD600;font-weight:800;color:#222;font-size:19px\">'\n"
    b"      + '<td colspan=\"6\" style=\"text-align:right;padding:6px 10px\">'\n"
    b"      + '\xed\x95\xa9\xea\xb3\x84 ' + rows.length + ' LOT</td>'\n"
    b"      + '<td class=\"mono-cell\" style=\"text-align:right;padding:6px 8px\">'\n"
    b"      + fmtN(sumBal) + ' MT</td>'\n"
    b"      + '<td colspan=\"9\"></td>'\n"
    b"      + '</tr></tfoot>';\n"
    b"    html += '</tbody></table></div></section>';\n"
    b"    container.innerHTML = html;\n"
    b"  }\n"
    b"\n"
    b"  /* \xeb\xb0\x98\xed\x92\x88 \xea\xb2\x80\xec\x82\xac\xec\x99\x84\xeb\xa3\x8c"
    b" \xe2\x86\x92 AVAILABLE \xec\xa0\x84\xed\x99\x98 */\n"
)

# ── 패치 3: Move tfoot 삽입 ──────────────────────────────────────────
# 앵커: ).join(''); + move-table show
P3_OLD = (
    b"      }).join('');\n"
    b"      document.getElementById('move-table').style.display = '';\n"
)

P3_NEW = (
    b"      }).join('');\n"
    b"      // v8.6.9 \xeb\x85\xb8\xeb\x9e\x80 tfoot \xed\x95\xa9\xea\xb3\x84 (Move)\n"
    b"      (function() {\n"
    b"        var _sumQty = 0;\n"
    b"        rows.forEach(function(r) {\n"
    b"          _sumQty += r.qty_mt != null ? Number(r.qty_mt) :\n"
    b"                     (r.qty_kg != null ? Number(r.qty_kg) / 1000 : 0);\n"
    b"        });\n"
    b"        var _moveTbl = document.getElementById('move-table');\n"
    b"        if (_moveTbl && !_moveTbl.querySelector('tfoot')) {\n"
    b"          var _tf = document.createElement('tfoot');\n"
    b"          _tf.innerHTML =\n"
    b"            '<tr style=\"background:#FFD600;font-weight:800;color:#222;font-size:19px\">'\n"
    b"            + '<td colspan=\"4\" style=\"text-align:right;padding:6px 10px\">'\n"
    b"            + '\xed\x95\xa9\xea\xb3\x84 ' + rows.length + '\xea\xb1\xb4</td>'\n"
    b"            + '<td class=\"mono-cell\" style=\"text-align:right;padding:6px 8px\">'\n"
    b"            + (typeof fmtN === 'function' ? fmtN(_sumQty) : _sumQty.toFixed(3)) + ' MT</td>'\n"
    b"            + '<td colspan=\"3\"></td>'\n"
    b"            + '</tr>';\n"
    b"          _moveTbl.appendChild(_tf);\n"
    b"        }\n"
    b"      })();\n"
    b"      document.getElementById('move-table').style.display = '';\n"
)

PATCHES = [
    ("Sold tfoot font-size:13→19",   P1_OLD, P1_NEW),
    ("Return tfoot 삽입",             P2_OLD, P2_NEW),
    ("Move tfoot 삽입",               P3_OLD, P3_NEW),
]

def try_variants(data, old):
    if old in data:
        return old, old, "LF"
    cr = old.replace(b'\n', b'\r\n')
    if cr in data:
        return cr, old, "CRLF"
    return None, None, None

def main():
    if not os.path.exists(TARGET):
        print(f"❌ 파일 없음: {TARGET}")
        sys.exit(1)

    with open(TARGET, 'rb') as f:
        data = f.read()

    bak = TARGET + '.bak_footer_log_' + datetime.now().strftime('%Y%m%d_%H%M%S')
    shutil.copy2(TARGET, bak)
    print(f"📦 백업: {bak}")

    changed = False
    for label, old, new in PATCHES:
        anchor, _, mode = try_variants(data, old)
        if anchor is None:
            print(f"⚠️  [{label}] 앵커 없음 — 이미 적용됐거나 스킵")
            continue
        rep = new if mode == "LF" else new.replace(b'\n', b'\r\n')
        cnt = data.count(anchor)
        if cnt > 1:
            print(f"⚠️  [{label}] 앵커 {cnt}개 — 첫 번째만 치환")
        data = data.replace(anchor, rep, 1)
        print(f"✅ [{label}] 적용 ({mode})")
        changed = True

    if not changed:
        print("ℹ️  변경 없음")
        return

    with open(TARGET, 'wb') as f:
        f.write(data)
    print(f"✅ 저장 완료 ({len(data)} bytes)")

    result = subprocess.run(['node', '--check', TARGET], capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ node --check 통과")
    else:
        print("❌ node --check 실패 — 백업 복원")
        print(result.stderr)
        shutil.copy2(bak, TARGET)
        sys.exit(1)

if __name__ == '__main__':
    main()
