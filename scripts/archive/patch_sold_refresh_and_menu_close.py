# -*- coding: utf-8 -*-
"""
patch_sold_refresh_and_menu_close.py — v8.6.9 (2026-05-25)

수정 사항:
  1. (Issue 2) SOLD 모달 열 때 메뉴바 자동 닫기
  2. (Issue 3) SOLD 확정 성공 후 PICKED/Outbound 페이지 자동 새로고침

대상: frontend/js/sqm-upload-modals.js (IIFE) → patch script 사용
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "frontend" / "js" / "sqm-upload-modals.js"


# (1) 모달 진입 시 메뉴 자동 닫기 — function showBarcodeSoldConfirmModal() { 직후에 추가
OLD_1 = """  function showBarcodeSoldConfirmModal() {
    var overlay = document.createElement('div');"""

NEW_1 = """  function showBarcodeSoldConfirmModal() {
    // v8.6.9 fix: 메뉴바 자동 닫기 (onclick으로 호출되면 closeAllMenus 미호출되는 문제)
    try { if (window.closeAllMenus) window.closeAllMenus(); } catch (_e) {}
    var overlay = document.createElement('div');"""


# (2) 확정(apply) 성공 시 PICKED / Outbound / 현재 페이지 자동 새로고침
OLD_2 = """    btnApply.onclick = function() {
      if (!confirm('정말 ' + (btnApply.textContent.match(/\\d+/) || [0]) + '건을 SOLD 로 확정하시겠습니까?\\n\\n⚠️ SOLD 는 취소할 수 없습니다 (차량 출발 = 거래 종료).')) return;
      _upload(false, function() {
        btnApply.style.display = 'none';
        btnPrev.disabled = true;
      });
    };
  }"""

NEW_2 = """    btnApply.onclick = function() {
      if (!confirm('정말 ' + (btnApply.textContent.match(/\\d+/) || [0]) + '건을 SOLD 로 확정하시겠습니까?\\n\\n⚠️ SOLD 는 취소할 수 없습니다 (차량 출발 = 거래 종료).')) return;
      _upload(false, function(d) {
        btnApply.style.display = 'none';
        btnPrev.disabled = true;
        // v8.6.9 fix Issue 3: SOLD 확정 후 관련 페이지 자동 새로고침
        // (현재 활성 페이지가 picked/outbound면 즉시 다시 로드 → SOLD된 톤백 사라짐)
        try {
          var route = window.getCurrentRoute && window.getCurrentRoute();
          if (route === 'picked' && window.loadPickedPage)      { window.loadPickedPage(); }
          else if (route === 'outbound' && window.loadOutboundPage) { window.loadOutboundPage(); }
          else if (route === 'inventory' && window.loadInventoryPage) { window.loadInventoryPage(); }
          else if (route === 'available' && window.loadAvailablePage) { window.loadAvailablePage(); }
          else if (route === 'allocation' && window.loadAllocationPage) { window.loadAllocationPage(); }
        } catch (_e) {}
        // 사이드바 뱃지(카운트)도 갱신
        try { if (window.refreshSidebarBadges) window.refreshSidebarBadges(); } catch (_e) {}
      });
    };
  }"""


PATCHES = [
    ("(1) 모달 진입 시 메뉴 닫기", OLD_1, NEW_1),
    ("(2) SOLD 성공 후 페이지 자동 새로고침", OLD_2, NEW_2),
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
    backup = TARGET.with_suffix(TARGET.suffix + ".bak_refresh_fix")
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
