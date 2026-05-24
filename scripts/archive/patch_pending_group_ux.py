"""
patch_pending_group_ux.py  (v8.6.9)
Pending 그룹 헤더 UX 개선

변경 대상:
  frontend/js/sqm-inventory.js  (1239줄, IIFE → Edit 툴 금지, 스크립트 처리)

변경 내용 4가지:
  ① 기본 모드 'lot' → 'date' (도착일별이 기본)
  ② 버튼 순서/라벨 변경:
       LOT별·컨테이너별·날짜별
     → 📅 도착일별 / 📦 컨테이너별 / 🔢 LOT별
  ③a defaultDate 계산 제거 → arrivalRef 계산으로 교체
  ③b 그룹 헤더 날짜 입력란:
     - 기존: 날짜 자동 세팅 (defaultDate)
     - 변경: 📅 도착일 참조 표시(읽기전용) + 🏭 입고확정일 빈칸(직접 입력 강제)

실행: python scripts/patch_pending_group_ux.py
"""
import pathlib, shutil, datetime

ROOT   = pathlib.Path(__file__).resolve().parent.parent
TARGET = ROOT / "frontend" / "js" / "sqm-inventory.js"
TS     = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def backup(p: pathlib.Path):
    bak = p.with_suffix(p.suffix + f".bak_pendingux_{TS}")
    shutil.copy2(p, bak)
    print(f"  📦 백업: {bak.name}")


def patch(src: str) -> str:
    total_applied = 0

    # ── ① 기본 모드 'lot' → 'date' ──────────────────────────────────
    OLD1 = "  window._pendingViewMode = window._pendingViewMode || 'lot';"
    NEW1 = "  window._pendingViewMode = window._pendingViewMode || 'date';"
    if OLD1 in src:
        src = src.replace(OLD1, NEW1, 1)
        print("  ✅  [①] 기본 모드 'lot' → 'date' 적용")
        total_applied += 1
    else:
        print("  ⚠️  [①] 기본 모드 패턴 미발견")

    # ── ② 버튼 순서/라벨 변경 ──────────────────────────────────────
    OLD2 = (
        "        + _pendingModeBtn('date', '📅 도착일별', mode)\n"
        "        + _pendingModeBtn('container', '📦 컨테이너별', mode)\n"
        "        + _pendingModeBtn('lot', '🔢 LOT별', mode)\n"
    )
    # 이미 ①② 1차 패치에서 적용됐으면 스킵
    if OLD2 in src:
        print("  ℹ️  [②] 버튼 순서/라벨 이미 적용됨 (스킵)")
        total_applied += 1
    else:
        OLD2_orig = (
            "        + _pendingModeBtn('lot', 'LOT별', mode)\n"
            "        + _pendingModeBtn('container', '컨테이너별', mode)\n"
            "        + _pendingModeBtn('date', '날짜별', mode)\n"
        )
        NEW2 = (
            "        + _pendingModeBtn('date', '📅 도착일별', mode)\n"
            "        + _pendingModeBtn('container', '📦 컨테이너별', mode)\n"
            "        + _pendingModeBtn('lot', '🔢 LOT별', mode)\n"
        )
        if OLD2_orig in src:
            src = src.replace(OLD2_orig, NEW2, 1)
            print("  ✅  [②] 버튼 순서/라벨 변경 적용")
            total_applied += 1
        else:
            print("  ⚠️  [②] 버튼 순서 패턴 미발견")

    # ── ③a defaultDate 줄 → arrivalRef 계산으로 교체 ──────────────
    OLD3a = "      var defaultDate = opts.defaultDate ? opts.defaultDate(key, lots, today) : today;\n"
    NEW3a = (
        "      var _arrivals = Array.from(new Set(lots.map(function(r){ return r.arrival_date; }).filter(Boolean))).sort();\n"
        "      var arrivalRef = _arrivals.length ? _arrivals.slice(0, 3).join(', ') : '-';\n"
    )
    if OLD3a in src:
        src = src.replace(OLD3a, NEW3a, 1)
        print("  ✅  [③a] defaultDate → arrivalRef 계산 적용")
        total_applied += 1
    else:
        print("  ⚠️  [③a] defaultDate 패턴 미발견")

    # ── ③b 그룹 헤더: 도착일 참조 + 입고확정일 빈칸 입력란 ─────────
    OLD3b = (
        "        + (summary ? '<span style=\"font-size:11px;color:var(--text-muted)\">' + escapeHtml(summary) + '</span>' : '')\n"
        "        + '<input type=\"date\" id=\"' + inputId + '\" value=\"' + escapeHtml(defaultDate) + '\" max=\"' + today + '\" '\n"
        "        + 'style=\"padding:4px 8px;background:var(--bg,#0f172a);border:1px solid var(--border,#334155);border-radius:4px;color:var(--text);font-size:12px;margin-left:auto\" '\n"
        "        + 'onclick=\"event.stopPropagation()\">'\n"
    )
    NEW3b = (
        "        + (summary ? '<span style=\"font-size:11px;color:var(--text-muted)\">' + escapeHtml(summary) + '</span>' : '')\n"
        "        + '<span style=\"font-size:11px;color:var(--text-muted);margin-left:auto;white-space:nowrap\">📅 도착일: <strong style=\"color:var(--text)\">' + escapeHtml(arrivalRef) + '</strong></span>'\n"
        "        + '<span style=\"font-size:12px;color:var(--text-muted);white-space:nowrap\">🏭 입고확정일:</span>'\n"
        "        + '<input type=\"date\" id=\"' + inputId + '\" value=\"\" max=\"' + today + '\" '\n"
        "        + 'style=\"padding:4px 8px;background:var(--bg,#0f172a);border:1px solid var(--accent,#3b82f6);border-radius:4px;color:var(--text);font-size:12px\" '\n"
        "        + 'onclick=\"event.stopPropagation()\">'\n"
    )
    if OLD3b in src:
        src = src.replace(OLD3b, NEW3b, 1)
        print("  ✅  [③b] 그룹 헤더 도착일 참조 + 입고확정일 빈칸 적용")
        total_applied += 1
    else:
        print("  ⚠️  [③b] 그룹 헤더 패턴 미발견")

    print(f"\n  📊 총 {total_applied}/4 패치 적용")
    return src


def main():
    print("\n=== patch_pending_group_ux.py 시작 ===\n")
    print(f"[{TARGET.name}]")
    src = TARGET.read_text(encoding="utf-8")
    backup(TARGET)
    patched = patch(src)
    if patched != src:
        TARGET.write_text(patched, encoding="utf-8")
        print("  💾  저장 완료")
    else:
        print("  ℹ️   변경 없음")
    print("\n=== 패치 완료 ===")


if __name__ == "__main__":
    main()
