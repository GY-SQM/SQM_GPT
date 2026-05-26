#!/usr/bin/env python3
"""
patch_revert_skip.py
목적: sqm-status-revert.js injectPanel() 에서
     available / allocation / picked 라우트도 패널 삽입 건너뜀
     → SOLD 스타일 단일 툴바와 충돌 제거
적용: 2026-05-25  파일: sqm-status-revert.js (LF)
"""
import os, sys

TARGET = os.path.normpath(os.path.join(os.path.dirname(__file__),
    '..', 'frontend', 'js', 'sqm-status-revert.js'))

OLD = (
    "  function injectPanel() {\n"
    "    var route = currentRoute();\n"
    "    if (route === 'outbound') return;\n"
).encode('utf-8')

NEW = (
    "  function injectPanel() {\n"
    "    var route = currentRoute();\n"
    "    if (route === 'outbound' || route === 'available' || route === 'allocation' || route === 'picked') return;\n"
).encode('utf-8')

with open(TARGET, 'rb') as f:
    data = f.read()

if OLD not in data:
    print('[MISS] 패치 대상 없음 — 이미 적용됐거나 내용 불일치')
    print(repr(OLD[:100]))
    sys.exit(1)

data = data.replace(OLD, NEW, 1)

with open(TARGET, 'wb') as f:
    f.write(data)

print('[OK] 저장 완료:', TARGET)
