# -*- coding: utf-8 -*-
"""
patch_alloc_sample_fix.py
=========================
[SAMPLE-FIX] allocation_api.py — 샘플 톤백 포함 LOT의 QTY_EXCEEDS_AVAILABLE 오류 수정

증상: 정상 10개 + 샘플 1개 LOT에서 qty_mt=10 MT → ceil(10000/909)=11 → 가용 10개 초과 HARD-STOP
원인: qty_mt가 전체 LOT 중량(샘플 포함)으로 기입될 때 단위 중량으로 나누면 ceil 오버 발생
해결: 엔진 호출 전 sublot_count 미지정 행에 대해 DB 정상 톤백 수를 조회하여 자동 보정
     calc_pick_count > avail_normal_cnt 이면 sublot_count = avail_normal_cnt 로 캡
     (engine_modules 수정 금지 Rule 준수 — allocation_api.py 에만 패치)
"""
import pathlib, sys, math

TARGET = pathlib.Path(__file__).resolve().parents[1] / "backend" / "api" / "allocation_api.py"

OLD = '        # 엔진 호출 — 트랜잭션 내부 처리\n        result = engine.reserve_from_allocation(rows, source_file=file.filename)'

NEW = '''        # 엔진 호출 — 트랜잭션 내부 처리
        # [SAMPLE-FIX v8.6.9] sublot_count 미지정 행: 정상 톤백 수 자동 보정
        # 샘플 포함 LOT에서 qty_mt=전체중량 → ceil 오버 → QTY_EXCEEDS_AVAILABLE 방지
        try:
            import math as _math
            _fix_con = _alloc_db()
            for _row in rows:
                if _row.get('sublot_count'):
                    continue  # 이미 지정된 경우 스킵
                _ln  = _row.get('lot_no')
                _qmt = float(_row.get('qty_mt') or 0)
                if not _ln or _qmt <= 0:
                    continue
                _avail = _fix_con.execute(
                    """SELECT COUNT(*) AS cnt, AVG(weight) AS avg_w
                       FROM inventory_tonbag
                       WHERE lot_no=? AND status='AVAILABLE'
                         AND COALESCE(is_sample, 0) = 0""",
                    (_ln,)
                ).fetchone()
                if not _avail or not _avail[0]:
                    continue
                _avail_cnt = int(_avail[0])
                _avg_w     = float(_avail[1] or 0)
                if _avg_w <= 0 or _avail_cnt <= 0:
                    continue
                _calc_cnt = _math.ceil(_qmt * 1000 / _avg_w)
                if _calc_cnt > _avail_cnt:
                    logger.info(
                        "[SAMPLE-FIX] %s: calc=%d > avail=%d → sublot_count=%d 자동보정 "
                        "(qty_mt=%.3f, avg_w=%.0fkg)",
                        _ln, _calc_cnt, _avail_cnt, _avail_cnt, _qmt, _avg_w
                    )
                    _row['sublot_count'] = _avail_cnt
            _fix_con.close()
        except Exception as _fix_err:
            logger.debug("[SAMPLE-FIX] 스킵: %s", _fix_err)

        result = engine.reserve_from_allocation(rows, source_file=file.filename)'''

def main():
    src = TARGET.read_text(encoding="utf-8")

    count = src.count(OLD)
    if count == 0:
        print("❌ OLD 패턴을 찾을 수 없습니다. 이미 패치됐거나 코드가 변경됨.")
        sys.exit(1)
    if count > 1:
        print(f"❌ OLD 패턴이 {count}곳 — 중복 위험. 수동 확인 필요.")
        sys.exit(1)

    patched = src.replace(OLD, NEW, 1)

    # 백업
    bak = TARGET.with_suffix(".py.bak_sample_fix_" +
          __import__('datetime').datetime.now().strftime("%Y%m%d_%H%M%S"))
    bak.write_text(src, encoding="utf-8")
    print(f"백업: {bak.name}")

    TARGET.write_text(patched, encoding="utf-8")
    print("✅ 패치 완료:", TARGET)

    # 문법 검사
    import py_compile
    try:
        py_compile.compile(str(TARGET), doraise=True)
        print("✅ py_compile OK")
    except py_compile.PyCompileError as e:
        print("❌ py_compile FAIL:", e)
        TARGET.write_text(src, encoding="utf-8")
        print("⏪ 롤백 완료")
        sys.exit(1)

if __name__ == "__main__":
    main()
