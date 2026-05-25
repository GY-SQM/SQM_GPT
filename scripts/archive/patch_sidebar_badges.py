#!/usr/bin/env python3
"""
patch_sidebar_badges.py
=======================
sqm-core.js loadSidebarBadges() 업데이트 (v8.6.9)
  - 각 사이드바 버튼에 "톤백 N개 · 샘플 M개" 표시
  - 기존: 서브메뉴 배지 모두 비움 (2026-05-05 지시)
  - 변경: 각 상태별 bags / sample_bags 표시

대상: frontend/js/sqm-core.js (IIFE, ABSOLUTE EDIT BAN)
방식: bytes 레벨 find & replace
"""
import sys, os, shutil, subprocess
from datetime import datetime

BASE   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(BASE, 'frontend', 'js', 'sqm-core.js')

# ── 앵커: 기존 배지 숨김 블록 ~ badge-inv-total 설정 ─────────────────
OLD = (
    b"      // \xec\x84\x9c\xeb\xb8\x8c\xeb\xa9\x94\xeb\x89\xb4 \xeb\xb0\xb0\xec\xa7\x80 \xec\x88\xa8\xea\xb9\x80 \xec\xb2\x98\xeb\xa6\xac\n"
    b"      ['badge-available','badge-allocation','badge-picked','badge-return'].forEach(function(id){\n"
    b"        var el = document.getElementById(id);\n"
    b"        if (el) el.textContent = '';\n"
    b"      });\n"
    b"      // \xec\x83\x81\xeb\x8b\xa8 Inventory \xeb\xb2\x84\xed\x8a\xbc \xec\xb4\x9d\xea\xb3\x84\xeb\x8a\x94 \xec\x9c\xa0\xec\xa7\x80\n"
    b"      var tot = document.getElementById('badge-inv-total');\n"
    b"      if (tot && d.total) tot.textContent = d.total.bags + '\xea\xb0\x9c \xc2\xb7 ' + d.total.mt.toFixed(3) + 'MT';\n"
)

NEW = (
    b"      // v8.6.9: \xec\x83\x81\xed\x83\x9c\xeb\xb3\x84 \xeb\xb0\xb0\xec\xa7\x80 \xed\x91\x9c\xec\x8b\x9c (\xed\x86\xa4\xeb\xb0\xb1 N\xea\xb0\x9c \xc2\xb7 \xec\x83\x98\xed\x94\x8c M\xea\xb0\x9c)\n"
    b"      function _badge(id, data) {\n"
    b"        var el = document.getElementById(id);\n"
    b"        if (!el || !data) return;\n"
    b"        var txt = '\xed\x86\xa4\xeb\xb0\xb1 ' + data.bags + '\xea\xb0\x9c';\n"
    b"        if (data.sample_bags > 0) txt += ' \xc2\xb7 \xec\x83\x98\xed\x94\x8c ' + data.sample_bags + '\xea\xb0\x9c';\n"
    b"        el.textContent = txt;\n"
    b"      }\n"
    b"      _badge('badge-pending',    d.pending);\n"
    b"      _badge('badge-available',  d.available);\n"
    b"      _badge('badge-allocation', d.reserved);\n"
    b"      _badge('badge-picked',     d.picked);\n"
    b"      _badge('badge-sold',       d.sold);\n"
    b"      _badge('badge-return',     d['return']);\n"
    b"      // \xec\x83\x81\xeb\x8b\xa8 Inventory \xeb\xb2\x84\xed\x8a\xbc \xec\xb4\x9d\xea\xb3\x84 \xec\x9c\xa0\xec\xa7\x80\n"
    b"      var tot = document.getElementById('badge-inv-total');\n"
    b"      if (tot && d.total) tot.textContent = d.total.bags + '\xea\xb0\x9c \xc2\xb7 ' + d.total.mt.toFixed(3) + 'MT';\n"
)

def main():
    if not os.path.exists(TARGET):
        print(f"❌ 파일 없음: {TARGET}")
        sys.exit(1)

    with open(TARGET, 'rb') as f:
        data = f.read()

    # LF 버전도 시도
    old_lf = OLD.replace(b'\n', b'\r\n') if b'\r\n' not in OLD else OLD
    if OLD in data:
        anchor, rep = OLD, NEW
        print("앵커: LF 버전 매칭")
    else:
        old_crlf = OLD.replace(b'\n', b'\r\n')
        if old_crlf in data:
            anchor = old_crlf
            rep = NEW.replace(b'\n', b'\r\n')
            print("앵커: CRLF 버전 매칭")
        else:
            print("❌ 앵커를 찾지 못했습니다. 이미 적용됐거나 파일이 변경됐습니다.")
            check = b"badge-available','badge-allocation','badge-picked','badge-return"
            idx = data.find(check)
            if idx != -1:
                print(f"  → 유사 패턴 위치 {idx}:", repr(data[idx:idx+200]))
            sys.exit(1)

    count = data.count(anchor)
    if count > 1:
        print(f"⚠️  앵커 {count}개 — 첫 번째만 치환")

    bak = TARGET + '.bak_badges_' + datetime.now().strftime('%Y%m%d_%H%M%S')
    shutil.copy2(TARGET, bak)
    print(f"📦 백업: {bak}")

    new_data = data.replace(anchor, rep, 1)
    with open(TARGET, 'wb') as f:
        f.write(new_data)
    print(f"✅ 패치 완료 ({len(data)} → {len(new_data)} bytes)")

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
