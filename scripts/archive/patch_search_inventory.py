#!/usr/bin/env python3
"""
patch_search_inventory.py
목적: Pending / Available 탭에 검색바(텍스트+날짜범위+초기화+카운트) 추가
     - Pending: 텍스트(LOT·BL·컨테이너·선박) + 입항일 범위
     - Available: 텍스트(LOT·BL·컨테이너·Product) + 입고일 범위
     DOM 필터 방식 (재로드 없이 즉시 필터링)
적용: 2026-05-25  파일: sqm-inventory.js (CRLF)
"""
import os, sys

TARGET = os.path.normpath(os.path.join(os.path.dirname(__file__),
    '..', 'frontend', 'js', 'sqm-inventory.js'))

def crlf(s):
    return s.replace('\n', '\r\n')

with open(TARGET, 'rb') as f:
    data = f.read()
orig = data
errors = 0

def patch(label, old_s, new_s):
    global data, errors
    old_b = crlf(old_s).encode('utf-8')
    new_b = crlf(new_s).encode('utf-8')
    if old_b not in data:
        print(f'[MISS {label}]')
        print('  앞 80:', repr(old_b[:80]))
        errors += 1
    else:
        data = data.replace(old_b, new_b, 1)
        print(f'[OK   {label}]')

# ─────────────────────────────────────────────────────
#  P1: _renderPendingGroupRows 바깥 div에 data-pend-grp 추가
# ─────────────────────────────────────────────────────
patch('P1-pend-grp',
    "      html += '<div style=\"margin-bottom:12px;border:1px solid var(--border,#334155);border-radius:8px;overflow:hidden\">'\n",
    "      html += '<div data-pend-grp=\"1\" style=\"margin-bottom:12px;border:1px solid var(--border,#334155);border-radius:8px;overflow:hidden\">'\n"
)

# ─────────────────────────────────────────────────────
#  P2: _renderPendingLotRows <tbody>에 id="pend-lot-tbody"
# ─────────────────────────────────────────────────────
patch('P2-pend-tbody',
    "      + '<th>WH</th>'\n"
    "      + '</tr></thead><tbody>';\n"
    "    html += rows.map(function(r, i) {\n"
    "      var lotSafe = escapeHtml(r.lot_no || '');\n",
    "      + '<th>WH</th>'\n"
    "      + '</tr></thead><tbody id=\"pend-lot-tbody\">';\n"
    "    html += rows.map(function(r, i) {\n"
    "      var lotSafe = escapeHtml(r.lot_no || '');\n"
)

# ─────────────────────────────────────────────────────
#  P3: Pending 검색바 — 툴바 직후, 빈상태 체크 앞에 삽입
# ─────────────────────────────────────────────────────
PEND_SEARCH_BAR = (
    "      html += '<div style=\"display:flex;align-items:center;gap:6px;padding:6px 0 8px;flex-wrap:wrap;border-bottom:1px solid var(--border,#334155);margin-bottom:8px\">'\n"
    "        + '<span style=\"font-size:11px;color:var(--text-muted);flex-shrink:0\">🔍 검색</span>'\n"
    "        + '<input id=\"pend-q\" type=\"text\" placeholder=\"LOT · BL · 컨테이너 · 선박\" style=\"font-size:12px;padding:3px 8px;background:var(--surface,#1e293b);border:1px solid var(--border,#334155);border-radius:4px;color:var(--text-primary);width:180px\" oninput=\"window._pendingFilter()\">'\n"
    "        + '<span style=\"font-size:11px;color:var(--text-muted);flex-shrink:0\">입항일</span>'\n"
    "        + '<input id=\"pend-df\" type=\"date\" style=\"font-size:12px;padding:2px 6px;background:var(--surface,#1e293b);border:1px solid var(--border,#334155);border-radius:4px;color:var(--text-primary)\" onchange=\"window._pendingFilter()\">'\n"
    "        + '<span style=\"font-size:11px;color:var(--text-muted)\">~</span>'\n"
    "        + '<input id=\"pend-dt\" type=\"date\" style=\"font-size:12px;padding:2px 6px;background:var(--surface,#1e293b);border:1px solid var(--border,#334155);border-radius:4px;color:var(--text-primary)\" onchange=\"window._pendingFilter()\">'\n"
    "        + '<button class=\"btn\" style=\"font-size:12px;padding:3px 10px;border-radius:4px\" onclick=\"window._pendingFilterReset()\">✕ 초기화</button>'\n"
    "        + '<span id=\"pend-count\" style=\"font-size:11px;color:var(--text-muted)\"></span>'\n"
    "        + '</div>';\n"
)

