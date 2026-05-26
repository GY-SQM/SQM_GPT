# -*- coding: utf-8 -*-
"""
patch_wh_grid_clean.py
======================
sqm-warehouse-dashboard.js 셀 표시 단순화:
  - 빈 셀(EMPTY / 데이터 없음) → 완전 공란 (배경·테두리 없음)
  - 점유 셀(OCCUPIED/HALF/OVER/MIXED) → 색상만, 숫자 제거
"""
import pathlib, sys, shutil, datetime, re

TARGET = pathlib.Path(__file__).parent.parent / 'frontend' / 'js' / 'sqm-warehouse-dashboard.js'
STAMP  = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

src = TARGET.read_text(encoding='utf-8')

# ── 1) 데이터 없는 빈 셀: dashed 테두리 → 완전 공란 ──────────────
OLD1 = "border:1px dashed #444;"
if OLD1 not in src:
    print('WARN: dashed 패턴 없음 (이미 적용됐을 수 있음)')
else:
    src = src.replace(OLD1, '', 1)
    print('  [1] 빈 셀 dashed 테두리 제거 OK')

# ── 2) EMPTY 상태 셀 스타일 — 배경 제거 ─────────────────────────
# STATE_COLORS.EMPTY bg 를 투명으로 변경
OLD2 = "EMPTY:    { bg: '#37474f', border: '#546e7a', text: '⬜' },"
NEW2 = "EMPTY:    { bg: 'transparent', border: 'transparent', text: '' },"
if OLD2 not in src:
    print('WARN: EMPTY 색상 상수 패턴 없음')
else:
    src = src.replace(OLD2, NEW2, 1)
    print('  [2] EMPTY 배경·테두리 투명 처리 OK')

# ── 3) 셀 숫자(active_count) 제거 ───────────────────────────────
# + (c.state === 'EMPTY' ? '' : c.active_count)  →  + ''
OLD3 = "+ (c.state === 'EMPTY' ? '' : c.active_count)"
NEW3 = "+ ''"
if OLD3 not in src:
    print('WARN: active_count 패턴 없음')
else:
    src = src.replace(OLD3, NEW3, 1)
    print('  [3] 숫자(active_count) 표시 제거 OK')

# ── 4) EMPTY 셀 cursor 를 default 로 ────────────────────────────
# 빈 셀은 클릭 불가 느낌 주기 위해: EMPTY 상태일 때 cursor:default
# 기존: cursor:pointer (모든 셀 공통)
# → EMPTY bg/border 가 transparent 이므로 클릭해도 detail 패널만 뜸
# → cursor 는 JS 조건으로 분리 (간단 치환)
OLD4 = "';color:#fff;text-align:center;cursor:pointer;font-size:9px;'"
NEW4 = "';text-align:center;cursor:' + (c.state === 'EMPTY' ? 'default' : 'pointer') + ';font-size:9px;'"
if OLD4 not in src:
    print('WARN: cursor 패턴 없음')
else:
    src = src.replace(OLD4, NEW4, 1)
    print('  [4] EMPTY 셀 cursor:default 처리 OK')

# ── 저장 ────────────────────────────────────────────────────────
bak = TARGET.with_suffix('.js.bak_gridclean_' + STAMP)
shutil.copy2(TARGET, bak)
print(f'  백업: {bak.name}')

TARGET.write_text(src, encoding='utf-8')
print(f'  저장: {TARGET.name}  ({src.count(chr(10))+1} 줄)')
print('DONE.')
