#!/usr/bin/env python3
"""
patch_alloc_sp_grouping.py
==========================
Allocation 화면 — LOT 아래에 샘플(SP) 서브행 삽입
  _renderAllocTable() 의 rows.map(...) return 마지막 '</tr>' 뒤에
  sample_bags > 0 일 때 SP 서브행 <tr> 을 추가한다.

대상: frontend/js/sqm-allocation.js  (IIFE ≥ 925줄, Edit 금지)
방식: bytes 레벨 find & replace (IIFE 구조 보존)
"""
import sys
import os
import shutil
import subprocess
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JS   = os.path.join(BASE, 'frontend', 'js', 'sqm-allocation.js')

# ── 앵커: 행 템플릿 마지막 '</tr>'; 와 }).join(''); ─────────────────
OLD = b"        '</tr>';\n    }).join('');"

NEW = (
    b"        '</tr>' +\n"
    b"        (Number(r.sample_bags || 0) > 0 ? (\n"
    b"          '<tr class=\"alloc-sample-subrow\" data-lot=\"' + lot + '\" style=\"background:#2a2200;font-size:.85em\">' +\n"
    b"          '<td></td><td></td>' +\n"
    b"          '<td class=\"mono-cell cell-left\" style=\"padding-left:28px;color:#f59e0b;font-style:italic\">\xe2\x8c\x9e ' + lot + '(SP)</td>' +\n"
    b"          '<td class=\"mono-cell\">' + escapeHtml(r.sap_no || '-') + '</td>' +\n"
    b"          '<td style=\"color:#f59e0b;font-style:italic\">' + escapeHtml((r.product || '') + ' (SP)') + '</td>' +\n"
    b"          '<td class=\"mono-cell\" style=\"text-align:right\">' + Number(r.sample_mt || 0).toFixed(4) + '</td>' +\n"
    b"          '<td class=\"mono-cell\" style=\"text-align:center\">1</td>' +\n"
    b"          '<td class=\"mono-cell\" style=\"text-align:center;color:#22c55e\">' + Number(r.sample_avail || 0) + '</td>' +\n"
    b"          '<td class=\"mono-cell\" style=\"text-align:center;color:#3b82f6\">-</td>' +\n"
    b"          '<td class=\"mono-cell\" style=\"text-align:center;color:#f59e0b\">-</td>' +\n"
    b"          '<td class=\"mono-cell\" style=\"text-align:center\">' + Number(r.sample_bags || 0) + '</td>' +\n"
    b"          '<td class=\"mono-cell\" style=\"text-align:center\">-</td>' +\n"
    b"          '<td></td><td></td><td></td>' +\n"
    b"          '<td>' + escapeHtml(r.customer || r.sold_to || '-') + '</td>' +\n"
    b"          '<td class=\"mono-cell\">' + escapeHtml(r.sale_ref || '-') + '</td>' +\n"
    b"          '<td class=\"mono-cell\">' + escapeHtml(r.outbound_date || r.ship_date || '-') + '</td>' +\n"
    b"          '<td>' + escapeHtml(r.warehouse || r.wh || '-') + '</td>' +\n"
    b"          '<td><span class=\"tag\" style=\"background:#78350f;color:#fef3c7;font-weight:700\">SAMPLE</span></td>' +\n"
    b"          '</tr>'\n"
    b"        ) : '');\n"
    b"    }).join('');"
)

def main():
    if not os.path.exists(JS):
        print(f"❌ 파일 없음: {JS}")
        sys.exit(1)

    with open(JS, 'rb') as f:
        data = f.read()

    count = data.count(OLD)
    if count == 0:
        print("❌ 앵커를 찾지 못했습니다. 이미 적용됐거나 파일이 변경됐습니다.")
        sys.exit(1)
    if count > 1:
        print(f"⚠️  앵커가 {count}곳 — 첫 번째만 치환합니다.")

    # 백업
    bak = JS + '.bak_sprow_' + datetime.now().strftime('%Y%m%d_%H%M%S')
    shutil.copy2(JS, bak)
    print(f"📦 백업: {bak}")

    new_data = data.replace(OLD, NEW, 1)
    with open(JS, 'wb') as f:
        f.write(new_data)
    print(f"✅ 패치 완료 ({len(data)} → {len(new_data)} bytes)")

    # node --check
    result = subprocess.run(['node', '--check', JS], capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ node --check 통과")
    else:
        print("❌ node --check 실패 — 백업에서 복원합니다.")
        print(result.stderr)
        shutil.copy2(bak, JS)
        sys.exit(1)

if __name__ == '__main__':
    main()
