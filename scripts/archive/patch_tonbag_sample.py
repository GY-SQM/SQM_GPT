"""
patch_tonbag_sample.py  (v8.6.9)
actions2.py 톤백 리스트에 is_sample(샘플여부) 컬럼 추가 패치

변경 대상:
  1. _tonbag_sql()          — SELECT에 t.is_sample 추가 (index 16)
  2. _append_tonbag_rack_candidates() — is_sample을 출력 tuple에 포함
  3. _TONBAG_LIST_JSON_HEADERS — "is_sample" 추가 (index 16)
  4. _build_tonbag_workbook() — Excel 헤더/데이터/열너비에 "샘플여부" 추가

효과:
  - 화면 톤백 리스트 footer: 🧱 일반 Xoo개 + 🧪 샘플 Yy개 분리 표시
  - Excel 내보내기: 마지막 열에 "샘플여부"(샘플/일반) 컬럼 추가

실행: python scripts/patch_tonbag_sample.py
"""
import pathlib, shutil, datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent
TARGET = ROOT / "backend" / "api" / "actions2.py"
TS = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def backup(p: pathlib.Path):
    bak = p.with_suffix(p.suffix + f".bak_tbsample_{TS}")
    shutil.copy2(p, bak)
    print(f"  📦 백업: {bak.name}")


def apply(src: str, old: str, new: str, label: str) -> str:
    if old not in src:
        print(f"  ⚠️  [{label}] 패턴 미발견 — 이미 패치됐거나 코드 변경됨")
        return src
    result = src.replace(old, new, 1)
    print(f"  ✅  [{label}] 적용 완료")
    return result


# ─────────────────────────────────────────────────────────────────
# 1. _tonbag_sql() — SELECT 마지막에 t.is_sample 추가
# ─────────────────────────────────────────────────────────────────
def patch_sql(src: str) -> str:
    OLD = (
        "               i.warehouse,\n"
        "               t.lot_no\n"
        "        FROM inventory_tonbag t\n"
    )
    NEW = (
        "               i.warehouse,\n"
        "               t.lot_no, t.is_sample\n"
        "        FROM inventory_tonbag t\n"
    )
    return apply(src, OLD, NEW, "_tonbag_sql: t.is_sample 추가")


# ─────────────────────────────────────────────────────────────────
# 2. _append_tonbag_rack_candidates() — is_sample(index 16) 보존
#    원본: row[:10] + [rack_candidate] + row[10:15]
#    변경: row[:10] + [rack_candidate] + row[10:15] + [is_sample]
# ─────────────────────────────────────────────────────────────────
def patch_rack_candidates(src: str) -> str:
    OLD = (
        "        # Drop hidden lot_no and insert candidate after actual location.\n"
        "        out.append(tuple(row[:10] + [rack_candidate] + row[10:15]))\n"
    )
    NEW = (
        "        # Drop hidden lot_no and insert candidate after actual location.\n"
        "        # is_sample at index 16 (after lot_no at 15) — preserve it.\n"
        "        is_sample = row[16] if len(row) > 16 else 0\n"
        "        out.append(tuple(row[:10] + [rack_candidate] + row[10:15] + [is_sample]))\n"
    )
    return apply(src, OLD, NEW, "_append_tonbag_rack_candidates: is_sample 보존")


# ─────────────────────────────────────────────────────────────────
# 3. _TONBAG_LIST_JSON_HEADERS — "is_sample" 추가
# ─────────────────────────────────────────────────────────────────
def patch_headers(src: str) -> str:
    OLD = (
        '_TONBAG_LIST_JSON_HEADERS = [\n'
        '    "sap_no", "bl_no", "container_no", "product",\n'
        '    "tonbag_uid", "sub_lt", "tonbag_no", "weight_kg",\n'
        '    "status", "location", "rack_location_candidate", "inbound_date", "sold_to",\n'
        '    "sale_ref", "remarks", "warehouse",\n'
        ']'
    )
    NEW = (
        '_TONBAG_LIST_JSON_HEADERS = [\n'
        '    "sap_no", "bl_no", "container_no", "product",\n'
        '    "tonbag_uid", "sub_lt", "tonbag_no", "weight_kg",\n'
        '    "status", "location", "rack_location_candidate", "inbound_date", "sold_to",\n'
        '    "sale_ref", "remarks", "warehouse", "is_sample",\n'
        ']'
    )
    return apply(src, OLD, NEW, "_TONBAG_LIST_JSON_HEADERS: is_sample 추가")


