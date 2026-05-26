#!/usr/bin/env python3
"""
patch_search_alloc.py
목적: Allocation 탭에 검색바(LOT·BL·Sale Ref 텍스트 + 고객사 입력) 추가
     기존 _renderAllocTable() 필터 파이프라인에 텍스트 검색 통합
적용: 2026-05-25  파일: sqm-allocation.js (CRLF)
"""
import os, sys

TARGET = os.path.normpath(os.path.join(os.path.dirname(__file__),
    '..', 'frontend', 'js', 'sqm-allocation.js'))

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
#  P1: _allocState에 searchQ / searchCust 추가
# ─────────────────────────────────────────────────────
patch('P1-allocstate',
    "  var _allocState = {\n"
    "    currentFilter: 'all',\n"
    "    rows: [],\n"
    "    selectedLots: new Set()\n"
    "  };\n",
    "  var _allocState = {\n"
    "    currentFilter: 'all',\n"
    "    rows: [],\n"
    "    selectedLots: new Set(),\n"
    "    searchQ: '',\n"
    "    searchCust: ''\n"
    "  };\n"
)

# ─────────────────────────────────────────────────────
#  P2: _renderAllocTable 필터에 텍스트/고객사 검색 추가
# ─────────────────────────────────────────────────────
patch('P2-renderfiler',
    "    var rows = _allocState.rows.filter(function(r){\n"
    "      if (filter === 'all') return true;\n"
    "      return (r.status || 'RESERVED').toUpperCase() === filter;\n"
    "    });\n",
    "    var _sQ = (_allocState.searchQ||'').toLowerCase().trim();\n"
    "    var _sC = (_allocState.searchCust||'').toLowerCase().trim();\n"
    "    var rows = _allocState.rows.filter(function(r){\n"
    "      if (filter !== 'all' && (r.status||'RESERVED').toUpperCase() !== filter) return false;\n"
    "      if (_sQ) {\n"
    "        var _t = [(r.lot_no||''),(r.bl_no||''),(r.sale_ref||''),(r.sap_no||''),(r.product||'')].join(' ').toLowerCase();\n"
    "        if (_t.indexOf(_sQ) === -1) return false;\n"
    "      }\n"
    "      if (_sC) {\n"
    "        var _c = (r.customer||r.sold_to||'').toLowerCase();\n"
    "        if (_c.indexOf(_sC) === -1) return false;\n"
    "      }\n"
    "      return true;\n"
    "    });\n"
)

# ─────────────────────────────────────────────────────
#  P3: 검색바 HTML — 툴바 </div> 뒤, 로딩 div 앞에 삽입
# ─────────────────────────────────────────────────────
patch('P3-alloc-searchbar',
    "      '</div>',\n"
    "      /* ── 로딩 / 빈 상태 ── */\n",
    "      '</div>',\n"
    "      '<div style=\"display:flex;align-items:center;gap:6px;padding:6px 0 8px;flex-wrap:wrap;border-bottom:1px solid var(--border,#334155);margin-bottom:8px\">',\n"
    "      '  <span style=\"font-size:11px;color:var(--text-muted);flex-shrink:0\">🔍 검색</span>',\n"
    "      '  <input id=\"alloc-q\" type=\"text\" placeholder=\"LOT · BL · Sale Ref · SAP\" style=\"font-size:12px;padding:3px 8px;background:var(--surface,#1e293b);border:1px solid var(--border,#334155);border-radius:4px;color:var(--text-primary);width:160px\" oninput=\"window._allocFilter()\">',\n"
    "      '  <span style=\"font-size:11px;color:var(--text-muted);flex-shrink:0\">고객사</span>',\n"
    "      '  <input id=\"alloc-cust\" type=\"text\" placeholder=\"고객사 이름\" style=\"font-size:12px;padding:3px 8px;background:var(--surface,#1e293b);border:1px solid var(--border,#334155);border-radius:4px;color:var(--text-primary);width:120px\" oninput=\"window._allocFilter()\">',\n"
    "      '  <button class=\"btn\" style=\"font-size:12px;padding:3px 10px;border-radius:4px\" onclick=\"window._allocFilterReset()\">✕ 초기화</button>',\n"
    "      '  <span id=\"alloc-search-count\" style=\"font-size:11px;color:var(--text-muted)\"></span>',\n"
    "      '</div>',\n"
    "      /* ── 로딩 / 빈 상태 ── */\n"
)

# ─────────────────────────────────────────────────────
#  P4: 필터 함수 + 카운트 표시 — window.loadAllocationPage 뒤에 삽입
# ─────────────────────────────────────────────────────
ALLOC_FILTER_FN = (
    "\n"
    "  window._allocFilter = function() {\n"
    "    _allocState.searchQ = (document.getElementById('alloc-q')||{value:''}).value;\n"
    "    _allocState.searchCust = (document.getElementById('alloc-cust')||{value:''}).value;\n"
    "    _renderAllocTable();\n"
    "    var lbl = document.getElementById('alloc-summary-label');\n"
    "    var cnt = document.getElementById('alloc-search-count');\n"
    "    if (cnt && lbl) cnt.textContent = lbl.textContent;\n"
    "  };\n"
    "\n"
    "  window._allocFilterReset = function() {\n"
    "    _allocState.searchQ = ''; _allocState.searchCust = '';\n"
    "    var el;\n"
    "    el = document.getElementById('alloc-q');    if (el) el.value = '';\n"
    "    el = document.getElementById('alloc-cust'); if (el) el.value = '';\n"
    "    el = document.getElementById('alloc-search-count'); if (el) el.textContent = '';\n"
    "    _renderAllocTable();\n"
    "  };\n"
)

patch('P4-alloc-filterfn',
    "  window.loadAllocationPage = loadAllocationPage;\n",
    "  window.loadAllocationPage = loadAllocationPage;\n"
    + ALLOC_FILTER_FN
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
