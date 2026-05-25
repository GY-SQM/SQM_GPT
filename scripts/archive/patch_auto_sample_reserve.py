#!/usr/bin/env python3
"""
patch_auto_sample_reserve.py
============================
[AUTO-SAMPLE-RESERVE] 일반 배정(is_sample_req=False) 완료 후
해당 LOT에 존재하는 샘플 톤백(is_sample=1)을 자동으로 RESERVED 상태로 전환.

문제:
  _ra_fetch_tonbag_pool() 이 is_sample=0 만 반환 → 샘플 톤백은
  배정 완료 후에도 AVAILABLE 그대로 남음.

해결:
  _ra_log_random_selection() 호출 직후에 AUTO-SAMPLE-RESERVE 블록 삽입.
  LOT의 AVAILABLE 샘플 톤백을 찾아 status=RESERVED + picked_to + sale_ref 기록.

대상: engine_modules/inventory_modular/outbound_mixin.py  (Python, Edit 허용)
방식: bytes 레벨 find & replace (4,232줄 대형 파일, 정확성 보장)
"""
import sys, os, shutil, subprocess
from datetime import datetime

BASE    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET  = os.path.join(BASE, 'engine_modules', 'inventory_modular', 'outbound_mixin.py')

# ── 앵커: _ra_log_random_selection 호출 블록 + 다음 if strict_mode ─────────
OLD = (
    b"                    # \xeb\x9e\x9c\xeb\x8d\xa4 \xec\x84\xa0\xed\x83\x9d \xec\x9d\xb4\xeb\xa0\xa5 \xeb\xa1\x9c\xea\xb7\xb8\r\n"
    b"                    self._ra_log_random_selection(\r\n"
    b"                        lot_no, sale_ref, customer, allocation_random_mode,\r\n"
    b"                        seed_hash, tonbags, selected, reserved_in_lot, now)\r\n"
    b"\r\n"
    b"                if strict_mode and strict_errors:\r\n"
)

NEW = (
    b"                    # \xeb\x9e\x9c\xeb\x8d\xa4 \xec\x84\xa0\xed\x83\x9d \xec\x9d\xb4\xeb\xa0\xa5 \xeb\xa1\x9c\xea\xb7\xb8\r\n"
    b"                    self._ra_log_random_selection(\r\n"
    b"                        lot_no, sale_ref, customer, allocation_random_mode,\r\n"
    b"                        seed_hash, tonbags, selected, reserved_in_lot, now)\r\n"
    b"\r\n"
    b"                    # [v8.6.9 AUTO-SAMPLE-RESERVE]: \xec\x9d\xbc\xeb\xb0\x98 \xeb\xb0\xb0\xec\xa0\x95 \xec\x99\x84\xeb\xa3\x8c \xed\x9b\x84 \xed\x95\xb4\xeb\x8b\xb9 LOT \xec\x83\x98\xed\x94\x8c \xed\x86\xa4\xeb\xb0\xb1 \xec\x9e\x90\xeb\x8f\x99 RESERVED\r\n"
    b"                    # \xec\xa1\xb0\xea\xb1\xb4: is_sample_req=False(\xec\x9d\xbc\xeb\xb0\x98 \xeb\xb0\xb0\xec\xa0\x95) + \xec\x8a\xb9\xec\x9d\xb8\xeb\x8c\x80\xea\xb8\xb0 \xec\x95\x84\xeb\x8b\x90 + AVAILABLE \xec\x83\x98\xed\x94\x8c \xed\x86\xa4\xeb\xb0\xb1 \xec\xa1\xb4\xec\x9e\xac\r\n"
    b"                    if not is_sample_req and not (need_approval and has_workflow_status_col):\r\n"
    b"                        try:\r\n"
    b"                            _sample_pool = self.db.fetchall(\r\n"
    b"                                \"SELECT id, sub_lt FROM inventory_tonbag \"\r\n"
    b"                                \"WHERE lot_no=? AND status='AVAILABLE' \"\r\n"
    b"                                \"AND COALESCE(is_sample,0)=1\",\r\n"
    b"                                (lot_no,)\r\n"
    b"                            )\r\n"
    b"                            if _sample_pool:\r\n"
    b"                                _sample_upd = [\r\n"
    b"                                    (STATUS_RESERVED, customer, sale_ref, now,\r\n"
    b"                                     (sb.get('id') if isinstance(sb, dict) else sb[0]))\r\n"
    b"                                    for sb in _sample_pool\r\n"
    b"                                ]\r\n"
    b"                                self.db.executemany(\r\n"
    b"                                    \"UPDATE inventory_tonbag SET \"\r\n"
    b"                                    \"status=?, picked_to=?, sale_ref=?, updated_at=? \"\r\n"
    b"                                    \"WHERE id=?\",\r\n"
    b"                                    _sample_upd\r\n"
    b"                                )\r\n"
    b"                                self._recalc_lot_status(lot_no)\r\n"
    b"                                logger.info(\r\n"
    b"                                    \"[AUTO-SAMPLE-RESERVE] %s: \xec\x83\x98\xed\x94\x8c %d\xea\xb0\x9c AVAILABLE\xe2\x86\x92RESERVED \"\r\n"
    b"                                    \"(customer=%s, sale_ref=%s)\",\r\n"
    b"                                    lot_no, len(_sample_pool), customer, sale_ref\r\n"
    b"                                )\r\n"
    b"                        except Exception as _spe:\r\n"
    b"                            logger.warning(\r\n"
    b"                                \"[AUTO-SAMPLE-RESERVE] %s: \xec\x83\x98\xed\x94\x8c \xec\x98\x88\xec\x95\xbd \xec\x8b\xa4\xed\x8c\xa8(\xeb\xac\xb4\xec\x8b\x9c): %s\",\r\n"
    b"                                lot_no, _spe\r\n"
    b"                            )\r\n"
    b"\r\n"
    b"                if strict_mode and strict_errors:\r\n"
)