# ─────────────────────────────────────────────────────────────────
# 4-A. _build_tonbag_workbook() — Excel 헤더에 "샘플여부" 추가
# ─────────────────────────────────────────────────────────────────
def patch_excel_headers(src: str) -> str:
    OLD = (
        '    headers = [\n'
        '        "SAP NO", "BL NO", "Container", "제품명",\n'
        '        "톤백 UID", "Sub LT", "톤백 번호", "중량(kg)",\n'
        '        "상태", "실제 위치", "랙 위치 후보", "입고일", "출고대상", "Sale Ref", "비고", "창고"\n'
        '    ]'
    )
    NEW = (
        '    headers = [\n'
        '        "SAP NO", "BL NO", "Container", "제품명",\n'
        '        "톤백 UID", "Sub LT", "톤백 번호", "중량(kg)",\n'
        '        "상태", "실제 위치", "랙 위치 후보", "입고일", "출고대상", "Sale Ref", "비고", "창고", "샘플여부"\n'
        '    ]'
    )
    return apply(src, OLD, NEW, "_build_tonbag_workbook: Excel 헤더 샘플여부 추가")


# ─────────────────────────────────────────────────────────────────
# 4-B. _build_tonbag_workbook() — 데이터 행 추가 시 is_sample → 샘플/일반 변환
# ─────────────────────────────────────────────────────────────────
def patch_excel_rows(src: str) -> str:
    OLD = (
        '    for r in rows:\n'
        '        ws.append(list(r))\n'
        '        status = r[8] or ""\n'
    )
    NEW = (
        '    for r in rows:\n'
        '        row_data = list(r)\n'
        '        if len(row_data) > 16:\n'
        '            row_data[16] = \'샘플\' if row_data[16] else \'일반\'\n'
        '        ws.append(row_data)\n'
        '        status = r[8] or ""\n'
    )
    return apply(src, OLD, NEW, "_build_tonbag_workbook: 데이터 행 샘플여부 변환")


# ─────────────────────────────────────────────────────────────────
# 4-C. _build_tonbag_workbook() — 열 너비 배열에 샘플여부 너비 추가
# ─────────────────────────────────────────────────────────────────
def patch_excel_widths(src: str) -> str:
    OLD = (
        '    # 열 너비: SAP,BL,Container,제품명,UID,SubLT,#,중량,상태,실제위치,후보,입고일,출고,SaleRef,비고,창고\n'
        '    widths = [12, 14, 16, 22, 20, 8, 10, 12, 12, 12, 14, 12, 14, 14, 20, 10]'
    )
    NEW = (
        '    # 열 너비: SAP,BL,Container,제품명,UID,SubLT,#,중량,상태,실제위치,후보,입고일,출고,SaleRef,비고,창고,샘플여부\n'
        '    widths = [12, 14, 16, 22, 20, 8, 10, 12, 12, 12, 14, 12, 14, 14, 20, 10, 8]'
    )
    return apply(src, OLD, NEW, "_build_tonbag_workbook: 열 너비 샘플여부 추가")


# ─────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────
def main():
    print("\n=== patch_tonbag_sample.py 시작 ===\n")
    print(f"[{TARGET.name}]")

    src = TARGET.read_text(encoding="utf-8")
    backup(TARGET)

    src = patch_sql(src)
    src = patch_rack_candidates(src)
    src = patch_headers(src)
    src = patch_excel_headers(src)
    src = patch_excel_rows(src)
    src = patch_excel_widths(src)

    TARGET.write_text(src, encoding="utf-8")
    print(f"\n  💾  저장 완료")
    print("\n=== 패치 완료 ===")


if __name__ == "__main__":
    main()
