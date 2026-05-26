# -*- coding: utf-8 -*-
"""
patch_sold_modal_labels.py — v8.6.9 (2026-05-25)

SOLD 확정 모달의 라벨을 새 비즈니스 로직에 맞게 수정.

변경:
  - "상태 불일치" 배지 → "중복 스킵 (SOLD)"
  - "PICKED 아님 — 처리 안 됨" → "이미 SOLD 처리됨 (중복 스킵)"
  - 매칭 결과에 previous_status 표시 (어떤 상태에서 SOLD로 전환되는지)

대상: frontend/js/sqm-upload-modals.js (IIFE) → patch script 사용
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "frontend" / "js" / "sqm-upload-modals.js"


# (1) 상단 4분면 배지 라벨 변경
OLD_1 = """'<div style="padding:8px;background:rgba(245,158,11,0.1);border:1px solid #f59e0b44;border-radius:4px;text-align:center"><div style="color:#f59e0b;font-weight:800;font-size:18px">' + (s.mismatch_status||0) + '</div><div style="font-size:11px;color:var(--text-muted,#94a3b8)">상태 불일치</div></div>'"""

NEW_1 = """'<div style="padding:8px;background:rgba(245,158,11,0.1);border:1px solid #f59e0b44;border-radius:4px;text-align:center"><div style="color:#f59e0b;font-weight:800;font-size:18px">' + (s.mismatch_status||0) + '</div><div style="font-size:11px;color:var(--text-muted,#94a3b8)">중복 스킵<br>(이미 SOLD)</div></div>'"""


# (2) 상세 목록 제목 + 항목 표시 변경
OLD_2 = """      html += _list('⚠️ 상태 불일치 (PICKED 아님 — 처리 안 됨)', mismatch, '#f59e0b', function(it){
        return '<div>' + (it.tonbag_uid||'-') + ' · 현재: ' + (it.current_status||'?') + ' · 위치: ' + (it.actual_location||'-') + '</div>';
      });"""

NEW_2 = """      html += _list('⏸️ 중복 스킵 (이미 SOLD 처리됨)', mismatch, '#f59e0b', function(it){
        var note = it.note ? ' · ' + it.note : '';
        return '<div>' + (it.tonbag_uid||'-') + ' · 현재: ' + (it.current_status||'?') + ' · 위치: ' + (it.actual_location||'-') + note + '</div>';
      });"""


# (3) matched 결과에 previous_status 표시 추가 (locChanged 안내 직후에 매칭 상세 추가)
OLD_3 = """      if (locChanged > 0) {
        html += '<div style="background:rgba(245,158,11,0.15);border-left:3px solid #f59e0b;padding:6px 10px;margin-bottom:8px;font-size:12px">📍 위치 변경 예정: <strong>' + locChanged + '</strong>건 (직원이 스캔한 실제 위치로 갱신)</div>';
      }"""

NEW_3 = """      if (locChanged > 0) {
        html += '<div style="background:rgba(245,158,11,0.15);border-left:3px solid #f59e0b;padding:6px 10px;margin-bottom:8px;font-size:12px">📍 위치 변경 예정: <strong>' + locChanged + '</strong>건 (직원이 스캔한 실제 위치로 갱신)</div>';
      }
      // v8.6.9: 이전 상태 분포 표시 (어떤 상태에서 SOLD로 전환되는지)
      if (matched.length > 0) {
        var prevDist = {};
        matched.forEach(function(m){ var ps = m.previous_status || '?'; prevDist[ps] = (prevDist[ps]||0)+1; });
        var distStr = Object.keys(prevDist).map(function(k){ return k + ' ' + prevDist[k] + '건'; }).join(' · ');
        html += '<div style="background:rgba(34,197,94,0.1);border-left:3px solid #22c55e;padding:6px 10px;margin-bottom:8px;font-size:12px">🔄 상태 전환: ' + distStr + ' → <strong>SOLD</strong></div>';
      }"""


PATCHES = [
    ("(1) 상단 배지 라벨 변경", OLD_1, NEW_1),
    ("(2) 상세 목록 제목 + 항목", OLD_2, NEW_2),
    ("(3) 이전 상태 분포 표시", OLD_3, NEW_3),
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
    backup = TARGET.with_suffix(TARGET.suffix + ".bak_labels")
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
