#!/usr/bin/env python3
"""
patch_sold_today_fix.py
목적: sqm-logistics.js 의 _soldTodayStr() 를 Intl.DateTimeFormat(Asia/Seoul) 기반으로 교체
원인: PyWebView JS 엔진에서 new Date().getDate() 가 UTC 기준으로 반환될 수 있어
     한국 시간(KST = UTC+9) 기준 날짜가 틀리게 나옴 (예: 05-26 오전에 05-25 반환)
적용: 2026-05-25
"""
import sys, os

TARGET = os.path.join(os.path.dirname(__file__),
    '..', 'frontend', 'js', 'sqm-logistics.js')
TARGET = os.path.normpath(TARGET)

OLD = """  function _soldTodayStr() {
    return _soldLocalDate(new Date());
  }""".encode('utf-8')

NEW = """  function _soldTodayStr() {
    // v869: Intl 기반 KST 날짜 — PyWebView UTC 버그 우회
    try {
      var parts = new Intl.DateTimeFormat('ko-KR', {
        timeZone: 'Asia/Seoul',
        year: 'numeric', month: '2-digit', day: '2-digit'
      }).formatToParts(new Date());
      var p = {};
      parts.forEach(function(x){ p[x.type] = x.value; });
      return p.year + '-' + p.month + '-' + p.day;
    } catch(e) {
      return _soldLocalDate(new Date()); // fallback
    }
  }""".encode('utf-8')

with open(TARGET, 'rb') as f:
    data = f.read()

if OLD not in data:
    print('[ERROR] 패치 대상 문자열을 찾지 못했습니다. 이미 패치됐거나 파일이 달라졌습니다.')
    print('검색 문자열:', OLD[:60])
    sys.exit(1)

count = data.count(OLD)
print(f'[INFO] 패치 대상 {count}곳 발견')

patched = data.replace(OLD, NEW, 1)

with open(TARGET, 'wb') as f:
    f.write(patched)

print(f'[OK] {TARGET} 패치 완료')
