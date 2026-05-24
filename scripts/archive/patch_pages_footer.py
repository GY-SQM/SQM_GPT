"""
patch_pages_footer.py  (v8.6.9)
pages/ 디렉토리 IIFE 파일 4개 — 합계 footer 노란 배경 일괄 패치

대상 (IIFE → Edit툴 금지 → 스크립트 처리):
  1. pages/allocation.js  — _renderAllocFooter  배지 노란 배경
  2. pages/outbound.js    — _renderOutboundFooter 배지 노란 배경
  3. pages/scan.js        — _renderScanFooter   건수 배지만 노란 배경 (성공/실패 컬러 유지)
  4. pages/tonbag.js      — _renderTonbagPageFooter + _renderMoveFooter 노란 배경

실행: python scripts/patch_pages_footer.py
"""
import pathlib, shutil, datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent
JS   = ROOT / "frontend" / "js" / "pages"
TS   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

YELLOW = (
    "display:inline-block;padding:4px 18px;margin-right:10px;"
    "background:#FFD600;border-radius:8px;"
    "font-size:14px;color:#222;font-weight:800;"
    "box-shadow:0 1px 4px rgba(0,0,0,.25);"
)
OLD_BLUE = (
    "display:inline-block;padding:2px 14px;margin-right:8px;"
    "background:rgba(79,195,247,0.13);border-radius:6px;"
    "font-size:12px;color:var(--accent,#4fc3f7);font-weight:700;"
)


def backup(p: pathlib.Path):
    bak = p.with_suffix(p.suffix + f".bak_pgfoot_{TS}")
    shutil.copy2(p, bak)
    print(f"  📦 백업: {bak.name}")


def apply(src: str, old: str, new: str, label: str) -> str:
    if old not in src:
        print(f"  ⚠️  [{label}] 패턴 미발견 — 이미 패치됐거나 코드 변경됨")
        return src
    count = src.count(old)
    result = src.replace(old, new)
    print(f"  ✅  [{label}] {count}곳 적용 완료")
    return result


# ─────────────────────────────────────────────────────────────────
# 1. allocation.js — _renderAllocFooter 배지
# ─────────────────────────────────────────────────────────────────
def patch_allocation(src: str) -> str:
    OLD = (
        "    var s = 'display:inline-block;padding:2px 14px;margin-right:8px;"
        "background:rgba(79,195,247,0.13);border-radius:6px;"
        "font-size:12px;color:var(--accent,#4fc3f7);font-weight:700;';\n"
        "    var totBal  = data.reduce"
    )
    NEW = (
        f"    var s = '{YELLOW}';\n"
        "    var totBal  = data.reduce"
    )
    return apply(src, OLD, NEW, "allocation: _renderAllocFooter 노란배지")


# ─────────────────────────────────────────────────────────────────
# 2. outbound.js — _renderOutboundFooter 배지
# ─────────────────────────────────────────────────────────────────
def patch_outbound(src: str) -> str:
    OLD = (
        "    var s = 'display:inline-block;padding:2px 14px;margin-right:8px;"
        "background:rgba(79,195,247,0.13);border-radius:6px;"
        "font-size:12px;color:var(--accent,#4fc3f7);font-weight:700;';\n"
        "    var total = 0;"
    )
    NEW = (
        f"    var s = '{YELLOW}';\n"
        "    var total = 0;"
    )
    return apply(src, OLD, NEW, "outbound: _renderOutboundFooter 노란배지")


# ─────────────────────────────────────────────────────────────────
# 3. scan.js — _renderScanFooter 건수 배지만 노란색 (성공/실패 컬러 유지)
# ─────────────────────────────────────────────────────────────────
def patch_scan(src: str) -> str:
    OLD = (
        "    var s = 'display:inline-block;padding:2px 14px;margin-right:8px;"
        "background:rgba(79,195,247,0.13);border-radius:6px;"
        "font-size:12px;color:var(--accent,#4fc3f7);font-weight:700;';\n"
        "    var shown = hist.slice(0, 20);"
    )
    NEW = (
        f"    var s = '{YELLOW}';\n"
        "    var shown = hist.slice(0, 20);"
    )
    return apply(src, OLD, NEW, "scan: _renderScanFooter 건수 노란배지")


# ─────────────────────────────────────────────────────────────────
# 4. tonbag.js — _renderTonbagPageFooter + _renderMoveFooter (동일 패턴 2곳)
# ─────────────────────────────────────────────────────────────────
def patch_tonbag(src: str) -> str:
    # 두 함수 모두 동일한 blue style 문자열 → replace_all
    OLD = (
        "    var s = 'display:inline-block;padding:2px 14px;margin-right:8px;"
        "background:rgba(79,195,247,0.13);border-radius:6px;"
        "font-size:12px;color:var(--accent,#4fc3f7);font-weight:700;';"
    )
    NEW = f"    var s = '{YELLOW}';"
    return apply(src, OLD, NEW, "tonbag: _renderTonbagPageFooter + _renderMoveFooter 노란배지")


# ─────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────
def main():
    print("\n=== patch_pages_footer.py 시작 ===\n")

    jobs = [
        (JS / "allocation.js", patch_allocation, "allocation.js"),
        (JS / "outbound.js",   patch_outbound,   "outbound.js"),
        (JS / "scan.js",       patch_scan,        "scan.js"),
        (JS / "tonbag.js",     patch_tonbag,      "tonbag.js"),
    ]

    for path, fn, label in jobs:
        print(f"[{label}]")
        src = path.read_text(encoding="utf-8")
        backup(path)
        patched = fn(src)
        if patched != src:
            path.write_text(patched, encoding="utf-8")
            print(f"  💾  저장 완료\n")
        else:
            print(f"  ℹ️   변경 없음\n")

    print("=== 패치 완료 ===")


if __name__ == "__main__":
    main()
