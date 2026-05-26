#!/usr/bin/env python3
"""
patch_search_picked2.py
목적: patch_search_picked.py P2 재시도 — 올바른 들여쓰기(6칸) 포함
적용: 2026-05-25  파일: sqm-picked.js (LF)
"""
import os, sys

TARGET = os.path.normpath(os.path.join(os.path.dirname(__file__),
    '..', 'frontend', 'js', 'sqm-picked.js'))

with open(TARGET, 'rb') as f:
    data = f.read()

SEARCH_BAR_LINES = (
    "      '<div style=\"display:flex;align-items:center;gap:6px;padding:6px 0 8px;flex-wrap:wrap;border-bottom:1px solid var(--border,#334155);margin-bottom:8px\">',\n"
    "      '  <span style=\"font-size:11px;color:var(--text-muted);flex-shrink:0\">🔍 검색</span>',\n"
    "      '  <input id=\"picked-q\" type=\"text\" placeholder=\"LOT · BL · 고객사\" style=\"font-size:12px;padding:3px 8px;background:var(--surface,#1e293b);border:1px solid var(--border,#334155);border-radius:4px;color:var(--text-primary);width:180px\" oninput=\"window._pickedFilter()\">',\n"
    "      '  <span style=\"font-size:11px;color:var(--text-muted);flex-shrink:0\">날짜</span>',\n"
    "      '  <input id=\"picked-df\" type=\"date\" style=\"font-size:12px;padding:2px 6px;background:var(--surface,#1e293b);border:1px solid var(--border,#334155);border-radius:4px;color:var(--text-primary)\" onchange=\"window._pickedFilter()\">',\n"
    "      '  <span style=\"font-size:11px;color:var(--text-muted)\">~</span>',\n"
    "      '  <input id=\"picked-dt\" type=\"date\" style=\"font-size:12px;padding:2px 6px;background:var(--surface,#1e293b);border:1px solid var(--border,#334155);border-radius:4px;color:var(--text-primary)\" onchange=\"window._pickedFilter()\">',\n"
    "      '  <button class=\"btn\" style=\"font-size:12px;padding:3px 10px;border-radius:4px\" onclick=\"window._pickedFilterReset()\">✕ 초기화</button>',\n"
    "      '  <span id=\"picked-count\" style=\"font-size:11px;color:var(--text-muted)\"></span>',\n"
    "      '</div>',\n"
)

OLD = (
    "      '  <button class=\"btn\" style=\"font-size:12px;padding:3px 10px;border-radius:4px\" onclick=\"renderPage(\\'picked\\')\">🔁 새로고침</button>',\n"
    "      '</div>',\n"
    "      '<div id=\"picked-loading\" style=\"padding:40px;text-align:center;color:var(--text-muted)\">⏳ 데이터 로딩 중...</div>',\n"
).encode('utf-8')

NEW = (
    "      '  <button class=\"btn\" style=\"font-size:12px;padding:3px 10px;border-radius:4px\" onclick=\"renderPage(\\'picked\\')\">🔁 새로고침</button>',\n"
    "      '</div>',\n"
    + SEARCH_BAR_LINES +
    "      '<div id=\"picked-loading\" style=\"padding:40px;text-align:center;color:var(--text-muted)\">⏳ 데이터 로딩 중...</div>',\n"
).encode('utf-8')

if OLD not in data:
    print('[MISS] 패치 대상 없음')
    print(repr(OLD[:100]))
    sys.exit(1)

data = data.replace(OLD, NEW, 1)

with open(TARGET, 'wb') as f:
    f.write(data)
print('[OK] 저장 완료')
