// dashboard-warehouse-embed.js  (v8.6.9)
// =============================================================
// 대시보드 인라인 창고 히트맵
//
// 구조:
//   [1단계] 동·랙 히트맵  — /api/warehouse/rack-heatmap
//           랙 16개 미니 블록, LOT별 색상 (지배 LOT 기준)
//   [2단계] 랙 확대 뷰    — /api/warehouse/cell-grid
//           랙 클릭 시 31열×N층 전체, LOT 색상 표시
//   [3단계] 셀 툴팁       — 클릭 위치 근처에 작은 팝업
//           LOT NO / Sub-LOT NO / 상태 표시, 외부 클릭 닫기
//
// ABSOLUTE EDIT BAN 우회: sqm-inline.js 미수정
// sqm-inline.js 의 loadKpi() 이후 window.initWarehouseEmbed() 로 호출
// =============================================================

(function () {
  'use strict';
  if (window.__SQM_WH_EMBED__) return;
  window.__SQM_WH_EMBED__ = true;

  // ── 상수 ────────────────────────────────────────────────────
  var API_BASE = '';   // FastAPI 동일 origin
  var REFRESH_MS = 60000;  // 1분 자동 갱신

  // LOT 색상 팔레트 (20색 순환, 빈 셀 제외)
  var LOT_PALETTE = [
    '#1565c0','#6a1b9a','#00695c','#e65100','#558b2f',
    '#ad1457','#0277bd','#4527a0','#2e7d32','#c62828',
    '#37474f','#4e342e','#00838f','#ef6c00','#5c6bc0',
    '#7b1fa2','#0288d1','#388e3c','#d84315','#1976d2',
  ];
  var _lotColorMap = {};
  var _colorIdx    = 0;

  function _lotColor(lot) {
    if (!lot) return '#263238';
    if (!_lotColorMap[lot]) {
      _lotColorMap[lot] = LOT_PALETTE[_colorIdx % LOT_PALETTE.length];
      _colorIdx++;
    }
    return _lotColorMap[lot];
  }

  // ── DOM 헬퍼 ────────────────────────────────────────────────
  function _el(id) { return document.getElementById(id); }
  function _esc(s) {
    return String(s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;')
                          .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }

  // ── API 호출 ─────────────────────────────────────────────────
  function _get(url, cb) {
    fetch(API_BASE + url)
      .then(function(r){ return r.json(); })
      .then(function(d){ cb(null, d); })
      .catch(function(e){ cb(e, null); });
  }

  // ── 툴팁 ────────────────────────────────────────────────────
  var _tip = null;
  function _showTip(ev, cell) {
    _hideTip();
    var t = document.createElement('div');
    t.id = 'wh-embed-tip';
    var lot = _esc(cell.lot_no || '—');
    var sub = cell.sub_lt != null ? _esc(String(cell.sub_lt)) : '—';
    var state = _esc(cell.state || '—');
    var cnt   = cell.active_count != null ? cell.active_count : '—';
    var cap   = cell.capacity    != null ? cell.capacity    : '—';
    t.innerHTML =
      '<div style="font-size:11px;font-weight:700;color:var(--accent,#4fc3f7);margin-bottom:4px;">📍 ' + _esc(cell.location) + '</div>'
    + '<div style="font-size:11px;margin-bottom:2px;"><span style="color:var(--text-muted,#90a4ae);">LOT&nbsp;&nbsp;&nbsp;&nbsp;:</span> <b>' + lot + '</b></div>'
    + '<div style="font-size:11px;margin-bottom:2px;"><span style="color:var(--text-muted,#90a4ae);">Sub-LOT :</span> <b>' + sub + '</b></div>'
    + '<div style="font-size:11px;margin-bottom:2px;"><span style="color:var(--text-muted,#90a4ae);">상태&nbsp;&nbsp;&nbsp;&nbsp;:</span> ' + state + '</div>'
    + '<div style="font-size:11px;"><span style="color:var(--text-muted,#90a4ae);">점유&nbsp;&nbsp;&nbsp;&nbsp;:</span> ' + cnt + ' / ' + cap + '</div>';
    t.style.cssText = [
      'position:fixed',
      'z-index:9999',
      'background:var(--bg-card,#1e272e)',
      'border:1px solid var(--accent,#4fc3f7)',
      'border-radius:6px',
      'padding:8px 12px',
      'box-shadow:0 4px 16px rgba(0,0,0,.5)',
      'pointer-events:none',
      'min-width:170px',
    ].join(';');

    document.body.appendChild(t);
    _tip = t;

    // 위치 결정 (화면 밖으로 나가지 않게)
    var x = ev.clientX + 12;
    var y = ev.clientY + 12;
    var tw = 190, th = 120;
    if (x + tw > window.innerWidth)  x = ev.clientX - tw - 8;
    if (y + th > window.innerHeight) y = ev.clientY - th - 8;
    t.style.left = x + 'px';
    t.style.top  = y + 'px';
  }

  function _hideTip() {
    if (_tip) { _tip.remove(); _tip = null; }
  }

  // 외부 클릭 시 툴팁 닫기
  document.addEventListener('click', function(ev) {
    if (_tip && !_tip.contains(ev.target)) _hideTip();
  });

  // ── 상태 색상 (EMPTY 등 상태별) ──────────────────────────────
  function _cellBg(cell) {
    var s = cell.state || 'UNKNOWN';
    if (s === 'EMPTY' || s === 'UNKNOWN') return 'transparent';
    if (s === 'OVER')  return '#b71c1c';
    if (s === 'MIXED') return '#7b1fa2';
    return _lotColor(cell.lot_no || '');  // LOT 색상
  }

  // ── 1단계: 히트맵 렌더 ───────────────────────────────────────
  var _lastHeatmap = null;

  function _renderHeatmap(data) {
    var racks = data.racks || [];
    _lastHeatmap = racks;

    // LOT 색상 미리 배정 (순서 일관성)
    var allLots = [];
    racks.forEach(function(r) {
      (r.lots || []).forEach(function(l) {
        if (l && allLots.indexOf(l) < 0) allLots.push(l);
      });
    });
    allLots.forEach(function(l) { _lotColor(l); });

    var container = _el('wh-embed-heatmap');
    if (!container) return;

    var dongs = [5, 6];
    var html = '';
    dongs.forEach(function(dong) {
      var dongRacks = racks.filter(function(r){ return r.dong === dong; });
      html += '<div style="margin-bottom:10px;">';
      html += '<div style="font-size:11px;font-weight:700;color:var(--text-muted,#90a4ae);'
            + 'margin-bottom:4px;letter-spacing:.5px;">' + dong + '동</div>';
      html += '<div style="display:flex;gap:3px;flex-wrap:nowrap;">';
      dongRacks.forEach(function(r) {
        var pct  = r.total > 0 ? Math.round(r.occupied / r.total * 100) : 0;
        var bg   = r.dominant_lot ? _lotColor(r.dominant_lot) : 'transparent';
        var border = r.dominant_lot ? '1px solid rgba(255,255,255,.25)' : '1px solid #37474f';
        var opacity = r.occupied > 0 ? (0.4 + pct / 100 * 0.6).toFixed(2) : '0.15';
        html += '<div class="wh-rack-block"'
              + ' data-dong="' + r.dong + '" data-rack="' + r.rack + '"'
              + ' title="' + r.dong + '동 ' + r.rack_label + '랙 | LOT: ' + _esc(r.dominant_lot||'빈 랙')
              +              ' | 점유: ' + r.occupied + '/' + r.total + ' (' + pct + '%)"'
              + ' style="width:28px;height:40px;border-radius:3px;cursor:pointer;'
              +         'background:' + bg + ';border:' + border + ';opacity:' + opacity + ';'
              +         'display:flex;flex-direction:column;align-items:center;justify-content:flex-end;'
              +         'padding-bottom:3px;transition:transform .1s,box-shadow .1s;"'
              + ' onmouseover="this.style.transform=\'scale(1.15)\';this.style.boxShadow=\'0 0 8px rgba(255,255,255,.3)\'"'
              + ' onmouseout="this.style.transform=\'\';this.style.boxShadow=\'\'"'
              + ' onclick="window._whEmbedOpenRack(' + r.dong + ',' + r.rack + ')">'
              + '<span style="font-size:8px;color:rgba(255,255,255,.7);">' + r.rack_label + '</span>'
              + '</div>';
      });
      html += '</div></div>';
    });

    // 범례
    html += '<div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:6px;">';
    allLots.slice(0, 12).forEach(function(l) {
      html += '<span style="display:inline-flex;align-items:center;gap:3px;font-size:10px;color:var(--text-muted,#90a4ae);">'
            + '<span style="display:inline-block;width:10px;height:10px;border-radius:2px;background:' + _lotColor(l) + ';"></span>'
            + _esc(l) + '</span>';
    });
    if (allLots.length > 12) {
      html += '<span style="font-size:10px;color:var(--text-muted,#90a4ae);">외 ' + (allLots.length - 12) + '개</span>';
    }
    html += '</div>';

    container.innerHTML = html;
  }

  // ── 2단계: 랙 확대 뷰 렌더 ──────────────────────────────────
  var _currentRack = null;

  window._whEmbedOpenRack = function(dong, rack) {
    _currentRack = {dong: dong, rack: rack};
    var box = _el('wh-embed-rack-detail');
    if (!box) return;
    box.innerHTML = '<div style="padding:16px;color:var(--text-muted,#90a4ae);font-size:12px;">⏳ 로딩중...</div>';
    box.style.display = 'block';

    _get('/api/warehouse/cell-grid?dong=' + dong + '&rack=' + rack, function(err, res) {
      if (err || !res || !res.ok) {
        box.innerHTML = '<div style="padding:12px;color:#e57373;font-size:12px;">❌ 로드 실패</div>';
        return;
      }
      _renderRackGrid(res.data, box);
    });
  };

  function _renderRackGrid(data, box) {
    var cells   = data.cells  || [];
    var maxLv   = data.max_level || 1;
    var dong    = data.dong;
    var rack    = data.rack;

    // col별 그룹핑
    var byCol = {};
    cells.forEach(function(c) {
      if (!byCol[c.col]) byCol[c.col] = {};
      byCol[c.col][c.level] = c;
    });

    var cols = Object.keys(byCol).map(Number).sort(function(a,b){return a-b;});

    var html = '<div style="display:flex;align-items:center;justify-content:space-between;'
             + 'margin-bottom:8px;padding:0 2px;">'
             + '<span style="font-size:12px;font-weight:700;color:var(--accent,#4fc3f7);">'
             + '📦 ' + dong + '동 ' + String(rack).padStart(2,'0') + '번 랙</span>'
             + '<button onclick="window._whEmbedCloseRack()" '
             + 'style="background:none;border:none;cursor:pointer;color:var(--text-muted,#90a4ae);font-size:16px;padding:0 4px;">×</button>'
             + '</div>';

    // 그리드 (행=층, 열=열) — 층은 위에서 아래로 최상층 먼저
    html += '<div style="overflow-x:auto;">';
    html += '<table style="border-collapse:collapse;font-size:9px;">';

    // 헤더 (열 번호)
    html += '<tr><th style="width:24px;color:var(--text-muted,#90a4ae);padding:1px 3px;">층↓열→</th>';
    cols.forEach(function(col) {
      html += '<th style="width:18px;text-align:center;color:var(--text-muted,#90a4ae);padding:1px 1px;">'
            + String(col).padStart(2,'0') + '</th>';
    });
    html += '</tr>';

    // 층 행 (높은 층 위)
    for (var lv = maxLv; lv >= 1; lv--) {
      html += '<tr>';
      html += '<td style="text-align:right;color:var(--text-muted,#90a4ae);padding:1px 4px 1px 2px;font-weight:700;">L' + String(lv).padStart(2,'0') + '</td>';
      cols.forEach(function(col) {
        var cell = (byCol[col] || {})[lv];
        if (!cell) {
          html += '<td style="width:18px;height:18px;"></td>';
          return;
        }
        var isEmpty = (cell.state === 'EMPTY' || cell.state === 'UNKNOWN');
        var bg      = _cellBg(cell);
        var border  = isEmpty ? 'none' : '1px solid rgba(255,255,255,.2)';
        var cursor  = isEmpty ? 'default' : 'pointer';
        var radius  = isEmpty ? '0' : '2px';
        // cell 데이터를 onclick에 안전하게 전달 (빈 셀은 click 무시)
        var cellJson = JSON.stringify({
          location:     cell.location,
          lot_no:       cell.lot_no || '',
          sub_lt:       cell.sub_lt,
          state:        cell.state,
          active_count: cell.active_count,
          capacity:     cell.capacity,
        }).replace(/'/g, '&#39;');
        html += '<td onclick="window._whEmbedCellClick(event, \'' + cellJson.replace(/"/g,'&quot;') + '\')"'
              + ' style="width:18px;height:18px;background:' + bg + ';border:' + border + ';'
              +         'cursor:' + cursor + ';border-radius:' + radius + ';"></td>';
      });
      html += '</tr>';
    }
    html += '</table></div>';
    box.innerHTML = html;
  }

  window._whEmbedCloseRack = function() {
    var box = _el('wh-embed-rack-detail');
    if (box) { box.style.display = 'none'; box.innerHTML = ''; }
    _currentRack = null;
    _hideTip();
  };

  window._whEmbedCellClick = function(ev, cellJsonStr) {
    ev.stopPropagation();
    try {
      var cell = JSON.parse(cellJsonStr.replace(/&quot;/g, '"').replace(/&#39;/g, "'"));
      if (cell.state === 'EMPTY') { _hideTip(); return; }
      _showTip(ev, cell);
    } catch(e) { /* ignore */ }
  };

  // ── 초기화 + 갱신 ────────────────────────────────────────────
  function _load() {
    _get('/api/warehouse/rack-heatmap', function(err, res) {
      if (err || !res || !res.ok) return;
      _renderHeatmap(res.data);
    });
  }

  var _timer = null;
  function _startAutoRefresh() {
    if (_timer) clearInterval(_timer);
    _timer = setInterval(_load, REFRESH_MS);
  }

  // 공개 초기화 함수
  window.initWarehouseEmbed = function() {
    _load();
    _startAutoRefresh();
  };

  // 수동 갱신 버튼용
  window._whEmbedRefresh = function() {
    _load();
    if (_currentRack) {
      window._whEmbedOpenRack(_currentRack.dong, _currentRack.rack);
    }
  };

})();
