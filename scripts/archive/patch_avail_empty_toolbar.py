#!/usr/bin/env python3
"""
patch_avail_empty_toolbar.py
목적: AVAILABLE 페이지 — rows=0(빈 상태)일 때도 툴바가 표시되도록 수정
원인: loadAvailablePage()에서 rows.length==0 시 early return하여 툴바 미렌더
적용: 2026-05-25  파일: sqm-inventory.js (CRLF)
"""
import os, sys

TARGET = os.path.normpath(os.path.join(os.path.dirname(__file__),
    '..', 'frontend', 'js', 'sqm-inventory.js'))

OLD = (
    "      if (!rows.length) {\r\n"
    "        c.innerHTML = '<div class=\"empty\" style=\"padding:60px;text-align:center;color:var(--text-muted,#888)\">✅ Available 재고 없음 (전량 배분 또는 피킹 완료)</div>';\r\n"
    "        return;\r\n"
    "      }"
).encode('utf-8')

NEW = (
    "      if (!rows.length) {\r\n"
    "        c.innerHTML = '<section style=\"padding:12px 16px\">'\r\n"
    "          + '<div style=\"display:flex;align-items:center;gap:6px;padding:8px 0 10px;flex-wrap:wrap\">'\r\n"
    "          + '<h2 style=\"margin:0;font-size:14px;white-space:nowrap;flex-shrink:0\">✅ AVAILABLE</h2>'\r\n"
    "          + '<span style=\"font-size:11px;color:var(--text-muted);flex-shrink:0\">그룹:</span>'\r\n"
    "          + _availModeBtn('lot','LOT별') + _availModeBtn('container','컨테이너별') + _availModeBtn('date','입고일별')\r\n"
    "          + '<span style=\"flex:1\"></span>'\r\n"
    "          + '<button class=\"btn\" style=\"font-size:12px;padding:3px 10px;background:rgba(239,68,68,0.15);color:#ef4444;border:1px solid #ef444455;border-radius:4px\" onclick=\"window.availCancelSelected()\">↩️ →PENDING</button>'\r\n"
    "          + '<button class=\"btn\" style=\"font-size:12px;padding:3px 10px;border-radius:4px\" onclick=\"window.loadAvailablePage()\">🔄 새로고침</button>'\r\n"
    "          + '</div>'\r\n"
    "          + '<div class=\"empty\" style=\"padding:60px;text-align:center;color:var(--text-muted,#888)\">✅ Available 재고 없음 (전량 배분 또는 피킹 완료)</div></section>';\r\n"
    "        return;\r\n"
    "      }"
).encode('utf-8')

with open(TARGET, 'rb') as f:
    data = f.read()

if OLD not in data:
    print('[MISS] 패치 대상 없음 — 이미 적용됐거나 내용 불일치')
    print(repr(OLD[:80]))
    sys.exit(1)

data = data.replace(OLD, NEW, 1)

with open(TARGET, 'wb') as f:
    f.write(data)

print('[OK] 저장 완료')
