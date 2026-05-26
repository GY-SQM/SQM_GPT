#!/usr/bin/env python3
"""
patch_sold_excel.py
목적: SOLD 툴바에 📊 Excel 내보내기 버튼 추가 + exportSoldExcel 함수 등록
적용: 2026-05-25
파일: sqm-logistics.js (LF, IIFE → patch script)
"""
import sys, os

TARGET = os.path.normpath(os.path.join(os.path.dirname(__file__),
    '..', 'frontend', 'js', 'sqm-logistics.js'))

with open(TARGET, 'rb') as f:
    data = f.read()

# ── P1: exportSoldExcel 함수를 _soldSearch 바로 앞에 삽입 ──
OLD1 = "  window._soldSearch = function() {".encode('utf-8')
NEW1 = (
    "  window.exportSoldExcel = function() {\n"
    "    var tbl = document.getElementById('outbound-table');\n"
    "    if (!tbl) { showToast('warning', '내보낼 테이블이 없습니다'); return; }\n"
    "    var ts = new Date().toISOString().slice(0, 10);\n"
    "    if (window.exportTableToExcel) {\n"
    "      window.exportTableToExcel(tbl, 'SOLD_' + ts + '.xlsx');\n"
    "    } else {\n"
    "      showToast('warning', 'Excel 내보내기 함수를 찾을 수 없습니다');\n"
    "    }\n"
    "  };\n"
    "  window._soldSearch = function() {"
).encode('utf-8')

# ── P2: 툴바에 Excel 버튼 추가 (🔍 조회 바로 뒤, flex:1 spacer 앞) ──
OLD2 = (
    "      '  <span style=\"flex:1\"></span>',\n"
    "      '  <span style=\"font-size:11px;color:var(--text-muted);flex-shrink:0\">이전 단계로</span>',"
).encode('utf-8')
NEW2 = (
    "      '  <button class=\"btn\" onclick=\"window.exportSoldExcel()\" style=\"font-size:12px;padding:3px 10px;flex-shrink:0\">📊 Excel</button>',\n"
    "      '  <span style=\"flex:1\"></span>',\n"
    "      '  <span style=\"font-size:11px;color:var(--text-muted);flex-shrink:0\">이전 단계로</span>',"
).encode('utf-8')

errors = 0
for i, (old, new) in enumerate([(OLD1, NEW1), (OLD2, NEW2)], 1):
    if old not in data:
        print(f'[MISS P{i}]', repr(old[:60]))
        errors += 1
    else:
        data = data.replace(old, new, 1)
        print(f'[OK  P{i}]')

if not errors:
    with open(TARGET, 'wb') as f:
        f.write(data)
    print(f'[저장] {TARGET}')
else:
    print('[중단] 저장 안 함')
