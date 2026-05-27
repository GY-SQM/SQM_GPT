# -*- coding: utf-8 -*-
"""
patch_wh_dashboard_ui.py
========================
sqm-warehouse-dashboard.js 두 가지 UI 개선:

  변경 1) 오른쪽 상세 패널(wh-dash-detail, 300px) 완전 제거
          → 클릭 시 툴팁 방식(dashboard-warehouse-embed.js)으로 대체

  변경 2) 셀 크기 확대: 26×22px → 38×30px
          오른쪽 패널 제거로 생긴 공간 활용
"""
import pathlib, sys, shutil, datetime

TARGET = pathlib.Path(__file__).parent.parent / 'frontend' / 'js' / 'sqm-warehouse-dashboard.js'
STAMP  = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

src = TARGET.read_text(encoding='utf-8')

# ── 변경 1: 오른쪽 상세 패널 제거 ─────────────────────────────────────
OLD1 = (
    "      + '  <div id=\"wh-dash-detail\" style=\"width:300px;border-left:1px solid var(--panel-border);'\n"
    "      +       'overflow-y:auto;flex-shrink:0;background:var(--bg);padding:10px;\"></div>'"
)
NEW1 = (
    "      + '  <div id=\"wh-dash-detail\" style=\"display:none;\"></div>'"
)

if OLD1 not in src:
    print('ERROR: wh-dash-detail 패널 HTML 패턴 없음')
    sys.exit(1)
src = src.replace(OLD1, NEW1, 1)
print('  [1] wh-dash-detail 패널 display:none 처리 OK')

# ── 변경 2: 셀 크기 26×22 → 38×30 (헤더 th 포함) ──────────────────────
# 헤더 th width
OLD2a = "style=\"padding:2px;color:var(--text-muted);font-weight:400;width:26px;text-align:center;\""
NEW2a = "style=\"padding:2px;color:var(--text-muted);font-weight:400;width:38px;text-align:center;\""
if OLD2a not in src:
    print('WARN: 헤더 th width:26px 패턴 없음 (이미 적용됐을 수 있음)')
else:
    src = src.replace(OLD2a, NEW2a, 1)
    print('  [2a] 헤더 th width 26→38px OK')

# 빈 셀 td
OLD2b = "'<td style=\"width:26px;height:22px;\"></td>'"
NEW2b = "'<td style=\"width:38px;height:30px;\"></td>'"
if OLD2b not in src:
    print('WARN: 빈 셀 td 26×22 패턴 없음')
else:
    src = src.replace(OLD2b, NEW2b, 1)
    print('  [2b] 빈 셀 td 26×22 → 38×30px OK')

# 점유 셀 td (inline style 시작 부분)
OLD2c = "'style=\"width:26px;height:22px;border:1px solid ' + st.border + ';'"
NEW2c = "'style=\"width:38px;height:30px;border:1px solid ' + st.border + ';'"
if OLD2c not in src:
    print('WARN: 점유 셀 td width:26px 패턴 없음')
else:
    src = src.replace(OLD2c, NEW2c, 1)
    print('  [2c] 점유 셀 td 26×22 → 38×30px OK')

# ── 저장 ──────────────────────────────────────────────────────────────
bak = TARGET.with_suffix('.js.bak_dashui_' + STAMP)
shutil.copy2(TARGET, bak)
print(f'  백업: {bak.name}')

TARGET.write_text(src, encoding='utf-8')
print(f'  저장: {TARGET.name}  ({src.count(chr(10)) + 1} 줄)')
print('DONE.')
