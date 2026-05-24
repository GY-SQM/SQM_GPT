"""
session_start.py  (v8.6.9)
세션 시작 필수 검사 — SQM 코드베이스 헬스체크

검사 항목:
  1) Python  : backend/ 전체 py_compile (36개)
  2) JS      : frontend/js/ 전체 node --check (50개)
  3) DB WAL  : data/db/*.db-wal 크기 경고 (10MB 초과 시)
  4) 백업파일 : frontend/js/*.bak_* 누적 목록 (정보 표시)
  5) 최종 합산: PASS / FAIL 명확히 출력

실행: python scripts/session_start.py
      python scripts/session_start.py --fast   (변경 파일만, git diff 기준)
"""
from __future__ import annotations
import argparse
import py_compile
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ── 색상 코드 (Windows도 동작하도록 try) ────────────────────────────
try:
    import colorama; colorama.init()
    G  = "\033[92m"; R  = "\033[91m"; Y  = "\033[93m"
    B  = "\033[94m"; W  = "\033[0m";  BOLD = "\033[1m"
except Exception:
    G = R = Y = B = W = BOLD = ""


def _hdr(title: str) -> None:
    print(f"\n{BOLD}{B}{'─'*60}{W}")
    print(f"{BOLD}{B}  {title}{W}")
    print(f"{BOLD}{B}{'─'*60}{W}")


def _ok(msg: str)   -> None: print(f"  {G}✅ {msg}{W}")
def _fail(msg: str) -> None: print(f"  {R}❌ {msg}{W}")
def _warn(msg: str) -> None: print(f"  {Y}⚠️  {msg}{W}")
def _info(msg: str) -> None: print(f"  {B}ℹ️  {msg}{W}")


# ══════════════════════════════════════════════════════════════════════
# 1) Python py_compile
# ══════════════════════════════════════════════════════════════════════
def check_python(fast_files: set[Path] | None = None) -> tuple[int, int, list[str]]:
    """Returns (ok_count, fail_count, error_messages)"""
    # backend/ + scripts/ 만 스캔 (node_modules 등 제외)
    scan_dirs = [ROOT / "backend", ROOT / "scripts"]
    py_files = sorted(
        p for d in scan_dirs if d.exists()
        for p in d.rglob("*.py")
        if "__pycache__" not in p.parts
    )
    if fast_files is not None:
        py_files = [p for p in py_files if p in fast_files]

    ok = fail = 0
    errors: list[str] = []
    for f in py_files:
        try:
            py_compile.compile(str(f), doraise=True)
            ok += 1
        except py_compile.PyCompileError as e:
            fail += 1
            rel = f.relative_to(ROOT)
            errors.append(f"{rel} → {e}")
    return ok, fail, errors


# ══════════════════════════════════════════════════════════════════════
# 2) JS node --check
# ══════════════════════════════════════════════════════════════════════
def _node_check_one(f: Path) -> tuple[bool, str]:
    """node --check 단일 파일. (ok, error_msg) 반환."""
    r = subprocess.run(
        ["node", "--check", str(f)],
        capture_output=True, text=True,
    )
    if r.returncode == 0:
        return True, ""
    return False, f"{f.relative_to(ROOT)}\n    {r.stderr.strip()}"


def check_js(fast_files: set[Path] | None = None) -> tuple[int, int, list[str]]:
    js_dir = ROOT / "frontend" / "js"
    js_files = sorted(
        p for p in js_dir.rglob("*.js")
        if ".bak_" not in p.name
    )
    if fast_files is not None:
        js_files = [p for p in js_files if p in fast_files]

    ok = fail = 0
    errors: list[str] = []
    # 병렬 실행 — node 프로세스를 동시에 띄워 대기 시간 최소화
    with ThreadPoolExecutor(max_workers=12) as ex:
        futures = {ex.submit(_node_check_one, f): f for f in js_files}
        for future in as_completed(futures):
            passed, msg = future.result()
            if passed:
                ok += 1
            else:
                fail += 1
                errors.append(msg)
    errors.sort()  # 파일명순 정렬
    return ok, fail, errors


# ══════════════════════════════════════════════════════════════════════
# 3) DB WAL 크기 경고
# ══════════════════════════════════════════════════════════════════════
def check_wal() -> list[str]:
    warnings: list[str] = []
    db_dir = ROOT / "data" / "db"
    if not db_dir.exists():
        return warnings
    for wal in db_dir.glob("*.db-wal"):
        size_mb = wal.stat().st_size / 1_048_576
        if size_mb > 10:
            warnings.append(f"{wal.name}: {size_mb:.1f} MB (체크포인트 권장)")
    return warnings


# ══════════════════════════════════════════════════════════════════════
# 4) 백업파일 목록 (정보용)
# ══════════════════════════════════════════════════════════════════════
def list_backups() -> list[Path]:
    js_dir = ROOT / "frontend" / "js"
    baks = sorted(js_dir.rglob("*.bak_*"), key=lambda p: p.stat().st_mtime, reverse=True)
    return baks[:10]  # 최신 10개만


