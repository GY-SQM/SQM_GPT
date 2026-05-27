# -*- coding: utf-8 -*-
"""
patch_wh_dash_lot_color.py
==========================
sqm-warehouse-dashboard.js 에 LOT 색상 로직 적용.

  변경 1) STATE_COLORS 정의 직후에 LOT 팔레트 + _whdLotColor() 추가
  변경 2) 셀 렌더링 배경색을 lot_no 기준 LOT 색상으로 교체
          (EMPTY/UNKNOWN 제외, lot_no 없으면 STATE_COLORS 폴백)

결과: 창고 셀 점유 대시보드 팝업에서도 미니맵과 동일한 LOT별 색상 표시
"""
import pathlib, sys, shutil, datetime

TARGET = pathlib.Path(__file__).parent.parent / 'frontend' / 'js' / 'sqm-warehouse-dashboard.js'
STAMP  = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

src = TARGET.read_text(encoding='utf-8')

# ── 변경 1: LOT 팔레트 + _whdLotColor() — STATE_COLORS 블록 직후 삽입 ──
OLD1 = """\
  /* 랙별 최대 층 */
  var _rackLvMax = {};"""

NEW1 = """\
  /* LOT 색상 팔레트 — 미니맵과 동일 20색 순환 */
  var _WHD_LOT_PALETTE = [
    '#1565c0','#6a1b9a','#00695c','#e65100','#558b2f',
    '#ad1457','#0277bd','#4527a0','#2e7d32','#c62828',
    '#37474f','#4e342e','#00838f','#ef6c00','#5c6bc0',
    '#7b1fa2','#0288d1','#388e3c','#d84315','#1976d2',
  ];
  var _whdLotMap = {};
  var _whdLotIdx = 0;
  function _whdLotColor(lot) {
    if (!lot) return '#263238';
    if (!_whdLotMap[lot]) {
      _whdLotMap[lot] = _WHD_LOT_PALETTE[_whdLotIdx % _WHD_LOT_PALETTE.length];
      _whdLotIdx++;
    }
    return _whdLotMap[lot];
  }

  /* 랙별 최대 층 */
  var _rackLvMax = {};"""

if OLD1 not in src:
    print('ERROR: _rackLvMax 앵커 패턴 없음')
    sys.exit(1)
src = src.replace(OLD1, NEW1, 1)
print('  [1] LOT 팔레트 + _whdLotColor() 삽입 OK')

# ── 변경 2: 셀 배경색을 LOT 색상으로 교체 ──────────────────────────────
OLD2 = """\
        var st = STATE_COLORS[c.state] || STATE_COLORS.UNKNOWN;
        var isSel = (_state.selectedCell && _state.selectedCell.location === c.location);
        html += '<td onclick="window._whDashSelectCell(\\'' + _esc(c.location) + '\\')" '
          + 'title="' + _esc(c.location) + ' / ' + c.state + ' (' + c.active_count + '/' + c.capacity + ')" '
          + 'style="width:38px;height:30px;border:1px solid ' + st.border + ';'
          + 'background:' + st.bg + ';text-align:center;cursor:' + (c.state === 'EMPTY' ? 'default' : 'pointer') + ';font-size:9px;'
          + (isSel ? 'outline:3px solid #4fc3f7;outline-offset:-1px;' : '')
          + '">'
          + ''
          + '</td>';"""

NEW2 = """\
        var st = STATE_COLORS[c.state] || STATE_COLORS.UNKNOWN;
        var isSel = (_state.selectedCell && _state.selectedCell.location === c.location);
        // LOT 색상 우선 적용 (EMPTY/UNKNOWN 제외)
        var isEmpty = (c.state === 'EMPTY' || c.state === 'UNKNOWN');
        var cellBg  = (!isEmpty && c.lot_no) ? _whdLotColor(c.lot_no) : st.bg;
        var cellBorder = (!isEmpty && c.lot_no) ? '1px solid rgba(255,255,255,.2)' : '1px solid ' + st.border;
        html += '<td onclick="window._whDashSelectCell(\\'' + _esc(c.location) + '\\')" '
          + 'title="' + _esc(c.location) + ' / ' + _esc(c.lot_no || c.state) + ' (' + c.active_count + '/' + c.capacity + ')" '
          + 'style="width:38px;height:30px;border:' + cellBorder + ';'
          + 'background:' + cellBg + ';text-align:center;cursor:' + (isEmpty ? 'default' : 'pointer') + ';font-size:9px;'
          + (isSel ? 'outline:3px solid #4fc3f7;outline-offset:-1px;' : '')
          + '">'
          + ''
          + '</td>';"""

if OLD2 not in src:
    print('ERROR: 셀 렌더링 패턴 없음')
    sys.exit(1)
src = src.replace(OLD2, NEW2, 1)
print('  [2] 셀 배경색 LOT 색상 교체 OK')

# ── 저장 ──────────────────────────────────────────────────────────────
bak = TARGET.with_suffix('.js.bak_lotcolor_' + STAMP)
shutil.copy2(TARGET, bak)
print(f'  백업: {bak.name}')

TARGET.write_text(src, encoding='utf-8')
print(f'  저장: {TARGET.name}  ({src.count(chr(10)) + 1} 줄)')
print('DONE.')