def main():
    if not os.path.exists(TARGET):
        print(f"❌ 파일 없음: {TARGET}")
        sys.exit(1)

    with open(TARGET, 'rb') as f:
        data = f.read()

    # LF 버전도 시도
    old_lf = OLD.replace(b'\r\n', b'\n')
    if OLD in data:
        anchor, rep = OLD, NEW
        print("앵커: CRLF 버전 매칭")
    elif old_lf in data:
        anchor = old_lf
        rep = NEW.replace(b'\r\n', b'\n')
        print("앵커: LF 버전 매칭")
    else:
        print("❌ 앵커를 찾지 못했습니다. 이미 적용됐거나 파일이 변경됐습니다.")
        # 수동 진단
        check = b"_ra_log_random_selection"
        idx = data.find(check)
        if idx == -1:
            print("  → _ra_log_random_selection 자체가 없음!")
        else:
            print(f"  → _ra_log_random_selection 위치: {idx}")
            print("  → 주변 50바이트:", repr(data[idx:idx+200]))
        sys.exit(1)

    count = data.count(anchor)
    if count > 1:
        print(f"⚠️  앵커 {count}개 발견 — 첫 번째만 치환")

    # 백업
    bak = TARGET + '.bak_asr_' + datetime.now().strftime('%Y%m%d_%H%M%S')
    shutil.copy2(TARGET, bak)
    print(f"📦 백업: {bak}")

    new_data = data.replace(anchor, rep, 1)
    with open(TARGET, 'wb') as f:
        f.write(new_data)
    print(f"✅ 패치 완료 ({len(data)} → {len(new_data)} bytes)")

    # py_compile 검증
    result = subprocess.run(
        ['python', '-m', 'py_compile', TARGET],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print("✅ py_compile 통과")
    else:
        print("❌ py_compile 실패 — 백업에서 복원합니다.")
        print(result.stderr)
        shutil.copy2(bak, TARGET)
        sys.exit(1)

if __name__ == '__main__':
    main()
