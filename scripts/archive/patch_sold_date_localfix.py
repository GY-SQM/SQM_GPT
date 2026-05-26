#!/usr/bin/env python3
"""
patch_sold_date_localfix.py
===========================
SOLD 날짜 필터 (오늘/이번주/이번달) UTC 버그 수정

문제: new Date().toISOString().slice(0,10)  → UTC 날짜 (한국 자정~09:00 사이 하루 어긋남)
     new Date(year,month,1).toISOString()  → 월 시작일 오류 (UTC로 변환 시 전날로)
수정: 로컬 날짜 전용 헬퍼 _soldLocalDate(d) 추가 후 전 구간 교체

대상: frontend/js/sqm-logistics.js (IIFE, ABSOLUTE EDIT BAN)
방식: bytes 레벨 find & replace
"""
import sys, os, shutil, subprocess
from datetime import datetime

BASE   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(BASE, 'frontend', 'js', 'sqm-logistics.js')

# ── 앵커: 기존 SOLD 날짜 헬퍼 블록 전체 교체 ─────────────────────────
OLD = b"""\
  /* \xe2\x94\x80\xe2\x94\x80 SOLD 날짜 헬퍼 \xe2\x94\x80\xe2\x94\x80 */
  function _soldTodayStr() {
    return new Date().toISOString().slice(0, 10);
  }
  window._soldSetToday = function() {
    var t = _soldTodayStr();
    var f = document.getElementById('sold-date-from');
    var to = document.getElementById('sold-date-to');
    if (f) f.value = t;
    if (to) to.value = t;
    window._soldSearch();
  };
  window._soldSetWeek = function() {
    var now = new Date();
    var mon = new Date(now);
    mon.setDate(now.getDate() - ((now.getDay() + 6) % 7));
    var f = document.getElementById('sold-date-from');
    var to = document.getElementById('sold-date-to');
    if (f)  f.value  = mon.toISOString().slice(0, 10);
    if (to) to.value = _soldTodayStr();
    window._soldSearch();
  };
  window._soldSetMonth = function() {
    var now = new Date();
    var first = new Date(now.getFullYear(), now.getMonth(), 1);
    var f = document.getElementById('sold-date-from');
    var to = document.getElementById('sold-date-to');
    if (f)  f.value  = first.toISOString().slice(0, 10);
    if (to) to.value = _soldTodayStr();
    window._soldSearch();
  };"""

NEW = b"""\
  /* \xe2\x94\x80\xe2\x94\x80 SOLD 날짜 헬퍼 (v8.6.9 로컈 날짜 고정 \xe2\x80\x94 UTC 버그 수정) \xe2\x94\x80\xe2\x94\x80 */
  function _soldLocalDate(d) {
    // toISOString() 대신 로컈 기준 YYYY-MM-DD 반환
    var y = d.getFullYear();
    var m = String(d.getMonth() + 1).padStart(2, '0');
    var dd = String(d.getDate()).padStart(2, '0');
    return y + '-' + m + '-' + dd;
  }
  function _soldTodayStr() {
    return _soldLocalDate(new Date());
  }
  window._soldSetToday = function() {
    var t = _soldTodayStr();
    var f = document.getElementById('sold-date-from');
    var to = document.getElementById('sold-date-to');
    if (f) f.value = t;
    if (to) to.value = t;
    window._soldSearch();
  };
  window._soldSetWeek = function() {
    var now = new Date();
    var mon = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    mon.setDate(mon.getDate() - ((mon.getDay() + 6) % 7));
    var f = document.getElementById('sold-date-from');
    var to = document.getElementById('sold-date-to');
    if (f)  f.value  = _soldLocalDate(mon);
    if (to) to.value = _soldTodayStr();
    window._soldSearch();
  };
  window._soldSetMonth = function() {
    var now = new Date();
    var first = new Date(now.getFullYear(), now.getMonth(), 1);
    var f = document.getElementById('sold-date-from');
    var to = document.getElementById('sold-date-to');
    if (f)  f.value  = _soldLocalDate(first);
    if (to) to.value = _soldTodayStr();
    window._soldSearch();
  };"""

def main():
    if not os.path.exists(TARGET):
        print(f"❌ 파일 없음: {TARGET}")
        sys.exit(1)

    with open(TARGET, 'rb') as f:
        data = f.read()

    # 이미 적용 여부 확인
    if b'_soldLocalDate' in data:
        print("ℹ️  이미 적용됨 — 스킵")
        return

    # LF / CRLF 양쪽 시도
    if OLD in data:
        anchor, rep, mode = OLD, NEW, "LF"
    else:
        old_cr = OLD.replace(b'\n', b'\r\n')
        new_cr = NEW.replace(b'\n', b'\r\n')
        if old_cr in data:
            anchor, rep, mode = old_cr, new_cr, "CRLF"
        else:
            print("❌ 앵커 없음 — 진단:")
            idx = data.find(b'_soldTodayStr')
            if idx != -1:
                print(f"  _soldTodayStr 위치: {idx}")
                print("  주변:", repr(data[max(0,idx-40):idx+120]))
            sys.exit(1)

    bak = TARGET + '.bak_datefix_' + datetime.now().strftime('%Y%m%d_%H%M%S')
    shutil.copy2(TARGET, bak)
    print(f"📦 백업: {bak}")

    new_data = data.replace(anchor, rep, 1)
    with open(TARGET, 'wb') as f:
        f.write(new_data)
    print(f"✅ 패치 완료 ({len(data)} → {len(new_data)} bytes, {mode})")

    result = subprocess.run(['node', '--check', TARGET], capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ node --check 통과")
    else:
        print("❌ node --check 실패 — 백업 복원")
        print(result.stderr)
        shutil.copy2(bak, TARGET)
        sys.exit(1)

if __name__ == '__main__':
    main()