patch('P3-pend-searchbar',
    "        + '<button class=\"btn\" style=\"font-size:12px;padding:3px 10px;border-radius:4px\" onclick=\"window.loadPendingPage()\">🔄 새로고침</button>'\n"
    "        + '</div>';\n"
    "      if (!rows.length) {\n"
    "        html += '<div class=\"empty\" style=\"padding:60px;text-align:center;color:var(--text-muted);font-size:3em;font-weight:600;line-height:1.4\">⏳ 입고 대기 중인 화물 없음</div></section>';\n",
    "        + '<button class=\"btn\" style=\"font-size:12px;padding:3px 10px;border-radius:4px\" onclick=\"window.loadPendingPage()\">🔄 새로고침</button>'\n"
    "        + '</div>';\n"
    + PEND_SEARCH_BAR +
    "      if (!rows.length) {\n"
    "        html += '<div class=\"empty\" style=\"padding:60px;text-align:center;color:var(--text-muted);font-size:3em;font-weight:600;line-height:1.4\">⏳ 입고 대기 중인 화물 없음</div></section>';\n"
)

# ─────────────────────────────────────────────────────
#  P4: Available <tbody>에 id="avail-tbody"
# ─────────────────────────────────────────────────────
patch('P4-avail-tbody',
    "        + '<th>Inbound(MT)</th><th>Location</th><th></th>'\n"
    "        + '</tr></thead><tbody>';\n"
    "      html += rows.map(function(r, i) {\n",
    "        + '<th>Inbound(MT)</th><th>Location</th><th></th>'\n"
    "        + '</tr></thead><tbody id=\"avail-tbody\">';\n"
    "      html += rows.map(function(r, i) {\n"
)

# ─────────────────────────────────────────────────────
#  P5: Available 검색바 — 툴바 직후, 테이블 div 앞에 삽입 (데이터 있는 경우)
# ─────────────────────────────────────────────────────
AVAIL_SEARCH_BAR = (
    "        + '<div style=\"display:flex;align-items:center;gap:6px;padding:6px 0 8px;flex-wrap:wrap;border-bottom:1px solid var(--border,#334155);margin-bottom:8px\">'\n"
    "        + '<span style=\"font-size:11px;color:var(--text-muted);flex-shrink:0\">🔍 검색</span>'\n"
    "        + '<input id=\"avail-q\" type=\"text\" placeholder=\"LOT · BL · 컨테이너 · Product\" style=\"font-size:12px;padding:3px 8px;background:var(--surface,#1e293b);border:1px solid var(--border,#334155);border-radius:4px;color:var(--text-primary);width:180px\" oninput=\"window._availFilter()\">'\n"
    "        + '<span style=\"font-size:11px;color:var(--text-muted);flex-shrink:0\">입고일</span>'\n"
    "        + '<input id=\"avail-df\" type=\"date\" style=\"font-size:12px;padding:2px 6px;background:var(--surface,#1e293b);border:1px solid var(--border,#334155);border-radius:4px;color:var(--text-primary)\" onchange=\"window._availFilter()\">'\n"
    "        + '<span style=\"font-size:11px;color:var(--text-muted)\">~</span>'\n"
    "        + '<input id=\"avail-dt\" type=\"date\" style=\"font-size:12px;padding:2px 6px;background:var(--surface,#1e293b);border:1px solid var(--border,#334155);border-radius:4px;color:var(--text-primary)\" onchange=\"window._availFilter()\">'\n"
    "        + '<button class=\"btn\" style=\"font-size:12px;padding:3px 10px;border-radius:4px\" onclick=\"window._availFilterReset()\">✕ 초기화</button>'\n"
    "        + '<span id=\"avail-count\" style=\"font-size:11px;color:var(--text-muted)\"></span>'\n"
    "        + '</div>'\n"
)

