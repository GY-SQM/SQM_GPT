#!/usr/bin/env python3
"""
patch_alloc_revert_btn.py
목적: ALLOCATION 툴바에 '이전 단계로' 레이블 + ↩ →AVAILABLE 되돌리기 버튼 추가
      (Picked 툴바와 동일 패턴)
적용: 2026-05-25  파일: sqm-allocation.js (CRLF)
"""
import os, sys

TARGET = os.path.normpath(os.path.join(os.path.dirname(__file__),
    '..', 'frontend', 'js', 'sqm-allocation.js'))

def crlf(s):
    return s.replace('\n', '\r\n')

OLD = crlf(
    "      '  <span style=\"flex:1\"></span>',\n"
    "      '  <button class=\"btn\" style=\"font-size:12px;padding:3px 10px;background:var(--accent,#3b82f6);color:#fff;border:1px solid var(--accent,#3b82f6);border-radius:4px\" onclick=\"window.allocUploadExcel()\">📂 Excel 업로드</button>',\n"
    "      '  <button class=\"btn\" style=\"font-size:12px;padding:3px 10px;border-radius:4px\" onclick=\"renderPage(\\'allocation\\')\">🔁 새로고침</button>',\n"
    "      '</div>',"
).encode('utf-8')

NEW = crlf(
    "      '  <span style=\"flex:1\"></span>',\n"
    "      '  <span style=\"font-size:11px;color:var(--text-muted);flex-shrink:0\">이전 단계로</span>',\n"
    "      '  <button class=\"btn\" style=\"font-size:12px;padding:3px 10px;background:rgba(239,68,68,0.15);color:#ef4444;border:1px solid #ef444455;border-radius:4px\" onclick=\"window.allocRevertStep(\\'RESERVED\\')\">↩ →AVAILABLE</button>',\n"
    "      '  <button class=\"btn\" style=\"font-size:12px;padding:3px 10px;background:var(--accent,#3b82f6);color:#fff;border:1px solid var(--accent,#3b82f6);border-radius:4px\" onclick=\"window.allocUploadExcel()\">📂 Excel 업로드</button>',\n"
    "      '  <button class=\"btn\" style=\"font-size:12px;padding:3px 10px;border-radius:4px\" onclick=\"renderPage(\\'allocation\\')\">🔁 새로고침</button>',\n"
    "      '</div>',"
).encode('utf-8')

with open(TARGET, 'rb') as f:
    data = f.read()

if OLD not in data:
    print('[MISS] 패치 대상 없음 — 이미 적용됐거나 내용 불일치')
    print(repr(OLD[:120]))
    sys.exit(1)

data = data.replace(OLD, NEW, 1)

with open(TARGET, 'wb') as f:
    f.write(data)

print('[OK] 저장 완료:', TARGET)
