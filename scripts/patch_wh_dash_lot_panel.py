# -*- coding: utf-8 -*-
"""
patch_wh_dash_lot_panel.py
==========================
sqm-warehouse-dashboard.js 의 우측 패널(wh-dash-detail)을
현재 랙의 LOT 목록 패널(ASC/DESC 정렬)로 전환.

  변경 1) wh-dash-detail → display:none 제거, 실제 패널 스타일 적용
  변경 2) _whdLotSortDir 변수 삽입 (STATE_COLORS 블록 근처)
  변경 3) _renderDetail() 함수 교체 — 셀 상세 → LOT 목록 표시
  변경 4) _whdDashSortLots() 공개 함수 삽입
"""
import pathlib, sys, shutil, datetime

TARGET = pathlib.Path(__file__).parent.parent / 'frontend' / 'js' / 'sqm-warehouse-dashboard.js'
STAMP  = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

src = TARGET.read_text(encoding='utf-8')

# ── 변경 1: wh-dash-detail 패널 활성화 ────────────────────────────────────
OLD1 = "      + '  <div id=\"wh-dash-detail\" style=\"display:none;\"></div>'"
NEW1 = (
    "      + '  <div id=\"wh-dash-detail\" style=\"width:175px;flex-shrink:0;"
    "border-left:1px solid var(--panel-border);overflow-y:auto;"
    "background:var(--bg);display:flex;flex-direction:column;\"></div>'"
)

if OLD1 not in src:
    print('ERROR: wh-dash-detail display:none 패턴 없음')
    sys.exit(1)
src = src.replace(OLD1, NEW1, 1)
print('  [1] wh-dash-detail 패널 활성화 OK')

# ── 변경 2: _whdLotSortDir 변수 삽입 ─────────────────────────────────────
OLD2 = "  /* 랙별 최대 층 */\n  var _rackLvMax = {};"
NEW2 = "  /* LOT 목록 패널 정렬 방향 */\n  var _whdLotSortDir = 'asc';\n\n  /* 랙별 최대 층 */\n  var _rackLvMax = {};"

if OLD2 not in src:
    print('ERROR: _rackLvMax 앵커 없음')
    sys.exit(1)
src = src.replace(OLD2, NEW2, 1)
print('  [2] _whdLotSortDir 삽입 OK')

# ── 변경 3: _renderDetail() 함수 교체 ─────────────────────────────────────
OLD3 = """\
  /* ── 우측 셀 상세 ── */
  function _renderDetail() {
    var box = document.getElementById('wh-dash-detail');
    if (!_state.selectedCell) {
      box.innerHTML = '<div style="color:var(--text-muted);font-size:12px;text-align:center;padding:20px;">'
        + '🖱 셀을 클릭하면<br>여기에 상세 정보 표시'
        + '</div>';
      return;
    }
    var st = _state.selectedCell;
    var rep = STATE_COLORS[st.state] || STATE_COLORS.UNKNOWN;
    var html = ''
      + '<div style="font-family:Consolas,monospace;font-size:14px;font-weight:700;color:var(--accent);'
      +     'padding:6px 8px;background:var(--bg-hover);border-radius:6px;margin-bottom:8px;">'
      + '  📍 ' + _esc(st.location)
      + '</div>'
      + '<div style="display:inline-block;padding:3px 10px;border-radius:10px;'
      +     'background:' + rep.bg + ';color:#fff;font-weight:700;font-size:11px;margin-bottom:8px;">'
      + rep.text + ' ' + _esc(st.state) + ' (' + st.active_count + '/' + st.capacity + ')'
      + '</div>'
      + '<div style="font-size:11px;color:var(--text-muted);margin-bottom:8px;">'
      + 'packing_type: <b>' + _esc(st.packing_type || '?') + '</b>'
      + '</div>';

    var tbs = st.tonbags || [];
    if (tbs.length === 0) {
      html += '<div style="padding:10px;text-align:center;color:var(--text-muted);font-size:11px;">'
        + '비어있음'
        + '</div>';
    } else {
      html += '<div style="font-size:11px;font-weight:700;color:var(--text-muted);margin:4px 0 4px;">'
        + '활성 톤백 (' + tbs.length + '개)</div>';
      tbs.forEach(function(t) {
        html += '<div style="background:var(--bg-card);border:1px solid var(--panel-border);'
          + 'border-radius:4px;padding:6px 8px;margin-bottom:4px;font-size:11px;">'
          + '<div style="font-family:Consolas,monospace;color:var(--accent);">'
          + _esc(t.lot_no) + '-' + _esc(t.sub_lt)
          + '</div>'
          + '<div style="color:var(--text-muted);">'
          + (Number(t.weight_kg) || 0).toLocaleString() + 'kg · ' + _esc(t.status)
          + '</div>'
          + '</div>';
      });
    }
    if (st.validation && !st.validation.ok) {
      html += '<div style="color:#f44336;font-size:11px;margin-top:8px;">'
        + '⚠ ' + _esc(st.validation.reason || '') + '</div>';
    }
    box.innerHTML = html;
  }"""