patch('P5-avail-searchbar',
    "        + '<button class=\"btn\" style=\"font-size:12px;padding:3px 10px;border-radius:4px\" onclick=\"window.loadAvailablePage()\">🔄 새로고침</button>'\n"
    "        + '</div>'\n"
    "        + '<div style=\"overflow-x:auto\"><table class=\"data-table\"><thead><tr>'\n",
    "        + '<button class=\"btn\" style=\"font-size:12px;padding:3px 10px;border-radius:4px\" onclick=\"window.loadAvailablePage()\">🔄 새로고침</button>'\n"
    "        + '</div>'\n"
    + AVAIL_SEARCH_BAR +
    "        + '<div style=\"overflow-x:auto\"><table class=\"data-table\"><thead><tr>'\n"
)

# ─────────────────────────────────────────────────────
#  P6: Pending 필터 함수 — window.loadPendingPage 뒤에 삽입
# ─────────────────────────────────────────────────────
PEND_FILTER_FN = (
    "\n"
    "  window._pendingFilter = function() {\n"
    "    var q = ((document.getElementById('pend-q')||{}).value||'').toLowerCase().trim();\n"
    "    var df = (document.getElementById('pend-df')||{}).value||'';\n"
    "    var dt = (document.getElementById('pend-dt')||{}).value||'';\n"
    "    var countEl = document.getElementById('pend-count');\n"
    "    var mode = window._pendingViewMode || 'lot';\n"
    "    var vis = 0, total = 0;\n"
    "    if (mode === 'lot') {\n"
    "      var tbody = document.getElementById('pend-lot-tbody');\n"
    "      if (!tbody) return;\n"
    "      var trs = tbody.querySelectorAll('tr');\n"
    "      trs.forEach(function(row) {\n"
    "        var txt = row.textContent.toLowerCase();\n"
    "        var textOk = !q || txt.indexOf(q) !== -1;\n"
    "        var cells = row.cells;\n"
    "        var dateStr = cells && cells.length > 13 ? cells[13].textContent.trim() : '';\n"
    "        var dMatch = dateStr.match(/(\\d{4}-\\d{2}-\\d{2})/);\n"
    "        var d = dMatch ? dMatch[1] : '';\n"
    "        var dateOk = (!df || !d || d >= df) && (!dt || !d || d <= dt);\n"
    "        var show = textOk && dateOk;\n"
    "        row.style.display = show ? '' : 'none';\n"
    "        total++; if (show) vis++;\n"
    "      });\n"
    "    } else {\n"
    "      var groups = document.querySelectorAll('[data-pend-grp]');\n"
    "      groups.forEach(function(g) {\n"
    "        var txt = g.textContent.toLowerCase();\n"
    "        var textOk = !q || txt.indexOf(q) !== -1;\n"
    "        var dateOk = true;\n"
    "        if (df || dt) {\n"
    "          var dates = txt.match(/\\d{4}-\\d{2}-\\d{2}/g) || [];\n"
    "          if (dates.length) { dateOk = dates.some(function(d){ return (!df||d>=df)&&(!dt||d<=dt); }); }\n"
    "        }\n"
    "        var show = textOk && dateOk;\n"
    "        g.style.display = show ? '' : 'none';\n"
    "        total++; if (show) vis++;\n"
    "      });\n"
    "    }\n"
    "    if (countEl) countEl.textContent = vis + '/' + total + '건';\n"
    "  };\n"
    "\n"
    "  window._pendingFilterReset = function() {\n"
    "    var el;\n"
    "    el = document.getElementById('pend-q');  if (el) el.value = '';\n"
    "    el = document.getElementById('pend-df'); if (el) el.value = '';\n"
    "    el = document.getElementById('pend-dt'); if (el) el.value = '';\n"
    "    el = document.getElementById('pend-count'); if (el) el.textContent = '';\n"
    "    window._pendingFilter();\n"
    "  };\n"
)

