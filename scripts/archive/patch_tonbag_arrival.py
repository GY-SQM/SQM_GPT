"""
patch_tonbag_arrival.py  (v8.6.9)
tonbag 리스트 모달에 도착일(arrival_date) 컬럼 추가

변경 대상:
  frontend/js/sqm-listview.js — TONBAG_COLS 배열

변경 내용:
  inbound_date 항목 바로 뒤에 arrival_date 컬럼 정의 삽입

실행: python scripts/patch_tonbag_arrival.py
"""
import pathlib, shutil, datetime

ROOT   = pathlib.Path(__file__).resolve().parent.parent
TARGET = ROOT / "frontend" / "js" / "sqm-listview.js"
TS     = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def backup(p: pathlib.Path):
    bak = p.with_suffix(p.suffix + f".bak_arrival_{TS}")
    shutil.copy2(p, bak)
    print(f"  📦 백업: {bak.name}")


def patch(src: str) -> str:
    OLD = (
        "    { k: 'inbound_date', h: '입고일',      w: 100, align: 'center' },\n"
        "    { k: 'sold_to',      h: '출고대상',    w: 130, align: 'center' },\n"
    )
    NEW = (
        "    { k: 'inbound_date', h: '입고일',      w: 100, align: 'center' },\n"
        "    { k: 'arrival_date', h: '도착일',      w: 100, align: 'center' },\n"
        "    { k: 'sold_to',      h: '출고대상',    w: 130, align: 'center' },\n"
    )
    if OLD not in src:
        print("  ⚠️  패턴 미발견 — 이미 패치됐거나 코드 변경됨")
        return src
    result = src.replace(OLD, NEW, 1)
    print("  ✅  [sqm-listview TONBAG_COLS: 도착일 컬럼 추가] 적용 완료")
    return result


def main():
    print("\n=== patch_tonbag_arrival.py 시작 ===\n")
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
