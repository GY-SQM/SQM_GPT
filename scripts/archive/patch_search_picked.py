#!/usr/bin/env python3
"""
patch_search_picked.py
목적: Picked 탭에 검색바(LOT·BL·고객사 텍스트 + 날짜 범위) 추가
     - LOT 모드: #picked-tbody tr 필터링
     - 고객사/날짜 그룹 모드: [data-picked-grp] div 필터링
적용: 2026-05-25  파일: sqm-picked.js (LF)
"""
import os, sys

TARGET = os.path.normpath(os.path.join(os.path.dirname(__file__),
    '..', 'frontend', 'js', 'sqm-picked.js'))

with open(TARGET, 'rb') as f:
    data = f.read()
orig = data
errors = 0

def patch(label, old_s, new_s):
    global data, errors
    # sqm-picked.js 는 LF 파일 — 변환 없이 그대로
    old_b = old_s.encode('utf-8')
    new_b = new_s.encode('utf-8')
    if old_b not in data:
        print(f'[MISS {label}]')
        print('  앞 80:', repr(old_b[:80]))
        errors += 1
    else:
        data = data.replace(old_b, new_b, 1)
        print(f'[OK   {label}]')

# ─────────────────────────────────────────────────────
#  P1: _renderPickedGroup 바깥 div에 data-picked-grp 추가
# ─────────────────────────────────────────────────────
patch('P1-picked-grp',
    "      html += '<div style=\"margin-bottom:12px;border:1px solid var(--border,#334155);border-radius:8px;overflow:hidden\">'\n",
    "      html += '<div data-picked-grp=\"1\" style=\"margin-bottom:12px;border:1px solid var(--border,#334155);border-radius:8px;overflow:hidden\">'\n"
)

# ─────────────────────────────────────────────────────
#  P2: Picked 툴바 HTML 뒤에 검색바 삽입
#      ('<div id="picked-loading"...' 바로 앞)
# ─────────────────────────────────────────────────────
PICKED_SEARCH_BAR = (
    "'<div style=\"display:flex;align-items:center;gap:6px;padding:6px 0 8px;flex-wrap:wrap;border-bottom:1px solid var(--border,#334155);margin-bottom:8px\">',\n"
    "'  <span style=\"font-size:11px;color:var(--text-muted);flex-shrink:0\">🔍 검색</span>',\n"
    "'  <input id=\"picked-q\" type=\"text\" placeholder=\"LOT · BL · 고객사\" style=\"font-size:12px;padding:3px 8px;background:var(--surface,#1e293b);border:1px solid var(--border,#334155);border-radius:4px;color:var(--text-primary);width:180px\" oninput=\"window._pickedFilter()\">',\n"
    "'  <span style=\"font-size:11px;color:var(--text-muted);flex-shrink:0\">날짜</span>',\n"
    "'  <input id=\"picked-df\" type=\"date\" style=\"font-size:12px;padding:2px 6px;background:var(--surface,#1e293b);border:1px solid var(--border,#334155);border-radius:4px;color:var(--text-primary)\" onchange=\"window._pickedFilter()\">',\n"
    "'  <span style=\"font-size:11px;color:var(--text-muted)\">~</span>',\n"
    "'  <input id=\"picked-dt\" type=\"date\" style=\"font-size:12px;padding:2px 6px;background:var(--surface,#1e293b);border:1px solid var(--border,#334155);border-radius:4px;color:var(--text-primary)\" onchange=\"window._pickedFilter()\">',\n"
    "'  <button class=\"btn\" style=\"font-size:12px;padding:3px 10px;border-radius:4px\" onclick=\"window._pickedFilterReset()\">✕ 초기화</button>',\n"
    "'  <span id=\"picked-count\" style=\"font-size:11px;color:var(--text-muted)\"></span>',\n"
    "'</div>',\n"
)

patch('P2-picked-searchbar',
    "'</div>',\n"
    "'<div id=\"picked-loading\" style=\"padding:40px;text-align:center;color:var(--text-muted)\">⏳ 데이터 로딩 중...</div>',\n",
    "'</div>',\n"
    + PICKED_SEARCH_BAR
    + "'<div id=\"picked-loading\" style=\"padding:40px;text-align:center;color:var(--text-muted)\">⏳ 데이터 로딩 중...</div>',\n"
)

# ─────────────────────────────────────────────────────
#  P3: 필터 함수 — window.loadPickedPage 뒤에 삽입
# ─────────────────────────────────────────────────────
PICKED_FILTER_FN = (
    "\n"
    "  window._pickedFilter = function() {\n"
    "    var q = ((document.getElementById('picked-q')||{}).value||'').toLowerCase().trim();\n"
    "    var df = (document.getElementById('picked-df')||{}).value||'';\n"
    "    var dt = (document.getElementById('picked-dt')||{}).value||'';\n"
    "    var countEl = document.getElementById('picked-count');\n"
    "    var mode = window._pickedViewMode || 'lot';\n"
    "    var vis = 0, total = 0;\n"
    "    if (mode === 'lot') {\n"
    "      var tbody = document.getElementById('picked-tbody');\n"
    "      if (!tbody) return;\n"
    "      var trs = tbody.querySelectorAll('tr');\n"
    "      trs.forEach(function(row) {\n"
    "        var txt = row.textContent.toLowerCase();\n"
    "        var textOk = !q || txt.indexOf(q) !== -1;\n"
    "        var cells = row.cells;\n"
    "        var dateStr = cells && cells.length > 17 ? cells[17].textContent.trim() : '';\n"
    "        var dMatch = dateStr.match(/(\\d{4}-\\d{2}-\\d{2})/);\n"
    "        var d = dMatch ? dMatch[1] : '';\n"
    "        var dateOk = (!df || !d || d >= df) && (!dt || !d || d <= dt);\n"
    "        var show = textOk && dateOk;\n"
    "        row.style.display = show ? '' : 'none';\n"
    "        total++; if (show) vis++;\n"
    "      });\n"
    "    } else {\n"
    "      var groups = document.querySelectorAll('[data-picked-grp]');\n"
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
    "  window._pickedFilterReset = function() {\n"
    "    var el;\n"
    "    el = document.getElementById('picked-q');  if (el) el.value = '';\n"
    "    el = document.getElementById('picked-df'); if (el) el.value = '';\n"
    "    el = document.getElementById('picked-dt'); if (el) el.value = '';\n"
    "    el = document.getElementById('picked-count'); if (el) el.textContent = '';\n"
    "    window._pickedFilter();\n"
    "  };\n"
)

patch('P3-picked-filterfn',
    "  window.loadPickedPage = loadPickedPage;\n",
    "  window.loadPickedPage = loadPickedPage;\n"
    + PICKED_FILTER_FN
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
