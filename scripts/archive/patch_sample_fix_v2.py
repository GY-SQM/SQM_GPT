# -*- coding: utf-8 -*-
"""
patch_sample_fix_v2.py
======================
[SAMPLE-FIX v2] outbound_mixin.py — 정합성 강화

v1 문제: pick_count == len(tonbags)+1 이면 샘플 여부 확인 없이 cap
         → 진짜 1개 부족한 경우도 조용히 통과시키는 위험

v2 수정: LOT에 실제 샘플 톤백(is_sample=1)이 존재할 때만 cap 적용
         → 진짜 부족 케이스는 여전히 HARD-STOP 유지
"""
import pathlib, sys, py_compile
from datetime import datetime

ROOT = pathlib.Path(__file__).resolve().parents[1]
TARGET = ROOT / "engine_modules" / "inventory_modular" / "outbound_mixin.py"

OLD = \
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
                    pick_count = len(tonbags)'''

NEW = \
'''            else:
                pick_count = max(1, math.ceil(weight_kg / _unit_w))
                # [v8.6.9 SAMPLE-FIX v2]: ceil 반올림 오버 보정 (정합성 강화)
                # 조건 ①: pick_count = 가용 정상 톤백 수 + 1 (정확히 1개 초과)
                # 조건 ②: LOT에 샘플 톤백(is_sample=1)이 실제로 존재
                # → 두 조건 모두 만족할 때만 cap (진짜 부족 케이스는 HARD-STOP 유지)
                if pick_count == len(tonbags) + 1:
                    _has_sample = self.db.fetchone(
                        "SELECT 1 FROM inventory_tonbag "
                        "WHERE lot_no=? AND COALESCE(is_sample,0)=1 LIMIT 1",
                        (lot_no,)
                    )
                    if _has_sample:
                        logger.info(
                            "[SAMPLE-FIX] %s: 샘플 톤백 확인 → pick_count=%d cap→%d "
                            "(qty_mt=%.3f, unit_w=%.0fkg, ceil 반올림 보정)",
                            lot_no, pick_count, len(tonbags), qty_mt, _unit_w
                        )
                        pick_count = len(tonbags)
                    else:
                        logger.warning(
                            "[SAMPLE-FIX] %s: pick_count=%d > avail=%d 이나 샘플 없음 "
                            "→ HARD-STOP 유지 (진짜 부족)",
                            lot_no, pick_count, len(tonbags)
                        )'''

def main():
    src = TARGET.read_text(encoding="utf-8")
    count = src.count(OLD)
    if count == 0:
        print("❌ OLD 패턴 없음 — 이미 v2 적용됐거나 코드 변경됨")
        sys.exit(1)
    if count > 1:
        print(f"❌ OLD 패턴 {count}곳 — 중복 위험")
        sys.exit(1)

    bak = TARGET.with_suffix(".py.bak_samplefix_v2_" +
          datetime.now().strftime("%Y%m%d_%H%M%S"))
    bak.write_text(src, encoding="utf-8")
    print(f"백업: {bak.name}")

    patched = src.replace(OLD, NEW, 1)
    TARGET.write_text(patched, encoding="utf-8")

    try:
        py_compile.compile(str(TARGET), doraise=True)
        print("✅ py_compile OK")
    except py_compile.PyCompileError as e:
        print(f"❌ py_compile FAIL: {e}")
        TARGET.write_text(src, encoding="utf-8")
        print("⏪ 롤백 완료")
        sys.exit(1)

    # 적용 확인
    result = TARGET.read_text(encoding="utf-8")
    if "_has_sample" in result and "HARD-STOP 유지" in result:
        print("✅ SAMPLE-FIX v2 적용 확인")
    print("✅ 완료")

if __name__ == "__main__":
    main()
