"""
patch_sample_label.py  (v8.6.9)
톤백 리스트 모달에서 sub_lt=0 (샘플) 행 제품명 뒤에 " (Sample)" 표기 추가

변경 대상:
  frontend/js/sqm-listview.js — _renderTable() 내 tbody 렌더링 부분

변경 내용:
  product 컬럼 렌더 시 r.is_sample=1 또는 r.sub_lt=0 이면
  제품명 값에 ' (Sample)' 접미사 추가 후 _formatCell 호출

실행: python scripts/patch_sample_label.py
"""
import pathlib, shutil, datetime

ROOT   = pathlib.Path(__file__).resolve().parent.parent
TARGET = ROOT / "frontend" / "js" / "sqm-listview.js"
TS     = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def backup(p: pathlib.Path):
    bak = p.with_suffix(p.suffix + f".bak_smplabel_{TS}")
    shutil.copy2(p, bak)
    print(f"  📦 백업: {bak.name}")


def patch(src: str) -> str:
    OLD = (
        "      var tds = cols.map(function(c) {\n"
        "        var v = _formatCell(r[c.k], c);\n"
    )
    NEW = (
        "      var tds = cols.map(function(c) {\n"
        "        var _cv = r[c.k];\n"
        "        /* v8.6.9: sub_lt=0(샘플) 행 — 제품명 뒤에 \" (Sample)\" 표기 */\n"
        "        if (c.k === 'product' && (r.is_sample || Number(r.sub_lt) === 0)) {\n"
        "          _cv = (_cv || '') + ' (Sample)';\n"
        "        }\n"
        "        var v = _formatCell(_cv, c);\n"
    )
    if OLD not in src:
        print("  ⚠️  패턴 미발견 — 이미 패치됐거나 코드 변경됨")
        return src
    result = src.replace(OLD, NEW, 1)
    print("  ✅  [sqm-listview: 샘플 행 제품명 (Sample) 표기] 적용 완료")
    return result


def main():
    print("\n=== patch_sample_label.py 시작 ===\n")
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
