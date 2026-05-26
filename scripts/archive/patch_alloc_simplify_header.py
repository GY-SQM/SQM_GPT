# -*- coding: utf-8 -*-
"""
patch_alloc_simplify_header.py — v8.6.9 (2026-05-25)

Allocation 페이지 단순화: 상단 헤더 액션 버튼 4개 + "단계 되돌리기" 박스 삭제.

삭제 대상:
  - ❌ 배정 취소 (allocCancelSelected)  — RESERVED → AVAILABLE 되돌리기
  - 📦 PICKED   (allocPickSelected)     — RESERVED → PICKED 전진
  - 🔒 SOLD     (allocConfirmSelected) — PICKED → SOLD 전진
  - ⋯ 더보기    (showAllocMoreMenu)    — 추가 작업 메뉴
  - ↩ 단계 되돌리기 박스 전체 (RESERVED → AVAILABLE 버튼)

유지:
  - 📂 Excel 업로드
  - 🔁 새로고침

대상: frontend/js/sqm-allocation.js (946줄, IIFE) → patch script 필수.
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "frontend" / "js" / "sqm-allocation.js"


# 헤더 액션 버튼 4개 삭제 (line 48~51)
OLD_HEADER = """      '    <button class="btn btn-primary" onclick="window.allocUploadExcel()">📂 Excel 업로드</button>',
      '    <button class="btn btn-danger" onclick="window.allocCancelSelected()">❌ 배정 취소</button>',
      '    <button class="btn" onclick="window.allocPickSelected()" title="RESERVED → PICKED">📦 PICKED</button>',
      '    <button class="btn" onclick="window.allocConfirmSelected()" title="PICKED → SOLD">🔒 SOLD</button>',
      '    <button class="btn btn-secondary" onclick="window.showAllocMoreMenu(this)" title="추가 작업">⋯ 더보기</button>',
      '    <button class="btn btn-secondary" onclick="renderPage(\\'allocation\\')">🔁 새로고침</button>',"""

NEW_HEADER = """      '    <button class="btn btn-primary" onclick="window.allocUploadExcel()">📂 Excel 업로드</button>',
      '    <button class="btn btn-secondary" onclick="renderPage(\\'allocation\\')">🔁 새로고침</button>',"""


# "단계 되돌리기" 박스 전체 삭제 (line 55~59)
OLD_REVERT = """      '</div>',
      /* ── 단계 되돌리기 ── */
      '<div style="display:flex;flex-wrap:wrap;gap:6px;align-items:center;padding:6px 10px;background:var(--panel);border:1px solid var(--panel-border);border-radius:6px;margin-bottom:8px">',
      '  <span style="font-size:12px;font-weight:600;white-space:nowrap">↩ 단계 되돌리기:</span>',
      '  <button class="btn" onclick="window.allocRevertStep(\\'RESERVED\\')" style="font-size:12px">RESERVED → AVAILABLE</button>',
      '</div>',
      /* ── 로딩 / 빈 상태 ── */"""

NEW_REVERT = """      '</div>',
      /* ── 로딩 / 빈 상태 ── */"""


PATCHES = [
    ("헤더 액션 버튼 4개 삭제 (배정취소/PICKED/SOLD/더보기)", OLD_HEADER, NEW_HEADER),
    ("'단계 되돌리기' 박스 전체 삭제",                       OLD_REVERT, NEW_REVERT),
]


def main() -> int:
    if not TARGET.exists():
        print(f"[ERROR] 대상 없음: {TARGET}")
        return 1
    src = TARGET.read_text(encoding="utf-8")
    for label, old, new in PATCHES:
        if old not in src:
            print(f"[ERROR] {label} — OLD 매칭 실패")
            return 2
        if src.count(old) > 1:
            print(f"[ERROR] {label} — OLD 다중 매칭 ({src.count(old)})")
            return 3
        src = src.replace(old, new, 1)
        print(f"[OK]   {label}")
    backup = TARGET.with_suffix(TARGET.suffix + ".bak_simplify_header")
    backup.write_text(TARGET.read_text(encoding="utf-8"), encoding="utf-8")
    TARGET.write_text(src, encoding="utf-8")
    print(f"[BACKUP] {backup.name}")
    print(f"[WRITE]  {TARGET.name}")
    import subprocess
    r = subprocess.run(["node", "--check", str(TARGET)], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"[node --check] FAIL:\n{r.stderr}")
        return 4
    print("[node --check] OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
