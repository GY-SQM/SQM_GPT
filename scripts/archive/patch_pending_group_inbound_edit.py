"""
patch_pending_group_inbound_edit.py  (v8.6.9)
도착일별/컨테이너별 그룹 내부 행에 🏭 입고일 인라인 편집 추가

변경 대상:
  frontend/js/sqm-inventory.js  (1239줄, IIFE → Edit 툴 금지)

변경 내용 2가지:
  ① 그룹 내부 테이블 헤더: Arrival 뒤에 🏭 입고일 th 삽입
  ② 그룹 내부 테이블 행: arrival_date td 뒤에
     pendingEditInboundDate() 인라인 편집 버튼 td 삽입
     (LOT별 모드와 동일한 방식)

실행: python scripts/patch_pending_group_inbound_edit.py
"""
import pathlib, shutil, datetime

ROOT   = pathlib.Path(__file__).resolve().parent.parent
TARGET = ROOT / "frontend" / "js" / "sqm-inventory.js"
TS     = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def backup(p: pathlib.Path):
    bak = p.with_suffix(p.suffix + f".bak_grpedit_{TS}")
    shutil.copy2(p, bak)
    print(f"  📦 백업: {bak.name}")


def patch(src: str) -> str:
    total_applied = 0

    # ── ① 그룹 내부 테이블 헤더에 🏭 입고일 th 추가 ─────────────────
    OLD1 = (
        "        + '<th style=\"color:var(--text-muted);text-align:center;width:36px\">#</th>"
        "<th>LOT</th><th>Product</th><th>Qty</th><th>BL No</th>"
        "<th>Container</th><th>Vessel</th><th>Arrival</th>"
        "<th style=\"width:50px\">⚙️</th>'\n"
    )
    NEW1 = (
        "        + '<th style=\"color:var(--text-muted);text-align:center;width:36px\">#</th>"
        "<th>LOT</th><th>Product</th><th>Qty</th><th>BL No</th>"
        "<th>Container</th><th>Vessel</th><th>Arrival</th>"
        "<th title=\"실제 창고 반입 예정일 (클릭하여 편집)\">🏭 입고일</th>"
        "<th style=\"width:50px\">⚙️</th>'\n"
    )
    if OLD1 in src:
        src = src.replace(OLD1, NEW1, 1)
        print("  ✅  [①] 그룹 헤더 🏭 입고일 th 추가")
        total_applied += 1
    else:
        print("  ⚠️  [①] 헤더 패턴 미발견")

    # ── ② 그룹 내부 행: arrival_date td 뒤에 인라인 편집 td 삽입 ─────
    OLD2 = (
        "          + '<td class=\"mono-cell\">' + escapeHtml(r.arrival_date||'-') + '</td>'\n"
        "          + '<td style=\"text-align:center\"><button class=\"btn btn-ghost\" style=\"padding:1px 8px;font-size:12px\" '\n"
        "          + 'onclick=\"window.showPendingActionMenu(event,\\'' + escapeHtml(r.lot_no||'') + '\\')\">⋯</button></td>'\n"
    )
    NEW2 = (
        "          + '<td class=\"mono-cell\">' + escapeHtml(r.arrival_date||'-') + '</td>'\n"
        "          + '<td class=\"mono-cell\" style=\"padding:2px 4px\">'\n"
        "          + '<button class=\"btn btn-ghost btn-xs\" style=\"font-size:12px;padding:2px 8px;width:100%;text-align:left;'\n"
        "          + ((r.inbound_date||'').slice(0,10) ? 'color:#22c55e;font-weight:600' : 'color:var(--text-muted)') + '\" '\n"
        "          + 'onclick=\"window.pendingEditInboundDate(this,\\'' + escapeHtml(r.lot_no||'') + '\\',\\'' + escapeHtml((r.inbound_date||'').slice(0,10)) + '\\')\" '\n"
        "          + 'title=\"실제 입고일 편집 (클릭)\">' + ((r.inbound_date||'').slice(0,10) || '📅 미지정') + '</button>'\n"
        "          + '</td>'\n"
        "          + '<td style=\"text-align:center\"><button class=\"btn btn-ghost\" style=\"padding:1px 8px;font-size:12px\" '\n"
        "          + 'onclick=\"window.showPendingActionMenu(event,\\'' + escapeHtml(r.lot_no||'') + '\\')\">⋯</button></td>'\n"
    )
    if OLD2 in src:
        src = src.replace(OLD2, NEW2, 1)
        print("  ✅  [②] 그룹 행 🏭 입고일 인라인 편집 td 삽입")
        total_applied += 1
    else:
        print("  ⚠️  [②] 행 패턴 미발견")

    print(f"\n  📊 총 {total_applied}/2 패치 적용")
    return src


def main():
    print("\n=== patch_pending_group_inbound_edit.py 시작 ===\n")
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
