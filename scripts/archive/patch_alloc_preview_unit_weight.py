# -*- coding: utf-8 -*-
"""
patch_alloc_preview_unit_weight.py — v8.6.5

배정 다이얼로그 미리보기에 1000kg 톤백 인식 추가.

변경 내용:
  1. _allocation_tonbag_sample_counts(rows, db=None) — 시그니처 변경, 3-tuple 반환
     (tonbag_500, tonbag_1000, sample_count)
  2. LOT별 unit_weight 캐시로 1회만 DB 조회
  3. _format_tonbag_summary() 헬퍼 추가 — "500kg N개, 1000kg M개" 분리 표시
  4. 4개 호출부에 self.engine.db 전달, 표시 문자열 갱신
  5. 업로드 현황 팝업 — prev_tb 산정 시 LOT 기반 unit_weight 적용

Rule 5 준수: allocation_dialog.py = 1621줄 → Edit 툴 금지, 스크립트로 처리.
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "gui_app_modular" / "dialogs" / "allocation_dialog.py"


# ───────────────────────────────────────────────────────────────────────
# 패치 정의 (정확한 OLD 문자열 → NEW 문자열)
# ───────────────────────────────────────────────────────────────────────

OLD_FUNC = '''def _allocation_tonbag_sample_counts(rows: list) -> tuple:
    """Allocation 행에서 500kg 기준 톤백 표시 개수와 샘플(1kg) 개수 계산. (tonbag_500, sample_count)

    v8.6.1 설계 원칙:
    - 이 함수는 UI 표시 전용 (미리보기 카운트)이며 실제 DB 저장값과 무관.
    - lot_no가 없어 get_tonbag_unit_weight() DB 조회 불가 → 500kg 표시 기준 유지.
    - 실제 톤백 무게는 입고 시 (net_weight - 1kg) / mxbg_pallet 공식으로 결정.
    """
    tonbag_500 = 0
    sample_count = 0
    for r in rows:
        qty = 0.0
        if hasattr(r, 'get'):
            qty = float(r.get('qty_mt') or 0)
        else:
            qty = float(getattr(r, 'qty_mt', 0) or 0)
        if qty >= SAMPLE_MT_THRESHOLD:
            # 표시 전용: 500kg 기준 개수. 실제 톤백 단가는 DB inventory_tonbag.weight 참조.
            tonbag_500 += int(round(qty * 1000 / DEFAULT_TONBAG_WEIGHT))
        else:
            sample_count += 1
    return tonbag_500, sample_count'''

NEW_FUNC = '''def _allocation_tonbag_sample_counts(rows: list, db=None) -> tuple:
    """Allocation 행에서 톤백 표시 개수와 샘플(1kg) 개수 계산.

    Returns:
        (tonbag_500, tonbag_1000, sample_count)

    v8.6.5: db가 주어지면 LOT별 실제 톤백 단가를 조회하여 500/1000kg 분리 집계.
            db가 None이거나 LOT 단가 조회 실패 시 DEFAULT_TONBAG_WEIGHT(500)로 fallback.
            실제 톤백 무게는 입고 시 (net_weight - 1kg) / mxbg_pallet 공식으로 결정.
    """
    try:
        from engine_modules.constants import get_tonbag_unit_weight
    except Exception:
        get_tonbag_unit_weight = None

    tonbag_500 = 0
    tonbag_1000 = 0
    sample_count = 0
    unit_cache: dict = {}  # {lot_no: unit_weight_kg}

    for r in rows:
        if hasattr(r, 'get'):
            qty = float(r.get('qty_mt') or 0)
            lot_no = str(r.get('lot_no') or '').strip()
        else:
            qty = float(getattr(r, 'qty_mt', 0) or 0)
            lot_no = str(getattr(r, 'lot_no', '') or '').strip()

        if qty < SAMPLE_MT_THRESHOLD:
            sample_count += 1
            continue

        unit_w = float(DEFAULT_TONBAG_WEIGHT)
        if db is not None and lot_no and get_tonbag_unit_weight is not None:
            if lot_no not in unit_cache:
                try:
                    unit_cache[lot_no] = float(get_tonbag_unit_weight(db, lot_no) or DEFAULT_TONBAG_WEIGHT)
                except Exception:
                    unit_cache[lot_no] = float(DEFAULT_TONBAG_WEIGHT)
            unit_w = unit_cache[lot_no] or float(DEFAULT_TONBAG_WEIGHT)

        if unit_w <= 0:
            unit_w = float(DEFAULT_TONBAG_WEIGHT)
        count = int(round(qty * 1000.0 / unit_w))
        if abs(unit_w - 1000.0) < 0.5:
            tonbag_1000 += count
        else:
            tonbag_500 += count

    return tonbag_500, tonbag_1000, sample_count


def _format_tonbag_summary(tb500: int, tb1000: int) -> str:
    """톤백 카운트를 표시 문자열로 포맷.

    1000kg가 0이면 "500kg N개" 만, 둘 다 있으면 "500kg N개, 1000kg M개" 로 표시.
    """
    if tb1000 > 0 and tb500 > 0:
        return f"500kg {tb500}개, 1000kg {tb1000}개"
    if tb1000 > 0:
        return f"1000kg {tb1000}개"
    return f"500kg {tb500}개"'''


# ───────────────────────────────────────────────────────────────────────
# 호출부 1 (line 129~132) — show_with_data()
# ───────────────────────────────────────────────────────────────────────
OLD_CALL1 = '''        total_mt = sum(float(r.get('qty_mt') or 0) for r in rows)
        tb500, samp = _allocation_tonbag_sample_counts(rows)
        self._summary_var.set(
            f"고객: (붙여넣기) | 총 {len(rows)}행 | 총량: {total_mt:.4f} MT | 500kg {tb500}개, 샘플 {samp}개"
        )'''

NEW_CALL1 = '''        total_mt = sum(float(r.get('qty_mt') or 0) for r in rows)
        tb500, tb1000, samp = _allocation_tonbag_sample_counts(rows, db=getattr(self.engine, 'db', None))
        self._summary_var.set(
            f"고객: (붙여넣기) | 총 {len(rows)}행 | 총량: {total_mt:.4f} MT | {_format_tonbag_summary(tb500, tb1000)}, 샘플 {samp}개"
        )'''


# ───────────────────────────────────────────────────────────────────────
# 호출부 2 (line 488~492) — _parse_file()
# ───────────────────────────────────────────────────────────────────────
OLD_CALL2 = '''        fname = path.split('/')[-1].split(chr(92))[-1]
        tb500, samp = _allocation_tonbag_sample_counts(self.parsed_rows)
        self._summary_var.set(
            f"고객: {customer} | 총 {len(self.parsed_rows)}행 | 총량: {total:.4f} MT | "
            f"500kg {tb500}개, 샘플 {samp}개 | 파싱: {elapsed_sec:.2f}초 | {fname}"
        )'''

NEW_CALL2 = '''        fname = path.split('/')[-1].split(chr(92))[-1]
        tb500, tb1000, samp = _allocation_tonbag_sample_counts(self.parsed_rows, db=getattr(self.engine, 'db', None))
        self._summary_var.set(
            f"고객: {customer} | 총 {len(self.parsed_rows)}행 | 총량: {total:.4f} MT | "
            f"{_format_tonbag_summary(tb500, tb1000)}, 샘플 {samp}개 | 파싱: {elapsed_sec:.2f}초 | {fname}"
        )'''


# ───────────────────────────────────────────────────────────────────────
# 호출부 3 (line 573~582) — 예약 실행 확인 메시지
# ───────────────────────────────────────────────────────────────────────
OLD_CALL3 = '''        tb500, samp = _allocation_tonbag_sample_counts(self.parsed_rows)
        if self._lot_mode_var.get():
            confirm_msg = (
                f"LOT 단위로 500kg 제품 {tb500}개 및 샘플(1kg) {samp}개를 예약 계획으로 저장합니다.\\n"
                "톤백 ID는 지금 지정하지 않으며, 바코드 스캔 시점에 확정됩니다.\\n계속하시겠습니까?"
            )
        else:
            confirm_msg = (
                f"500kg 제품 {tb500}개 및 샘플(1kg) {samp}개 판매 배정합니다.\\n계속하시겠습니까?"
            )'''

NEW_CALL3 = '''        tb500, tb1000, samp = _allocation_tonbag_sample_counts(self.parsed_rows, db=getattr(self.engine, 'db', None))
        _tb_summary = _format_tonbag_summary(tb500, tb1000)
        if self._lot_mode_var.get():
            confirm_msg = (
                f"LOT 단위로 {_tb_summary} 제품 및 샘플(1kg) {samp}개를 예약 계획으로 저장합니다.\\n"
                "톤백 ID는 지금 지정하지 않으며, 바코드 스캔 시점에 확정됩니다.\\n계속하시겠습니까?"
            )
        else:
            confirm_msg = (
                f"{_tb_summary} 제품 및 샘플(1kg) {samp}개 판매 배정합니다.\\n계속하시겠습니까?"
            )'''


# ───────────────────────────────────────────────────────────────────────
# 호출부 4 (line 815~863) — 업로드 현황 팝업
#   - new_tb 산정 시 db 전달 + 1000kg 분리
#   - prev_tb 산정 시 allocation_plan.lot_no 함께 조회 → LOT 단가 기반
#   - 표시 변수는 합계(new_tb / prev_tb / total_tb)로 유지하되 1000kg 카운트도 보관
# ───────────────────────────────────────────────────────────────────────
OLD_CALL4 = '''        # ── 이번 업로드 수치 ─────────────────────────────────────────────────
        new_tb, new_samp = _allocation_tonbag_sample_counts(self.parsed_rows)
        new_total = len(self.parsed_rows)

        # ── 기존 예약 현황 (DB 조회) ─────────────────────────────────────────
        prev_tb, prev_samp, prev_total = 0, 0, 0
        if hasattr(self.engine, 'db') and self.engine.db:
            try:
                fp    = dup.get('fingerprint', '')
                fname = dup.get('file_name', '')
                if fp:
                    rows_db = self.engine.db.fetchall(
                        "SELECT qty_mt FROM allocation_plan "
                        "WHERE status = 'RESERVED' AND source_fingerprint = ?",
                        (fp,)
                    )
                elif fname and fname not in ('(붙여넣기)', '(붙여넣기 데이터)'):
                    rows_db = self.engine.db.fetchall(
                        "SELECT qty_mt FROM allocation_plan "
                        "WHERE status = 'RESERVED' AND source_file LIKE ?",
                        (f"%{fname}",)
                    )
                else:
                    rows_db = []
                for r in (rows_db or []):
                    q = float(r.get('qty_mt', 0) or 0) if isinstance(r, dict) else float(r[0] or 0)
                    if q >= SAMPLE_MT_THRESHOLD:
                        prev_tb += int(round(q * 1000 / 500))
                    else:
                        prev_samp += 1
                prev_total = len(rows_db or [])
            except Exception as e:
                logger.debug(f"[SUMMARY] DB 기존 예약 조회 실패: {e}")'''

NEW_CALL4 = '''        # ── 이번 업로드 수치 ─────────────────────────────────────────────────
        _db_ref = getattr(self.engine, 'db', None)
        new_tb500, new_tb1000, new_samp = _allocation_tonbag_sample_counts(self.parsed_rows, db=_db_ref)
        new_tb = new_tb500 + new_tb1000
        new_total = len(self.parsed_rows)

        # ── 기존 예약 현황 (DB 조회) ─────────────────────────────────────────
        prev_tb500, prev_tb1000, prev_samp, prev_total = 0, 0, 0, 0
        if _db_ref:
            try:
                fp    = dup.get('fingerprint', '')
                fname = dup.get('file_name', '')
                if fp:
                    rows_db = _db_ref.fetchall(
                        "SELECT qty_mt, lot_no FROM allocation_plan "
                        "WHERE status = 'RESERVED' AND source_fingerprint = ?",
                        (fp,)
                    )
                elif fname and fname not in ('(붙여넣기)', '(붙여넣기 데이터)'):
                    rows_db = _db_ref.fetchall(
                        "SELECT qty_mt, lot_no FROM allocation_plan "
                        "WHERE status = 'RESERVED' AND source_file LIKE ?",
                        (f"%{fname}",)
                    )
                else:
                    rows_db = []
                # LOT 기반 unit_weight 캐시 + 분리 집계 — 함수 재사용
                prev_tb500, prev_tb1000, prev_samp = _allocation_tonbag_sample_counts(
                    [dict(r) if not isinstance(r, dict) else r for r in (rows_db or [])],
                    db=_db_ref,
                )
                prev_total = len(rows_db or [])
            except Exception as e:
                logger.debug(f"[SUMMARY] DB 기존 예약 조회 실패: {e}")
        prev_tb = prev_tb500 + prev_tb1000'''


# ───────────────────────────────────────────────────────────────────────
# 호출부 4 (이어서) — 합계 + 테이블 셀에 1000kg 분리 표시
# ───────────────────────────────────────────────────────────────────────
OLD_TABLE = '''        # ── 합계 ─────────────────────────────────────────────────────────────
        total_tb   = prev_tb   + new_tb
        total_samp = prev_samp + new_samp
        total_rows = prev_total + new_total'''

NEW_TABLE = '''        # ── 합계 ─────────────────────────────────────────────────────────────
        total_tb500  = prev_tb500  + new_tb500
        total_tb1000 = prev_tb1000 + new_tb1000
        total_tb     = prev_tb     + new_tb
        total_samp   = prev_samp + new_samp
        total_rows   = prev_total + new_total

        # 셀 표시: 1000kg 톤백이 있으면 "N+M" 분리 표시, 없으면 기존처럼 N개
        def _tb_cell(tb500: int, tb1000: int) -> str:
            if tb1000 > 0 and tb500 > 0:
                return f"{tb500}+{tb1000}"
            if tb1000 > 0:
                return f"{tb1000}(1t)"
            return str(tb500)'''


OLD_TABLE_ROWS = '''        HEADERS   = ["구분",          "행 수", "톤백(500kg)", "샘플(1kg)"]
        COL_CHARS = [14,               7,       12,            9         ]'''

NEW_TABLE_ROWS = '''        HEADERS   = ["구분",          "행 수", "톤백(500/1000kg)", "샘플(1kg)"]
        COL_CHARS = [14,               7,       16,                 9         ]'''


OLD_TABLE_DATA = '''        table_rows = [
            ("기존 예약",   prev_total, prev_tb, prev_samp),
            ("이번 업로드", new_total,  new_tb,  new_samp),
            ("합  계",      total_rows, total_tb, total_samp),
        ]'''

NEW_TABLE_DATA = '''        table_rows = [
            ("기존 예약",   prev_total, _tb_cell(prev_tb500, prev_tb1000),  prev_samp),
            ("이번 업로드", new_total,  _tb_cell(new_tb500,  new_tb1000),   new_samp),
            ("합  계",      total_rows, _tb_cell(total_tb500, total_tb1000), total_samp),
        ]'''


PATCHES = [
    ("function definition (_allocation_tonbag_sample_counts)", OLD_FUNC, NEW_FUNC),
    ("call site 1: show_with_data()", OLD_CALL1, NEW_CALL1),
    ("call site 2: _parse_file()", OLD_CALL2, NEW_CALL2),
    ("call site 3: reserve confirm message", OLD_CALL3, NEW_CALL3),
    ("call site 4: upload summary popup (new+prev)", OLD_CALL4, NEW_CALL4),
    ("call site 4b: total + cell helper", OLD_TABLE, NEW_TABLE),
    ("call site 4c: table headers", OLD_TABLE_ROWS, NEW_TABLE_ROWS),
    ("call site 4d: table rows", OLD_TABLE_DATA, NEW_TABLE_DATA),
]


def main() -> int:
    if not TARGET.exists():
        print(f"[ERROR] 대상 파일 없음: {TARGET}")
        return 1

    src = TARGET.read_text(encoding="utf-8")
    original_len = len(src)

    applied = []
    skipped = []
    for label, old, new in PATCHES:
        if old not in src:
            skipped.append(label)
            print(f"[SKIP] {label} — OLD 문자열을 찾지 못함")
            continue
        cnt = src.count(old)
        if cnt > 1:
            print(f"[ERROR] {label} — OLD 문자열이 {cnt}개 매칭됨 (유니크해야 함)")
            return 2
        src = src.replace(old, new, 1)
        applied.append(label)
        print(f"[OK]   {label}")

    if skipped:
        print(f"\n[ABORT] {len(skipped)}개 패치 미적용 — 파일이 이미 수정되었거나 버전이 다름")
        return 3

    # 백업
    backup = TARGET.with_suffix(TARGET.suffix + ".bak_unit_weight")
    backup.write_text(TARGET.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"\n[BACKUP] {backup.name}")

    TARGET.write_text(src, encoding="utf-8")
    print(f"[WRITE]  {TARGET.name}  ({original_len} → {len(src)} bytes)")

    # py_compile 검증
    import py_compile
    try:
        py_compile.compile(str(TARGET), doraise=True)
        print(f"[COMPILE] OK")
    except py_compile.PyCompileError as e:
        print(f"[COMPILE] FAIL: {e}")
        return 4

    print(f"\n✅ {len(applied)}개 패치 모두 적용 + py_compile 통과")
    return 0


if __name__ == "__main__":
    sys.exit(main())