NEW3 = """\
  /* ── 우측 LOT 목록 패널 ── */
  function _renderDetail() {
    var box = document.getElementById('wh-dash-detail');
    if (!box) return;

    // _state.grid.cells 에서 LOT 추출
    var cells  = (_state.grid && _state.grid.cells) || [];
    var lotSet = {};
    cells.forEach(function(c) {
      if (c.lot_no && c.state !== 'EMPTY' && c.state !== 'UNKNOWN') {
        if (!lotSet[c.lot_no]) lotSet[c.lot_no] = 0;
        lotSet[c.lot_no]++;
      }
    });
    var lots = Object.keys(lotSet).sort(function(a, b) {
      return _whdLotSortDir === 'asc' ? a.localeCompare(b) : b.localeCompare(a);
    });

    // 헤더
    var html = '<div style="padding:8px 10px 4px;flex-shrink:0;">';
    html += '<div style="font-size:11px;font-weight:700;color:var(--accent);margin-bottom:6px;">'
          + 'LOT 목록 (' + lots.length + ')</div>';
    html += '<div style="display:flex;gap:4px;margin-bottom:6px;">'
          + '<button onclick="window._whdDashSortLots(\'asc\')" '
          + 'style="flex:1;background:' + (_whdLotSortDir==='asc' ? '#1565c0' : 'rgba(255,255,255,.08)') + ';'
          + 'color:#fff;border:none;border-radius:3px;padding:3px 0;font-size:10px;cursor:pointer;">↑ ASC</button>'
          + '<button onclick="window._whdDashSortLots(\'desc\')" '
          + 'style="flex:1;background:' + (_whdLotSortDir==='desc' ? '#1565c0' : 'rgba(255,255,255,.08)') + ';'
          + 'color:#fff;border:none;border-radius:3px;padding:3px 0;font-size:10px;cursor:pointer;">↓ DESC</button>'
          + '</div>';
    html += '</div>';

    // LOT 리스트 (스크롤 영역)
    html += '<div style="overflow-y:auto;flex:1;padding:0 10px 8px;">';
    if (lots.length === 0) {
      html += '<div style="color:var(--text-muted);font-size:11px;text-align:center;padding:16px 0;">—</div>';
    } else {
      lots.forEach(function(l) {
        html += '<div style="display:flex;align-items:center;gap:6px;padding:4px 0;'
              + 'border-bottom:1px solid rgba(255,255,255,.05);">'
              + '<span style="display:inline-block;width:10px;height:10px;border-radius:2px;'
              +              'flex-shrink:0;background:' + _whdLotColor(l) + ';"></span>'
              + '<span style="font-size:11px;color:var(--text);white-space:nowrap;overflow:hidden;'
              +              'text-overflow:ellipsis;" title="' + _esc(l) + '">' + _esc(l) + '</span>'
              + '<span style="margin-left:auto;font-size:10px;color:var(--text-muted);flex-shrink:0;">'
              +              lotSet[l] + '</span>'
              + '</div>';
      });
    }
    html += '</div>';
    box.innerHTML = html;
  }"""

if OLD3 not in src:
    print('ERROR: _renderDetail() 함수 패턴 없음')
    sys.exit(1)
src = src.replace(OLD3, NEW3, 1)
print('  [3] _renderDetail() → LOT 목록 렌더 교체 OK')

# ── 변경 4: _whdDashSortLots() 공개 함수 삽입 ────────────────────────────
OLD4 = """\
  /* ── 셀 선택 → 상세 로드 ── */
  window._whDashSelectCell = function(loc) {"""

NEW4 = """\
  /* ── LOT 목록 정렬 ── */
  window._whdDashSortLots = function(dir) {
    _whdLotSortDir = dir;
    _renderDetail();
  };

  /* ── 셀 선택 → 상세 로드 ── */
  window._whDashSelectCell = function(loc) {"""

if OLD4 not in src:
    print('ERROR: _whDashSelectCell 앵커 없음')
    sys.exit(1)
src = src.replace(OLD4, NEW4, 1)
print('  [4] _whdDashSortLots() 삽입 OK')

# ── 저장 ──────────────────────────────────────────────────────────────────
bak = TARGET.with_suffix('.js.bak_lotpanel_' + STAMP)
shutil.copy2(TARGET, bak)
print(f'  백업: {bak.name}')

TARGET.write_text(src, encoding='utf-8')
print(f'  저장: {TARGET.name}  ({src.count(chr(10)) + 1} 줄)')
print('DONE.')