# ══════════════════════════════════════════════════════════════════════
# 5) git 상태 요약
# ══════════════════════════════════════════════════════════════════════
def git_status() -> tuple[str, set[Path]]:
    """Returns (summary_text, changed_py_js_paths)"""
    r = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        capture_output=True, text=True, cwd=ROOT,
    )
    if r.returncode != 0:
        return "git 상태 조회 실패 (git 없음?)", set()
    lines = [l.strip() for l in r.stdout.strip().splitlines() if l.strip()]
    staged = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True, text=True, cwd=ROOT,
    )
    lines += [l.strip() for l in staged.stdout.strip().splitlines() if l.strip()]
    changed = set(ROOT / l for l in lines if l)
    summary = f"변경 파일 {len(lines)}개 (미커밋)" if lines else "미커밋 변경 없음"
    return summary, changed


# ══════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════
def main() -> None:
    parser = argparse.ArgumentParser(description="SQM 세션 시작 헬스체크")
    parser.add_argument("--fast", action="store_true",
                        help="git diff 기준 변경 파일만 검사 (빠름)")
    args = parser.parse_args()

    t0 = time.time()
    print(f"\n{BOLD}{'═'*60}")
    print(f"  SQM v8.6.9  세션 시작 검사  {'[--fast 모드]' if args.fast else '[전체 모드]'}")
    print(f"{'═'*60}{W}")

    fast_files: set[Path] | None = None
    git_sum, changed = git_status()

    if args.fast:
        fast_files = changed
        _info(f"git: {git_sum}")
        if not fast_files:
            _ok("변경 파일 없음 — 검사 생략")
            print(f"\n{BOLD}{G}  ✅ PASS (변경 없음){W}  ({time.time()-t0:.1f}s)\n")
            return

    # ── Python ──
    _hdr("1/4  Python py_compile")
    py_ok, py_fail, py_errors = check_python(fast_files)
    total_py = py_ok + py_fail
    if py_fail == 0:
        _ok(f"{py_ok}/{total_py} 전체 통과")
    else:
        _fail(f"{py_fail}/{total_py} 실패")
        for e in py_errors:
            print(f"      {R}{e}{W}")

    # ── JS ──
    _hdr("2/4  JavaScript node --check")
    js_ok, js_fail, js_errors = check_js(fast_files)
    total_js = js_ok + js_fail
    if js_fail == 0:
        _ok(f"{js_ok}/{total_js} 전체 통과")
    else:
        _fail(f"{js_fail}/{total_js} 실패")
        for e in js_errors:
            print(f"      {R}{e}{W}")

    # ── DB WAL ──
    _hdr("3/4  DB WAL 크기 확인")
    wal_warns = check_wal()
    if not wal_warns:
        _ok("WAL 크기 정상 (10MB 미만)")
    else:
        for w in wal_warns:
            _warn(w)

    # ── 백업파일 ──
    _hdr("4/4  패치 백업 파일 (정보용)")
    baks = list_backups()
    if not baks:
        _info("백업 파일 없음")
    else:
        _info(f"최신 {len(baks)}개 (삭제 불필요 — 참고용)")
        for b in baks[:5]:
            print(f"      {Y}{b.relative_to(ROOT)}{W}")
        if len(baks) > 5:
            print(f"      ... 외 {len(baks)-5}개")

    # ── git 요약 ──
    _hdr("git 상태")
    if changed:
        _warn(git_sum)
        for p in sorted(changed)[:10]:
            try:
                print(f"      {Y}{p.relative_to(ROOT)}{W}")
            except ValueError:
                print(f"      {Y}{p}{W}")
        if len(changed) > 10:
            print(f"      ... 외 {len(changed)-10}개")
        _warn("→ Windows CMD에서 git commit 권장 (Rule 6)")
    else:
        _ok(git_sum)

    # ── 최종 결과 ──
    elapsed = time.time() - t0
    print(f"\n{BOLD}{'═'*60}{W}")
    total_fail = py_fail + js_fail
    if total_fail == 0:
        print(f"{BOLD}{G}  ✅ PASS — Python {py_ok}/{total_py}  JS {js_ok}/{total_js}{W}  ({elapsed:.1f}s)")
    else:
        print(f"{BOLD}{R}  ❌ FAIL — Python {py_fail}개 오류 / JS {js_fail}개 오류{W}  ({elapsed:.1f}s)")
        print(f"{R}  ⚑  위 오류를 먼저 수정한 뒤 작업을 시작하세요.{W}")
    print(f"{BOLD}{'═'*60}{W}\n")

    sys.exit(0 if total_fail == 0 else 1)


if __name__ == "__main__":
    main()
