#!/usr/bin/env python3
"""
patch_footer_allocation.py
==========================
sqm-allocation.js — Allocation tfoot 폰트 1.5x (추가, font-size:19px)

기존 tfoot: background:#FFD600;font-weight:800;color:#222
변경 tfoot: background:#FFD600;font-weight:800;color:#222;font-size:19px

대상: frontend/js/sqm-allocation.js (IIFE, ABSOLUTE EDIT BAN)
방식: bytes 레벨 find & replace
"""
import sys, os, shutil, subprocess
from datetime import datetime

BASE   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(BASE, 'frontend', 'js', 'sqm-allocation.js')

OLD = b"      '<tr style=\"background:#FFD600;font-weight:800;color:#222\">' +\n"
NEW = b"      '<tr style=\"background:#FFD600;font-weight:800;color:#222;font-size:19px\">' +\n"

def main():
    if not os.path.exists(TARGET):
        print(f"❌ 파일 없음: {TARGET}")
        sys.exit(1)

    with open(TARGET, 'rb') as f:
        data = f.read()

    if b'font-size:19px' in data and OLD not in data:
        print("ℹ️  이미 적용됨 — 스킵")
        return

    # LF/CRLF 시도
    if OLD in data:
        anchor, rep, mode = OLD, NEW, "LF"
    else:
        old_cr = OLD.replace(b'\n', b'\r\n')
        new_cr = NEW.replace(b'\n', b'\r\n')
        if old_cr in data:
            anchor, rep, mode = old_cr, new_cr, "CRLF"
        else:
            print("❌ 앵커를 찾지 못했습니다.")
            idx = data.find(b'background:#FFD600;font-weight:800;color:#222')
            if idx != -1:
                print(f"  → 유사 패턴 위치 {idx}:", repr(data[idx:idx+120]))
            sys.exit(1)

    bak = TARGET + '.bak_footer_alloc_' + datetime.now().strftime('%Y%m%d_%H%M%S')
    shutil.copy2(TARGET, bak)
    print(f"📦 백업: {bak}")

    new_data = data.replace(anchor, rep, 1)
    with open(TARGET, 'wb') as f:
        f.write(new_data)
    print(f"✅ 패치 완료 ({len(data)} → {len(new_data)} bytes, {mode})")

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
