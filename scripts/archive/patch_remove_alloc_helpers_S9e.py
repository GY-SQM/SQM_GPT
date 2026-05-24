# -*- coding: utf-8 -*-
"""
Phase B - Slice S9e: alloc* 헬퍼 그룹 중복 제거 (최대 규모)

대상: sqm-inline.js line 208-765 (558줄)
- ALLOC_EDITABLE_FIELDS 변수 + 주석 (line 208-211)
- window._allocViewMode 변수 (line 212)
- 내부 헬퍼 (_allocModeBtn, _allocKeyContainer, _allocKeyDate,
              _renderAllocGroupRows, _renderAllocLotTableOnly,
              _renderAllocTable, _allocBulkAction)
- window 노출 16개 (allocUploadExcel, allocApplyApproved, ...,
                    cancelAllocation, toggleAllocDetail, etc.)

전제: 모든 함수가 sqm-allocation.js에 동일/유사 정의 + window 노출
- 내부 헬퍼 _renderAllocTable (sqm-allocation.js:138)
- 내부 헬퍼 _allocBulkAction (sqm-allocation.js:409)
- window 노출 20개+ (line 258-615 영역)

ALLOC_EDITABLE_FIELDS는 line 585 (allocEditCell 안)에서만 사용 → 같이 제거 OK

사용:
    python scripts/patch_remove_alloc_helpers_S9e.py --dry-run
    python scripts/patch_remove_alloc_helpers_S9e.py
    python scripts/patch_remove_alloc_helpers_S9e.py --rollback
"""

import argparse
import sys
import shutil
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent.parent
INLINE = ROOT / 'frontend' / 'js' / 'sqm-inline.js'
ALLOC = ROOT / 'frontend' / 'js' / 'sqm-allocation.js'
SLICE_ID = 'S9e'

START_LINE = 208
END_LINE = 765
EXPECTED_DELETE_COUNT = END_LINE - START_LINE + 1  # 558줄

SIG_START_PREFIX = '  /* [Sprint 1-1-D]'
SIG_END_LINE = '  };'  # cancelAllocation 닫힘
SIG_OUTER_IIFE_CLOSE = '})();'

# sqm-allocation.js 안전망 — 핵심 함수들
ALLOC_REQUIRED = [
    '  function loadAllocationPage() {',
    '  function _renderAllocTable() {',
    '  function _allocBulkAction(opts) {',
    '  window.allocUploadExcel = function() {',
    '  window.allocCancelSelected = function() {',
    '  window.toggleAllocDetail = function(lotNo) {',
    '  window.cancelAllocation = function(lot) {',
    '  window.loadAllocationPage = loadAllocationPage;',
]


def log(msg, level='INFO'):
    icons = {'INFO': 'ℹ', 'OK': '✓', 'WARN': '⚠', 'ERR': '✗', 'DRY': '🧪'}
    print(f"{icons.get(level, '·')} [{level}] {msg}")


def read_lines(path):
    with path.open('r', encoding='utf-8', newline='') as f:
        return f.readlines()


def write_lines(path, lines):
    with path.open('w', encoding='utf-8', newline='') as f:
        f.writelines(lines)


def backup(path, slice_id):
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    bak = path.with_suffix(path.suffix + f'.bak_{slice_id}_{ts}')
    shutil.copy2(path, bak)
    return bak


def verify_safety_net():
    if not ALLOC.exists():
        return [f"안전망 없음: {ALLOC}"]
    text = ALLOC.read_text(encoding='utf-8')
    errors = []
    for sig in ALLOC_REQUIRED:
        if sig not in text:
            errors.append(f"sqm-allocation.js에 시그니처 없음: {sig!r}")
    return errors


def verify_inline(lines):
    errors = []
    if len(lines) < 2500:
        errors.append(f"줄수 너무 적음: {len(lines)}")
        return errors

    lstart = lines[START_LINE - 1].rstrip()
    if not lstart.startswith(SIG_START_PREFIX):
        errors.append(f"line {START_LINE} 시작 시그니처 불일치: got {lstart[:60]!r}")

    lend = lines[END_LINE - 1].rstrip()
    if lend != SIG_END_LINE.rstrip():
        errors.append(f"line {END_LINE} 끝 시그니처 불일치: got {lend[:60]!r}")

    last = lines[-1].rstrip()
    if last != SIG_OUTER_IIFE_CLOSE:
        errors.append(f"마지막 줄 outer IIFE 손상: got {last!r}")

    return errors


def already_removed(lines):
    text = ''.join(lines[:300])
    return 'ALLOC_EDITABLE_FIELDS' not in text


def rollback():
    baks = sorted(INLINE.parent.glob(f'{INLINE.name}.bak_{SLICE_ID}_*'), reverse=True)
    if not baks:
        log(f'{SLICE_ID} 백업 없음', 'ERR')
        return False
    shutil.copy2(baks[0], INLINE)
    log(f'복원: {INLINE.name}', 'OK')
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--rollback', action='store_true')
    args = parser.parse_args()

    if args.rollback:
        log(f'=== Rollback {SLICE_ID} ===')
        return 0 if rollback() else 1

    mode = 'DRY-RUN' if args.dry_run else 'EXECUTE'
    log(f'=== S9e alloc* 헬퍼 중복 제거 ({mode}) ===')

    sn_errors = verify_safety_net()
    if sn_errors:
        for e in sn_errors:
            log(f'  - {e}', 'ERR')
        return 1
    log('sqm-allocation.js 안전망 통과 (8개 시그니처)', 'OK')

    inline_lines = read_lines(INLINE)
    log(f'입력 sqm-inline.js: {len(inline_lines)} 줄')

    if already_removed(inline_lines):
        log('이미 제거됨', 'WARN')
        return 0

    errors = verify_inline(inline_lines)
    if errors:
        for e in errors:
            log(f'  - {e}', 'ERR')
        return 1
    log(f'사전 검증 통과 (line {START_LINE}-{END_LINE})', 'OK')

    new_lines = inline_lines[:START_LINE - 1] + inline_lines[END_LINE:]
    expected = len(inline_lines) - EXPECTED_DELETE_COUNT
    if len(new_lines) != expected:
        log(f'줄수 오류: {expected} vs {len(new_lines)}', 'ERR')
        return 1
    if new_lines[-1].rstrip() != SIG_OUTER_IIFE_CLOSE:
        log('사후 outer IIFE 손상', 'ERR')
        return 1
    log(f'사후 검증 통과 ({len(inline_lines)} → {expected})', 'OK')

    if args.dry_run:
        log(f'DRY-RUN: {len(inline_lines)} → {expected}, 삭제 {EXPECTED_DELETE_COUNT}줄', 'DRY')
        return 0

    bak = backup(INLINE, SLICE_ID)
    log(f'백업: {bak.name}', 'OK')

    write_lines(INLINE, new_lines)
    log(f'수정: {INLINE.name} ({len(new_lines)}줄)', 'OK')

    final = read_lines(INLINE)
    if final[-1].rstrip() != SIG_OUTER_IIFE_CLOSE:
        log('최종 outer IIFE 손상', 'ERR')
        return 1
    log('=== 완료 ===')
    return 0


if __name__ == '__main__':
    sys.exit(main())
