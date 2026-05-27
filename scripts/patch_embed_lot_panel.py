# -*- coding: utf-8 -*-
"""
patch_embed_lot_panel.py
========================
dashboard-warehouse-embed.js 의 하단 LOT 범례(가로 칩 나열)를
오른쪽 세로 LOT 목록 패널(ASC/DESC 정렬)로 교체.

  변경 1) _colorIdx 선언 직후 _lotSortDir 변수 삽입
  변경 2) _renderHeatmap 에서:
          - 외부 flex 컨테이너를 2-컬럼(왼쪽 랙 그리드 + 오른쪽 LOT 패널)으로 변경
          - 기존 가로 범례 블록 → 오른쪽 LOT 목록 패널로 교체
  변경 3) window._whEmbedSortLots() 함수 삽입 (container.innerHTML 직후)
"""
import pathlib, sys, shutil, datetime

TARGET = pathlib.Path(__file__).parent.parent / 'frontend' / 'js' / 'dashboard-warehouse-embed.js'
STAMP  = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

src = TARGET.read_text(encoding='utf-8')

# ── 변경 1: _lotSortDir 변수 삽입 ────────────────────────────────────────
OLD1 = "  var _colorIdx   = 0;"
NEW1 = "  var _colorIdx   = 0;\n  var _lotSortDir  = 'asc';   // LOT 패널 정렬 방향"

if OLD1 not in src:
    print('ERROR: _colorIdx 앵커 없음')
    sys.exit(1)
src = src.replace(OLD1, NEW1, 1)
print('  [1] _lotSortDir 삽입 OK')

# ── 변경 2a: 외부 flex 컨테이너 → 2-컬럼 레이아웃 ────────────────────────
OLD2a = """\
    // ── 5동/6동 한 줄 나란히 ──────────────────────────────────
    var html = '<div style="display:flex;gap:20px;align-items:flex-start;flex-wrap:wrap;">';"""

NEW2a = """\
    // ── 2-컬럼 레이아웃: 왼쪽(랙 그리드) + 오른쪽(LOT 목록) ──
    var sortedLots = allLots.slice().sort(function(a, b) {
      return _lotSortDir === 'asc' ? a.localeCompare(b) : b.localeCompare(a);
    });
    var html = '<div style="display:flex;gap:16px;align-items:flex-start;">';
    html += '<div style="flex:1;min-width:0;">';  // 왼쪽: 랙 그리드"""

NEW2a += """
    // ── 5동/6동 한 줄 나란히 ──────────────────────────────────"""

if OLD2a not in src:
    print('ERROR: 외부 flex 컨테이너 앵커 없음')
    sys.exit(1)
src = src.replace(OLD2a, NEW2a, 1)
print('  [2a] 외부 컨테이너 2-컬럼 전환 OK')

# ── 변경 2b: 5동/6동 루프 끝 닫는 div + 기존 범례 → LOT 패널로 교체 ──────
OLD2b = """\
    // 구분선
    html += '</div>';

    // 범례
    html += '<div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:10px;">';
    allLots.slice(0, 14).forEach(function(l) {
      html += '<span style="display:inline-flex;align-items:center;gap:4px;font-size:11px;color:#90a4ae;">'
            + '<span style="display:inline-block;width:12px;height:12px;border-radius:2px;background:' + _lotColor(l) + ';"></span>'
            + _esc(l) + '</span>';
    });
    if (allLots.length > 14) {
      html += '<span style="font-size:11px;color:#90a4ae;">외 ' + (allLots.length - 14) + '개</span>';
    }
    html += '</div>';

    container.innerHTML = html;"""

NEW2b = """\
    // 5동/6동 랙 그리드 닫기
    html += '</div>';  // 5동/6동 flex row
    html += '</div>';  // 왼쪽 컬럼 닫기

    // ── 오른쪽: LOT 목록 패널 ────────────────────────────────
    html += '<div id="wh-lot-panel" style="'
          + 'width:170px;flex-shrink:0;'
          + 'background:var(--bg-card,#1e272e);'
          + 'border:1px solid rgba(255,255,255,.1);'
          + 'border-radius:6px;padding:8px 10px;'
          + 'max-height:300px;display:flex;flex-direction:column;">';
    // 헤더 + 정렬 버튼
    html += '<div style="display:flex;align-items:center;justify-content:space-between;'
          + 'margin-bottom:6px;flex-shrink:0;">';
    html += '<span style="font-size:11px;font-weight:700;color:#4fc3f7;">LOT 목록 ('
          + allLots.length + ')</span>';
    html += '<span>'
          + '<button onclick="window._whEmbedSortLots(\'asc\')" '
          + 'style="background:' + (_lotSortDir==='asc'?'#1565c0':'rgba(255,255,255,.08)') + ';'
          + 'color:#fff;border:none;border-radius:3px;padding:2px 6px;font-size:10px;cursor:pointer;margin-right:2px;">↑ ASC</button>'
          + '<button onclick="window._whEmbedSortLots(\'desc\')" '
          + 'style="background:' + (_lotSortDir==='desc'?'#1565c0':'rgba(255,255,255,.08)') + ';'
          + 'color:#fff;border:none;border-radius:3px;padding:2px 6px;font-size:10px;cursor:pointer;">↓ DESC</button>'
          + '</span>';
    html += '</div>';
    // 스크롤 가능한 LOT 리스트
    html += '<div style="overflow-y:auto;flex:1;">';
    sortedLots.forEach(function(l) {
      html += '<div style="display:flex;align-items:center;gap:6px;padding:3px 0;'
            + 'border-bottom:1px solid rgba(255,255,255,.04);">'
            + '<span style="display:inline-block;width:10px;height:10px;border-radius:2px;'
            +              'flex-shrink:0;background:' + _lotColor(l) + ';"></span>'
            + '<span style="font-size:11px;color:#cfd8dc;white-space:nowrap;overflow:hidden;'
            +              'text-overflow:ellipsis;" title="' + _esc(l) + '">' + _esc(l) + '</span>'
            + '</div>';
    });
    html += '</div>';  // 스크롤 영역
    html += '</div>';  // LOT 패널
    html += '</div>';  // 최외곽 2-컬럼 flex

    container.innerHTML = html;"""

if OLD2b not in src:
    print('ERROR: 범례 블록 앵커 없음')
    sys.exit(1)
src = src.replace(OLD2b, NEW2b, 1)
print('  [2b] 범례 → LOT 패널 교체 OK')

# ── 변경 3: _whEmbedSortLots 함수 삽입 ───────────────────────────────────
OLD3 = """\
  // ── 2단계: 랙 확대 뷰 렌더 ──────────────────────────────────
  var _currentRack = null;"""

NEW3 = """\
  window._whEmbedSortLots = function(dir) {
    _lotSortDir = dir;
    if (_lastHeatmap) _renderHeatmap({ racks: _lastHeatmap });
  };

  // ── 2단계: 랙 확대 뷰 렌더 ──────────────────────────────────
  var _currentRack = null;"""

if OLD3 not in src:
    print('ERROR: 2단계 앵커 없음')
    sys.exit(1)
src = src.replace(OLD3, NEW3, 1)
print('  [3] _whEmbedSortLots() 삽입 OK')

# ── 저장 ──────────────────────────────────────────────────────────────────
bak = TARGET.with_suffix('.js.bak_lotpanel_' + STAMP)
shutil.copy2(TARGET, bak)
print(f'  백업: {bak.name}')

TARGET.write_text(src, encoding='utf-8')
print(f'  저장: {TARGET.name}  ({src.count(chr(10)) + 1} 줄)')
print('DONE.')
