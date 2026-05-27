"""
make_v870_clean.py
------------------
v869_clean에서 실제 실행에 필요한 파일만 추려
D:\\program\\SQM_inventory\\sqm_v870_clean 을 새로 만듭니다.

실행: python make_v870_clean.py
"""

import os
import shutil
import sys

SRC  = r"D:\program\SQM_inventory\sqm_v869_clean"
DEST = r"D:\program\SQM_inventory\sqm_v870_clean"

# ── 복사할 디렉토리 (하위 전체, 단 제외 패턴 적용) ─────────────────────────
COPY_DIRS = [
    "backend",
    "frontend",
    "features",
    "core",
    "utils",
    "engine_modules",
    "templates",
    "resources",
    "data",
    "tests",
    "scripts",       # archive/ 제외
    "docs",          # audit/report/work_order 제외 (선택)
]

# ── 복사할 루트 파일 ────────────────────────────────────────────────────────
COPY_ROOT_FILES = [
    "main_webview.py",
    "config.py",
    "config_logging.py",
    "config_sql.py",
    "version.py",
    "theme_aware.py",
    "theme_preference.json",
    "settings.ini",
    "settings.ini.template",
    "requirements.txt",
    "requirements_webview.txt",
    "pytest.ini",
    "playwright.config.js",
    "package.json",
    "package-lock.json",
    "run.bat",
    "run_v869_clean.bat",
    "실행.bat",
    "run_master.bat",
    "run_master_api.bat",
    "CLAUDE.md",
    "HOW_TO_RUN.md",
    "RELEASE_NOTES.md",
]

# ── 제외 패턴 ──────────────────────────────────────────────────────────────
SKIP_DIRS = {
    "__pycache__", ".git", ".claude",
    "node_modules", "build", "dist", "output",
    "logs", "temp", "exports", "backup",
    "alloc_test_files", "alloc_test_woo_jakarta_real",
    "REPORTS", "_archive", "archive",   # scripts/archive 제외
    "del", "fixes", "analysis", "tools",
    "installer", "gui_app_modular", "parsers",
}

SKIP_EXTENSIONS = {
    ".bak", ".log", ".tmp", ".err", ".out",
    ".zip", ".spec",
}

SKIP_FILENAME_PREFIXES = ("patch_A", "patch_revert", "patch_rollback",
                           "patch_nocache", "patch_version_bump",
                           "patch_add_revert", "_add_hapag",
                           "auto_hotfix", "check_lots", "debug_gemini",
                           "gemini_cli", "create_test_db",
                           "git_", "push_", "build_v8",
                           "fix_explorer", "GIT_DEPLOY",
                           "smoke_and_pytest", "run_integration",
                           "ziBVtP",)

SKIP_EXACT_FILES = {
    "sqm_inventory.db",            # 루트 잔재
    "test_write_check.tmp",
    "FETCH_HEAD",
    "ONEY",
    "0.5", "7588",
    "window_state.json",
    "sqm_debug.log",
}


def should_skip_dir(dirname):
    return dirname in SKIP_DIRS or dirname.startswith(".")


def should_skip_file(filename):
    if filename in SKIP_EXACT_FILES:
        return True
    _, ext = os.path.splitext(filename)
    if ext in SKIP_EXTENSIONS:
        return True
    for prefix in SKIP_FILENAME_PREFIXES:
        if filename.startswith(prefix):
            return True
    # 한글/특수문자 xlsx 테스트 파일
    if filename.startswith("SMQ ") or filename.startswith("SQM_Upload") or \
       filename.startswith("위치재고") or filename.startswith("입고_4종"):
        return True
    # 루트 patch 파일
    if filename.startswith("patch_") and filename.endswith(".py"):
        return True
    return False


def copy_dir(src_dir, dest_dir):
    os.makedirs(dest_dir, exist_ok=True)
    copied = 0
    skipped = 0
    for root, dirs, files in os.walk(src_dir):
        # 제외 디렉토리 필터
        dirs[:] = [d for d in dirs if not should_skip_dir(d)]

        rel = os.path.relpath(root, src_dir)
        target_root = os.path.join(dest_dir, rel)
        os.makedirs(target_root, exist_ok=True)

        for fname in files:
            if should_skip_file(fname):
                skipped += 1
                continue
            src_f  = os.path.join(root, fname)
            dest_f = os.path.join(target_root, fname)
            shutil.copy2(src_f, dest_f)
            copied += 1

    return copied, skipped


def main():
    if os.path.exists(DEST):
        ans = input(f"\n⚠️  {DEST} 이미 존재합니다. 덮어쓸까요? (y/n): ").strip().lower()
        if ans != "y":
            print("취소")
            sys.exit(0)
        shutil.rmtree(DEST)
        print("기존 폴더 삭제 완료")

    print(f"\n{'='*55}")
    print(f"  SQM v870_clean 생성 시작")
    print(f"  SRC : {SRC}")
    print(f"  DEST: {DEST}")
    print(f"{'='*55}\n")

    total_copied = 0
    total_skipped = 0

    # 디렉토리 복사
    for d in COPY_DIRS:
        src_d  = os.path.join(SRC, d)
        dest_d = os.path.join(DEST, d)
        if not os.path.isdir(src_d):
            print(f"  [SKIP] {d}/ — 없음")
            continue
        c, s = copy_dir(src_d, dest_d)
        print(f"  ✅ {d}/  → {c}개 복사, {s}개 제외")
        total_copied  += c
        total_skipped += s

    # 루트 파일 복사
    print()
    for fname in COPY_ROOT_FILES:
        src_f  = os.path.join(SRC, fname)
        dest_f = os.path.join(DEST, fname)
        if os.path.isfile(src_f):
            shutil.copy2(src_f, dest_f)
            print(f"  ✅ {fname}")
            total_copied += 1
        else:
            print(f"  [SKIP] {fname} — 없음")

    # data/db — 메인 DB만 (bak 제외는 copy_dir에서 이미 처리됨)
    print()
    print(f"{'='*55}")
    print(f"  완료: 총 {total_copied}개 복사 / {total_skipped}개 제외")

    # 결과 크기
    total_size = 0
    for root, dirs, files in os.walk(DEST):
        for f in files:
            total_size += os.path.getsize(os.path.join(root, f))
    print(f"  폴더 크기: {total_size / 1024 / 1024:.1f} MB")
    print(f"{'='*55}")
    print(f"\n  📁 {DEST}")
    print("  완성! 바로 실행 가능합니다.\n")


if __name__ == "__main__":
    main()
