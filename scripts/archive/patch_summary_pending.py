# -*- coding: utf-8 -*-
"""
patch_summary_pending.py — v8.6.9

Pending 페이지 (sqm-inventory.js loadPendingPage):
  - 상단 헤더: 기존 'N LOT' 옆에 톤백/샘플 분리 합계 추가
  - 하단: 테이블 아래에 노란색 합계 div 추가 (tfoot 대체 — 그룹 모드 호환)
  - SQMSummary.compute / buildHeaderHTML / buildFooterHTML 헬퍼 사용

Rule 5: sqm-inventory.js (1259줄, IIFE) → Edit 금지 → 본 patch 스크립트 사용.
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "frontend" / "js" / "sqm-inventory.js"


# ── 헤더 패치: 'N LOT' 다음에 SQMSummary 헤더 추가 ─────────────────────
OLD_HEADER = """        + '<span style="font-size:12px;color:var(--text-muted)">' + rows.length + ' LOT</span>'
        + '<div style="display:flex;gap:4px;margin-left:auto">'
        + _pendingModeBtn('date', '📅 도착일별', mode)"""

NEW_HEADER = """        + '<span style="font-size:12px;color:var(--text-muted)">' + rows.length + ' LOT</span>'
        + (window.SQMSummary ? window.SQMSummary.buildHeaderHTML(window.SQMSummary.compute(rows, {qtyField:function(r){return Number(r.net_weight||0)/1000;}, tonbagCountField:'mxbg_pallet'})) : '')
        + '<div style="display:flex;gap:4px;margin-left:auto">'
        + _pendingModeBtn('date', '📅 도착일별', mode)"""


# ── 푸터 패치: '</section>' 직전에 합계 div 추가 ─────────────────────
# Pending은 LOT 모드(단일 테이블)와 그룹 모드(다중 테이블)가 있어 tfoot 대신 div로 추가
OLD_FOOTER = """      if (mode === 'container') html += _renderPendingByContainer(rows);
      else if (mode === 'date') html += _renderPendingByDate(rows);
      else html += _renderPendingLotRows(rows);
      html += '</section>';"""

NEW_FOOTER = """      if (mode === 'container') html += _renderPendingByContainer(rows);
      else if (mode === 'date') html += _renderPendingByDate(rows);
      else html += _renderPendingLotRows(rows);
      // ── v8.6.9: 하단 합계 (tfoot 대체 — 그룹 모드 호환) ──
      if (window.SQMSummary) {
        var _pStats = window.SQMSummary.compute(rows, {qtyField:function(r){return Number(r.net_weight||0)/1000;}, tonbagCountField:'mxbg_pallet'});
        html += '<div style="margin-top:12px;padding:10px 14px;background:#FFD600;color:#222;font-weight:800;border-radius:6px;font-size:13px;text-align:right">'
              + '⏳ Pending 합계 (' + _pStats.lotCount.toLocaleString('ko-KR') + ' LOT) · '
              + '📦 톤백 ' + Math.round(_pStats.tonbagCount).toLocaleString('ko-KR') + '개 ' + _pStats.tonbagMt.toFixed(4) + ' MT'
              + (_pStats.sampleCount > 0 ? ' · 🧪 샘플 ' + Math.round(_pStats.sampleCount).toLocaleString('ko-KR') + '개 ' + _pStats.sampleMt.toFixed(4) + ' MT' : '')
              + ' · 총 ' + _pStats.totalMt.toFixed(4) + ' MT'
              + '</div>';
      }
      html += '</section>';"""


PATCHES = [
    ("Pending 상단 헤더 합계 추가", OLD_HEADER, NEW_HEADER),
    ("Pending 하단 합계 div 추가",   OLD_FOOTER, NEW_FOOTER),
]


def main() -> int:
    if not TARGET.exists():
        print(f"[ERROR] 대상 파일 없음: {TARGET}")
        return 1

    src = TARGET.read_text(encoding="utf-8")
    original_len = len(src)
    applied = []

    for label, old, new in PATCHES:
        if old not in src:
            print(f"[SKIP] {label} — OLD 문자열을 찾지 못함")
            return 3
        if src.count(old) > 1:
            print(f"[ERROR] {label} — OLD 문자열 다중 매칭 ({src.count(old)}개)")
            return 2
        src = src.replace(old, new, 1)
        applied.append(label)
        print(f"[OK]   {label}")

    backup = TARGET.with_suffix(TARGET.suffix + ".bak_summary_pending")
    backup.write_text(TARGET.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"[BACKUP] {backup.name}")

    TARGET.write_text(src, encoding="utf-8")
    print(f"[WRITE]  {TARGET.name}  ({original_len} -> {len(src)} bytes)")

    import subprocess
    r = subprocess.run(["node", "--check", str(TARGET)], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"[node --check] FAIL:\n{r.stderr}")
        return 4
    print(f"[node --check] OK")
    print(f"\n{len(applied)} patches applied.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
