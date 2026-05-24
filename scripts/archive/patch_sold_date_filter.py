"""
patch_sold_date_filter.py  (v8.6.9)
SOLD 화면 날짜 필터 추가 — 한 줄 헤더 + 날짜 range + 빠른 버튼

변경 내용:
  ① loadOutboundPage 헤더 → 한 줄에 날짜 필터 통합
  ② apiGet('/api/q/sold-list') → 날짜 파라미터 포함 호출
  ③ window._soldSetToday/Week/Month/_soldSearch 헬퍼 함수 추가

기본값: 오늘 날짜 (start=end=today → 당일 처리)

실행: python scripts/patch_sold_date_filter.py
"""
import pathlib, shutil, datetime

ROOT   = pathlib.Path(__file__).resolve().parent.parent
TARGET = ROOT / "frontend" / "js" / "sqm-logistics.js"
TS     = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def backup(p):
    bak = p.with_suffix(p.suffix + f".bak_solddate_{TS}")
    shutil.copy2(p, bak)
    print(f"  📦 백업: {bak.name}")


def patch(src: str) -> str:
    total = 0

    # ── ① 헤더 교체 ─────────────────────────────────────────────────
    OLD1 = (
        "    '<div style=\"display:flex;align-items:center;gap:8px;flex-wrap:wrap;padding:8px 0 12px\">',\n"
        "      '  <h2 style=\"margin:0\">📤 출고 완료 (SOLD)</h2>',\n"
        "      '  <div style=\"display:flex;gap:4px;margin-left:12px\">' + \n"
        "         _outboundModeBtn('lot', 'LOT별', _outMode) + \n"
        "         _outboundModeBtn('customer', '고객사별', _outMode) + \n"
        "         _outboundModeBtn('date', '출고일별', _outMode) + \n"
        "      '  </div>',\n"
        "      '  <div style=\"margin-left:auto;display:flex;gap:8px;align-items:center\">',\n"
        "      '    <button class=\"btn btn-primary\" onclick=\"window.showOutboundPickingModal()\" style=\"font-weight:600\">📋 Picking List 업로드</button>',\n"
        "      '    <button class=\"btn\" onclick=\"window.allocRevertStep(\\'SOLD\\'\" style=\"font-size:12px\" title=\"SOLD 상태를 PICKED로 되돌립니다\">↩ SOLD &rarr; PICKED</button>',\n"
        "      '    <button class=\"btn btn-secondary\" onclick=\"renderPage(\\'outbound\\')\">🔁 새로고침</button>',\n"
        "      '  </div>',\n"
        "      '</div>',"
    )

    # 정확한 패턴 검색용 단순 앵커
    ANCHOR1 = "'<div style=\"display:flex;align-items:center;gap:8px;flex-wrap:wrap;padding:8px 0 12px\">',"
    ANCHOR1_END = "      '</div>',"

    # 위치 기반으로 교체 (앵커로 찾아서 블록 전체 대체)
    start_pos = src.find(ANCHOR1)
    if start_pos == -1:
        print("  ⚠️  [①] 헤더 앵커 미발견")
    else:
        # '</div>', 이후 다음 ','까지 블록 끝 찾기
        search_from = start_pos + len(ANCHOR1)
        # "      '</div>'," 패턴 중 헤더 블록의 마지막 것 찾기
        # outbound-loading div 바로 앞까지가 헤더 블록
        end_marker = "      '<div id=\"outbound-loading\""
        end_pos = src.find(end_marker, search_from)
        if end_pos == -1:
            print("  ⚠️  [①] 헤더 끝 마커 미발견")
        else:
            old_header = src[start_pos:end_pos]
            new_header = (
                "'<div style=\"display:flex;align-items:center;gap:6px;flex-wrap:nowrap;padding:8px 0 10px;overflow-x:auto\">',\n"
                "      '  <h2 style=\"margin:0;white-space:nowrap;font-size:15px\">📤 출고 완료 (SOLD)</h2>',\n"
                "      '  <div style=\"display:flex;gap:3px;flex-shrink:0\">' +\n"
                "         _outboundModeBtn('lot', 'LOT별', _outMode) +\n"
                "         _outboundModeBtn('customer', '고객사별', _outMode) +\n"
                "         _outboundModeBtn('date', '출고일별', _outMode) +\n"
                "      '  </div>',\n"
                "      '  <span style=\"width:1px;height:20px;background:var(--border);margin:0 2px;flex-shrink:0\"></span>',\n"
                "      '  <input type=\"date\" id=\"sold-date-from\" value=\"' + _soldTodayStr() + '\"'\n"
                "        + ' style=\"font-size:11px;padding:2px 4px;border:1px solid var(--border);border-radius:4px;background:var(--panel);color:var(--text);width:114px;flex-shrink:0\">',\n"
                "      '  <span style=\"font-size:12px;color:var(--text-muted);flex-shrink:0\">~</span>',\n"
                "      '  <input type=\"date\" id=\"sold-date-to\" value=\"' + _soldTodayStr() + '\"'\n"
                "        + ' style=\"font-size:11px;padding:2px 4px;border:1px solid var(--border);border-radius:4px;background:var(--panel);color:var(--text);width:114px;flex-shrink:0\">',\n"
                "      '  <button class=\"btn\" onclick=\"window._soldSetToday()\" style=\"font-size:11px;padding:2px 6px;flex-shrink:0\">오늘</button>',\n"
                "      '  <button class=\"btn\" onclick=\"window._soldSetWeek()\"  style=\"font-size:11px;padding:2px 6px;flex-shrink:0\">이번주</button>',\n"
                "      '  <button class=\"btn\" onclick=\"window._soldSetMonth()\" style=\"font-size:11px;padding:2px 6px;flex-shrink:0\">이번달</button>',\n"
                "      '  <button class=\"btn btn-primary\" onclick=\"window._soldSearch()\" style=\"font-size:11px;padding:2px 8px;font-weight:700;flex-shrink:0\">조회</button>',\n"
                "      '  <span style=\"width:1px;height:20px;background:var(--border);margin:0 2px;flex-shrink:0\"></span>',\n"
                "      '  <div style=\"display:flex;gap:5px;align-items:center;flex-shrink:0\">',\n"
                "      '    <button class=\"btn btn-primary\" onclick=\"window.showOutboundPickingModal()\" style=\"font-size:12px;padding:3px 8px\">📋 Picking</button>',\n"
                "      '    <button class=\"btn\" onclick=\"window.allocRevertStep(\\'SOLD\\')\" style=\"font-size:11px;padding:2px 6px\" title=\"SOLD→PICKED 되돌리기\">↩ SOLD→PICKED</button>',\n"
                "      '    <button class=\"btn btn-secondary\" onclick=\"window._soldSearch()\" style=\"font-size:12px;padding:3px 6px\">🔁</button>',\n"
                "      '  </div>',\n"
                "      '</div>',\n"
            )
            src = src[:start_pos] + new_header + src[end_pos:]
            print("  ✅  [①] 헤더 날짜 필터 한 줄 교체")
            total += 1

    # ── ② apiGet 호출 교체 — 날짜 파라미터 포함 ─────────────────────
    OLD2 = "    apiGet('/api/q/sold-list').then(function(res){"
    NEW2 = (
        "    var _sf = document.getElementById('sold-date-from');\n"
        "    var _st = document.getElementById('sold-date-to');\n"
        "    var _sd = (_sf && _sf.value) ? '&start_date=' + _sf.value : '';\n"
        "    var _ed = (_st && _st.value) ? '&end_date='   + _st.value : '';\n"
        "    apiGet('/api/q/sold-list?limit=1000' + _sd + _ed).then(function(res){"
    )
    if OLD2 in src:
        src = src.replace(OLD2, NEW2, 1)
        print("  ✅  [②] apiGet 날짜 파라미터 추가")
        total += 1
    else:
        print("  ⚠️  [②] apiGet 패턴 미발견")

    # ── ③ 헬퍼 함수 추가 — loadOutboundPage 함수 바로 앞에 ──────────
    OLD3 = "  function loadOutboundPage() {"
    NEW3 = (
        "  /* ── SOLD 날짜 헬퍼 ── */\n"
        "  function _soldTodayStr() {\n"
        "    return new Date().toISOString().slice(0, 10);\n"
        "  }\n"
        "  window._soldSetToday = function() {\n"
        "    var t = _soldTodayStr();\n"
        "    var f = document.getElementById('sold-date-from');\n"
        "    var to = document.getElementById('sold-date-to');\n"
        "    if (f) f.value = t;\n"
        "    if (to) to.value = t;\n"
        "    window._soldSearch();\n"
        "  };\n"
        "  window._soldSetWeek = function() {\n"
        "    var now = new Date();\n"
        "    var mon = new Date(now);\n"
        "    mon.setDate(now.getDate() - ((now.getDay() + 6) % 7));\n"
        "    var f = document.getElementById('sold-date-from');\n"
        "    var to = document.getElementById('sold-date-to');\n"
        "    if (f)  f.value  = mon.toISOString().slice(0, 10);\n"
        "    if (to) to.value = _soldTodayStr();\n"
        "    window._soldSearch();\n"
        "  };\n"
        "  window._soldSetMonth = function() {\n"
        "    var now = new Date();\n"
        "    var first = new Date(now.getFullYear(), now.getMonth(), 1);\n"
        "    var f = document.getElementById('sold-date-from');\n"
        "    var to = document.getElementById('sold-date-to');\n"
        "    if (f)  f.value  = first.toISOString().slice(0, 10);\n"
        "    if (to) to.value = _soldTodayStr();\n"
        "    window._soldSearch();\n"
        "  };\n"
        "  window._soldSearch = function() {\n"
        "    var f  = document.getElementById('sold-date-from');\n"
        "    var to = document.getElementById('sold-date-to');\n"
        "    window._outboundDateFrom = f  ? f.value  : '';\n"
        "    window._outboundDateTo   = to ? to.value : '';\n"
        "    renderPage('outbound');\n"
        "  };\n"
        "\n"
        "  function loadOutboundPage() {"
    )
    if OLD3 in src:
        src = src.replace(OLD3, NEW3, 1)
        print("  ✅  [③] 헬퍼 함수 추가 (_soldSetToday/Week/Month/_soldSearch)")
        total += 1
    else:
        print("  ⚠️  [③] loadOutboundPage 앵커 미발견")

    # ── ④ 헤더 날짜 input 초기값: 저장된 날짜 복원 ──────────────────
    # loadOutboundPage 안에서 저장된 날짜를 읽어 input에 세팅
    OLD4 = "    var _outMode = window._outboundViewMode || 'lot';"
    NEW4 = (
        "    var _outMode    = window._outboundViewMode || 'lot';\n"
        "    var _initFrom   = window._outboundDateFrom || '';\n"
        "    var _initTo     = window._outboundDateTo   || '';"
    )
    if OLD4 in src:
        src = src.replace(OLD4, NEW4, 1)
        print("  ✅  [④] 저장된 날짜 복원 변수 추가")
        total += 1
    else:
        print("  ⚠️  [④] _outMode 초기화 패턴 미발견")

    # ── ⑤ input value를 저장된 날짜로 교체 ─────────────────────────
    OLD5a = "' + _soldTodayStr() + '\" style=\"font-size:11px;padding:2px 4px;border:1px solid var(--border);border-radius:4px;background:var(--panel);color:var(--text);width:114px;flex-shrink:0\">',"
    NEW5a = "' + (_initFrom || _soldTodayStr()) + '\" style=\"font-size:11px;padding:2px 4px;border:1px solid var(--border);border-radius:4px;background:var(--panel);color:var(--text);width:114px;flex-shrink:0\">',"
    OLD5b_idx = src.find(OLD5a)
    if OLD5b_idx != -1:
        src = src.replace(OLD5a, NEW5a, 1)
        # 두 번째 (sold-date-to)
        OLD5b = "' + _soldTodayStr() + '\" style=\"font-size:11px;padding:2px 4px;border:1px solid var(--border);border-radius:4px;background:var(--panel);color:var(--text);width:114px;flex-shrink:0\">',"
        NEW5b = "' + (_initTo   || _soldTodayStr()) + '\" style=\"font-size:11px;padding:2px 4px;border:1px solid var(--border);border-radius:4px;background:var(--panel);color:var(--text);width:114px;flex-shrink:0\">',"
        src = src.replace(OLD5b, NEW5b, 1)
        print("  ✅  [⑤] input 초기값 저장된 날짜 연결")
        total += 1
    else:
        print("  ⚠️  [⑤] input value 패턴 미발견")

    print(f"\n  📊 총 {total}/5 패치 적용")
    return src


def main():
    print("\n=== patch_sold_date_filter.py 시작 ===\n")
    src = TARGET.read_text(encoding="utf-8")
    backup(TARGET)
    patched = patch(src)
    if patched != src:
        TARGET.write_text(patched, encoding="utf-8")
        print("  💾  저장 완료")
    else:
        print("  ℹ️   변경 없음")
    print("\n=== 패치 완료 ===")


if __name__ == "__main__":
    main()