patch('P6-pend-filterfn',
    "  window.loadPendingPage = loadPendingPage;\n"
    "\n"
    "  window._togglePendingGroup = function(id) {\n",
    "  window.loadPendingPage = loadPendingPage;\n"
    + PEND_FILTER_FN +
    "  window._togglePendingGroup = function(id) {\n"
)

# ─────────────────────────────────────────────────────
#  P7: Available 필터 함수 — window.loadAvailablePage 뒤에 삽입
# ─────────────────────────────────────────────────────
AVAIL_FILTER_FN = (
    "\n"
    "  window._availFilter = function() {\n"
    "    var q = ((document.getElementById('avail-q')||{}).value||'').toLowerCase().trim();\n"
    "    var df = (document.getElementById('avail-df')||{}).value||'';\n"
    "    var dt = (document.getElementById('avail-dt')||{}).value||'';\n"
    "    var tbody = document.getElementById('avail-tbody');\n"
    "    var countEl = document.getElementById('avail-count');\n"
    "    if (!tbody) return;\n"
    "    var trs = tbody.querySelectorAll('tr');\n"
    "    var vis = 0, total = 0;\n"
    "    trs.forEach(function(row) {\n"
    "      var txt = row.textContent.toLowerCase();\n"
    "      var textOk = !q || txt.indexOf(q) !== -1;\n"
    "      var cells = row.cells;\n"
    "      var dateStr = cells && cells.length > 14 ? cells[14].textContent.trim() : '';\n"
    "      var dMatch = dateStr.match(/(\\d{4}-\\d{2}-\\d{2})/);\n"
    "      var d = dMatch ? dMatch[1] : '';\n"
    "      var dateOk = (!df || !d || d >= df) && (!dt || !d || d <= dt);\n"
    "      var show = textOk && dateOk;\n"
    "      row.style.display = show ? '' : 'none';\n"
    "      total++; if (show) vis++;\n"
    "    });\n"
    "    if (countEl) countEl.textContent = vis + '/' + total + '건';\n"
    "  };\n"
    "\n"
    "  window._availFilterReset = function() {\n"
    "    var el;\n"
    "    el = document.getElementById('avail-q');  if (el) el.value = '';\n"
    "    el = document.getElementById('avail-df'); if (el) el.value = '';\n"
    "    el = document.getElementById('avail-dt'); if (el) el.value = '';\n"
    "    el = document.getElementById('avail-count'); if (el) el.textContent = '';\n"
    "    window._availFilter();\n"
    "  };\n"
)

patch('P7-avail-filterfn',
    "    window.loadAvailablePage = loadAvailablePage;\n"
    "\n"
    "  window.availToggleAll = function(masterCb) {\n",
    "    window.loadAvailablePage = loadAvailablePage;\n"
    + AVAIL_FILTER_FN +
    "  window.availToggleAll = function(masterCb) {\n"
)

# ─────────────────────────────────────────────────────
#  저장
# ─────────────────────────────────────────────────────
if errors:
    print(f'\n[중단] {errors}건 MISS — 저장 안 함')
    sys.exit(1)

with open(TARGET, 'wb') as f:
    f.write(data)
print(f'\n[저장] {TARGET}')
