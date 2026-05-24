# -*- coding: utf-8 -*-
"""
patch_sample_fix_engine.py
==========================
① allocation_api.py — SAMPLE-FIX 임시 패치 롤백
② outbound_mixin.py — _ra_resolve_pick_count() 근본 수정

[수정 내용]
  sublot_count 미지정 시 ceil(weight_kg / unit_w) 계산이
  가용 정상 톤백 수를 1 초과하는 경우 cap 처리.
  (샘플 포함 LOT에서 qty_mt=전체중량으로 기입 → ceil 반올림 오버)
"""
import pathlib, sys, py_compile
from datetime import datetime

ROOT = pathlib.Path(__file__).resolve().parents[1]

# ──────────────────────────────────────────────────────────────────────
# ① allocation_api.py 롤백 (SAMPLE-FIX 임시 패치 제거)
# ──────────────────────────────────────────────────────────────────────
ALLOC_PATH = ROOT / "backend" / "api" / "allocation_api.py"

ALLOC_OLD = '''        # [SAMPLE-FIX v8.6.9] sublot_count 미지정 행: 정상 톤백 수 자동 보정
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

ALLOC_NEW = '''        result = engine.reserve_from_allocation(rows, source_file=file.filename)'''

# ──────────────────────────────────────────────────────────────────────
# ② outbound_mixin.py 엔진 수정
# ──────────────────────────────────────────────────────────────────────
ENGINE_PATH = ROOT / "engine_modules" / "inventory_modular" / "outbound_mixin.py"

ENGINE_OLD = \
'''            else:
                pick_count = max(1, math.ceil(weight_kg / _unit_w))
            logger.debug(
                f"[B pick_count] {lot_no}: "
                f"qty_mt={qty_mt}→weight_kg={weight_kg}÷unit_w={_unit_w}"
                f"=pick_count={pick_count}"
            )
        return pick_count'''

ENGINE_NEW = \
'''            else:
                pick_count = max(1, math.ceil(weight_kg / _unit_w))
                # [v8.6.9 SAMPLE-FIX]: ceil 반올림으로 가용 정상 톤백 수 +1 초과 시 cap
                # 원인: 샘플 포함 LOT의 qty_mt=전체중량(샘플 포함) 기입 →
                #       ceil(qty_mt*1000 / unit_w) = 정상톤백수+1 → HARD-STOP 오발동
                # tonbags 는 _ra_fetch_tonbag_pool 반환값 (정상 톤백만 포함, is_sample=0)
                if pick_count == len(tonbags) + 1:
                    logger.info(
                        "[SAMPLE-FIX] %s: pick_count=%d → cap to avail=%d "
                        "(qty_mt=%.3f, unit_w=%.0fkg, ceil 반올림 보정)",
                        lot_no, pick_count, len(tonbags), qty_mt, _unit_w
                    )
                    pick_count = len(tonbags)
            logger.debug(
                f"[B pick_count] {lot_no}: "
                f"qty_mt={qty_mt}→weight_kg={weight_kg}÷unit_w={_unit_w}"
                f"=pick_count={pick_count}"
            )
        return pick_count'''


def patch_file(path, old, new, label):
    src = path.read_text(encoding="utf-8")
    count = src.count(old)
    if count == 0:
        print(f"  ⚠️  [{label}] OLD 패턴 없음 — 이미 적용됐거나 코드 변경됨, 스킵")
        return True
    if count > 1:
        print(f"  ❌ [{label}] OLD 패턴 {count}곳 — 중복 위험, 중단")
        return False
    bak = path.with_suffix(path.suffix + ".bak_engine_fix_" +
          datetime.now().strftime("%Y%m%d_%H%M%S"))
    bak.write_text(src, encoding="utf-8")
    print(f"  백업: {bak.name}")
    patched = src.replace(old, new, 1)
    path.write_text(patched, encoding="utf-8")
    try:
        py_compile.compile(str(path), doraise=True)
        print(f"  ✅ [{label}] 패치 + py_compile OK")
        return True
    except py_compile.PyCompileError as e:
        print(f"  ❌ [{label}] py_compile FAIL: {e}")
        path.write_text(src, encoding="utf-8")
        print(f"  ⏪ 롤백 완료")
        return False


def main():
    ok = True

    print("① allocation_api.py — 임시 패치 롤백")
    ok &= patch_file(ALLOC_PATH, ALLOC_OLD, ALLOC_NEW, "alloc-api rollback")

    print("② outbound_mixin.py — 엔진 SAMPLE-FIX 적용")
    ok &= patch_file(ENGINE_PATH, ENGINE_OLD, ENGINE_NEW, "engine sample-fix")

    if ok:
        print("\n✅ 모든 패치 완료")
    else:
        print("\n❌ 일부 패치 실패 — 위 로그 확인")
        sys.exit(1)

if __name__ == "__main__":
    main()
