#!/usr/bin/env python3
"""
patch_footer_inventory.py
=========================
sqm-inventory.js — Pending + Available 하단 합계 폰트 1.5x (13px → 19px)

변경 1: Pending 하단 div — font-size:13px → font-size:19px
변경 2: Available tfoot 메인행 — font-size 추가 (19px)
변경 3: Available tfoot 샘플행 — font-size 추가 (19px)

대상: frontend/js/sqm-inventory.js (IIFE, ABSOLUTE EDIT BAN)
방식: bytes 레벨 find & replace
"""
import sys, os, shutil, subprocess
from datetime import datetime

BASE   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(BASE, 'frontend', 'js', 'sqm-inventory.js')

PATCHES = [
    # ── 1. Pending 하단 div font-size:13px → 19px ──────────────────────
    (
        b"background:#FFD600;color:#222;font-weight:800;border-radius:6px;font-size:13px;text-align:right\">'\n",
        b"background:#FFD600;color:#222;font-weight:800;border-radius:6px;font-size:19px;text-align:right\">'\n",
    ),
    # ── 2. Available tfoot 메인행 — font-size:19px 추가 ─────────────────
    (
        b"      html += '<tr style=\"background:#FFD600;font-weight:800;color:#222\">';\n",
        b"      html += '<tr style=\"background:#FFD600;font-weight:800;color:#222;font-size:19px\">';\n",
    ),
    # ── 3. Available tfoot 샘플행 — font-size:19px 추가 ─────────────────
    (
        b"        html += '<tr style=\"background:#FFF9C4;font-weight:800;color:#92400e\">';\n",
        b"        html += '<tr style=\"background:#FFF9C4;font-weight:800;color:#92400e;font-size:19px\">';\n",
    ),
]

def try_patch(data, old, new):
    """LF/CRLF 양쪽 시도, 매칭된 버전으로 치환. (old, new) 쌍 반환."""
    if old in data:
        return data.replace(old, new, 1), "LF"
    old_cr = old.replace(b'\n', b'\r\n')
    new_cr = new.replace(b'\n', b'\r\n')
    if old_cr in data:
        return data.replace(old_cr, new_cr, 1), "CRLF"
    return None, None

def main():
    if not os.path.exists(TARGET):
        print(f"❌ 파일 없음: {TARGET}")
        sys.exit(1)

    with open(TARGET, 'rb') as f:
        data = f.read()

    # 이미 적용됐는지 확인 (font-size:19px 존재 여부)
    already = data.count(b'font-size:19px')
    if already >= 3:
        print(f"ℹ️  이미 적용됨 (font-size:19px {already}곳 발견) — 스킵")
        return

    bak = TARGET + '.bak_footer_inv_' + datetime.now().strftime('%Y%m%d_%H%M%S')
    shutil.copy2(TARGET, bak)
    print(f"📦 백업: {bak}")

    for i, (old, new) in enumerate(PATCHES, 1):
        new_data, mode = try_patch(data, old, new)
        if new_data is None:
            print(f"⚠️  패치 {i} 앵커 없음 — 이미 적용됐거나 파일 변경됨, 스킵")
        else:
            data = new_data
            print(f"✅ 패치 {i} 적용 ({mode})")

    with open(TARGET, 'wb') as f:
        f.write(data)
    print(f"✅ 저장 완료 ({len(data)} bytes)")

    result = subprocess.run(['node', '--check', TARGET], capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ node --check 통과")
    else:
        print("❌ node --check 실패 — 백업 복원")
        print(result.stderr)
        shutil.copy2(bak, TARGET)
        sys.exit(1)

if __name__ == '__main__':
    main()
