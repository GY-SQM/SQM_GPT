# -*- coding: utf-8 -*-
"""
scripts/patch_sold_terminology.py
==================================
UI 표기 통일 — OUTBOUND 텍스트 → SOLD

대상:
  frontend/js/sqm-logistics.js  — 페이지 제목 / 스캔 버튼
  frontend/js/sqm-allocation.js — 컬럼 헤더 / 전체초기화 confirm 텍스트

변경하지 않는 것:
  - API 경로명 (/api/outbound/...)
  - JS 함수·변수명 (loadOutboundPage, _outboundExpandedLot 등)
  - CSS 클래스명 (outbound-summary-row 등)
  - data-action / data-route 속성값 (기능 연결)
  - movement_type 문자열
"""
from __future__ import annotations
import io
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

BASE = Path(__file__).resolve().parent.parent / "frontend" / "js"

PATCHES = [
    # ── sqm-logistics.js ──────────────────────────────────────────────
    {
        "file": BASE / "sqm-logistics.js",
        "replacements": [
            # 페이지 제목
            (
                "'  <h2 style=\"margin:0\">📤 출고 완료 (Sold / Outbound)</h2>',",
                "'  <h2 style=\"margin:0\">📤 출고 완료 (SOLD)</h2>',",
            ),
            # 스캔 페이지 빠른 동작 버튼 레이블 (quickAction outbound는 유지)
            (
                ">Outbound</button>',",
                ">Sold</button>',",
            ),
        ],
    },
    # ── sqm-allocation.js ─────────────────────────────────────────────
    {
        "file": BASE / "sqm-allocation.js",
        "replacements": [
            # 배정 테이블 컬럼 헤더
            (
                "'    <th>OUTBOUND DATE</th>',",
                "'    <th>SOLD DATE</th>',",
            ),
            # 전체 초기화 confirm 텍스트
            (
                "모든 RESERVED/PICKED/OUTBOUND 배정을 취소하고 AVAILABLE로 원복합니다.",
                "모든 RESERVED/PICKED/SOLD 배정을 취소하고 AVAILABLE로 원복합니다.",
            ),
        ],
    },
]


def apply_patches() -> int:
    errors = 0
    for spec in PATCHES:
        path: Path = spec["file"]
        if not path.exists():
            print(f"[SKIP] 파일 없음: {path}")
            errors += 1
            continue

        text = path.read_text(encoding="utf-8")
        changed = False
        for old, new in spec["replacements"]:
            if old in text:
                text = text.replace(old, new, 1)
                changed = True
                print(f"[OK]   {path.name}: '{old[:50]}...' -> 변경")
            else:
                print(f"[WARN] {path.name}: 패턴 미발견 — '{old[:60]}'")

        if changed:
            path.write_text(text, encoding="utf-8")
            print(f"[SAVE] {path.name} 저장 완료")

    return errors


if __name__ == "__main__":
    errs = apply_patches()
    sys.exit(errs)
