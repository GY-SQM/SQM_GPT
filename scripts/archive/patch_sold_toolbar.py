#!/usr/bin/env python3
"""
patch_sold_toolbar.py  (v8.6.9)
================================
SOLD 툴바 재설계:
  [출고 완료 (SOLD)]  [보기(현재모드) ▾]  [↩ SOLD→PICKED]
  보기 드롭다운: LOT별 / 컨테이너별 / BL별 / 고객사별 / 출고일별
  출고일별 서브: 오늘 / 이번주 / 이번달 / 기간 지정...
대상: frontend/js/sqm-logistics.js  (IIFE)
방식: bytes-level, 3 patches
"""
import sys, os, shutil, subprocess
from datetime import datetime

BASE   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(BASE, 'frontend', 'js', 'sqm-logistics.js')

def E(s): return s.encode('utf-8')

# ── Patch 1: 툴바 HTML (c.innerHTML 배열 안) ─────────────────
P1_OLD = E(
    "      '<div style=\"display:flex;align-items:center;gap:6px;flex-wrap:nowrap;padding:8px 0 10px;overflow-x:auto\">',"
    "\n      '  <h2 style=\"margin:0;white-space:nowrap;font-size:15px\">📤 출고 완료 (SOLD)</h2>',"
    "\n      '  <div style=\"display:flex;gap:3px;flex-shrink:0\">' +"
    "\n         _outboundModeBtn('lot', 'LOT별', _outMode) +"
    "\n         _outboundModeBtn('customer', '고객사별', _outMode) +"
    "\n         _outboundModeBtn('date', '출고일별', _outMode) +"
    "\n      '  </div>',"
    "\n      '  <span style=\"width:1px;height:20px;background:var(--border);margin:0 2px;flex-shrink:0\"></span>',"
    "\n      '  <input type=\"date\" id=\"sold-date-from\" value=\"' + (_initFrom || _soldTodayStr()) + '\"'"
    "\n        + ' style=\"font-size:11px;padding:2px 4px;border:1px solid var(--border);border-radius:4px;background:var(--panel);color:var(--text);width:114px;flex-shrink:0\">',"
    "\n      '  <span style=\"font-size:12px;color:var(--text-muted);flex-shrink:0\">~</span>',"
    "\n      '  <input type=\"date\" id=\"sold-date-to\" value=\"' + (_initTo   || _soldTodayStr()) + '\"'"
    "\n        + ' style=\"font-size:11px;padding:2px 4px;border:1px solid var(--border);border-radius:4px;background:var(--panel);color:var(--text);width:114px;flex-shrink:0\">',"
    "\n      '  <button class=\"btn\" onclick=\"window._soldSetToday()\" style=\"font-size:11px;padding:2px 6px;flex-shrink:0\">오늘</button>',"
    "\n      '  <button class=\"btn\" onclick=\"window._soldSetWeek()\"  style=\"font-size:11px;padding:2px 6px;flex-shrink:0\">이번주</button>',"
    "\n      '  <button class=\"btn\" onclick=\"window._soldSetMonth()\" style=\"font-size:11px;padding:2px 6px;flex-shrink:0\">이번달</button>',"
    "\n      '  <button class=\"btn btn-primary\" onclick=\"window._soldSearch()\" style=\"font-size:11px;padding:2px 8px;font-weight:700;flex-shrink:0\">조회</button>',"
    "\n      '  <span style=\"width:1px;height:20px;background:var(--border);margin:0 2px;flex-shrink:0\"></span>',"
    "\n      '  <div style=\"display:flex;gap:5px;align-items:center;flex-shrink:0\">',"
    "\n      '    <button class=\"btn btn-primary\" onclick=\"window.showOutboundPickingModal()\" style=\"font-size:12px;padding:3px 8px\">📋 Picking</button>',"
    "\n      '    <button class=\"btn\" onclick=\"window.allocRevertStep(\\'SOLD\\')\" style=\"font-size:11px;padding:2px 6px\" title=\"SOLD→PICKED 되돌리기\">↩ SOLD→PICKED</button>',"
    "\n      '    <button class=\"btn btn-secondary\" onclick=\"window._soldSearch()\" style=\"font-size:12px;padding:3px 6px\">🔁</button>',"
    "\n      '  </div>',"
    "\n      '</div>',"
)

P1_NEW = E(
    "      '<div style=\"display:flex;align-items:center;gap:8px;flex-wrap:nowrap;padding:8px 0 10px\">',"
    "\n      '  <h2 style=\"margin:0;white-space:nowrap;font-size:15px\">📤 출고 완료 (SOLD)</h2>',"
    "\n      '  ' + _soldViewMenuHtml(_outMode) + '',"
    "\n      '  <span style=\"width:1px;height:20px;background:var(--border);margin:0 4px;flex-shrink:0\"></span>',"
    "\n      '  <button class=\"btn\" onclick=\"window.allocRevertStep(\\'SOLD\\')\" style=\"font-size:11px;padding:2px 8px;flex-shrink:0\" title=\"SOLD→PICKED 되돌리기\">↩ SOLD→PICKED</button>',"
    "\n      '</div>',"
    "\n      '<div id=\"sold-date-range-bar\" style=\"' + (_outMode==='date' ? 'display:flex' : 'display:none') + ';align-items:center;gap:6px;padding:0 0 8px;flex-wrap:nowrap\">',"
    "\n      '  <span style=\"font-size:12px;color:var(--text-muted);flex-shrink:0\">출고일 기간:</span>',"
    "\n      '  <input type=\"date\" id=\"sold-date-from\" value=\"' + (_initFrom || _soldTodayStr()) + '\"'"
    "\n        + ' onchange=\"window._outboundDateFrom=this.value\"'"
    "\n        + ' style=\"font-size:11px;padding:2px 4px;border:1px solid var(--border);border-radius:4px;background:var(--panel);color:var(--text);width:114px;flex-shrink:0\">',"
    "\n      '  <span style=\"font-size:12px;color:var(--text-muted);flex-shrink:0\">~</span>',"
    "\n      '  <input type=\"date\" id=\"sold-date-to\" value=\"' + (_initTo || _soldTodayStr()) + '\"'"
    "\n        + ' onchange=\"window._outboundDateTo=this.value\"'"
    "\n        + ' style=\"font-size:11px;padding:2px 4px;border:1px solid var(--border);border-radius:4px;background:var(--panel);color:var(--text);width:114px;flex-shrink:0\">',"
    "\n      '  <button class=\"btn btn-primary\" onclick=\"window._soldSearch()\" style=\"font-size:11px;padding:2px 8px;font-weight:700;flex-shrink:0\">조회</button>',"
    "\n      '</div>',"
)

# ── Patch 2: 그룹 렌더링에 container/bl 모드 추가 ────────────
P2_OLD = E(
    "      // v868 fix (2026-05-16): 그룹 모드 분기 — 고객사별/출고일별"
    "\n      if (_outMode === 'customer' || _outMode === 'date') {"
    "\n        var tbl = document.getElementById('outbound-table');"
    "\n        if (tbl) tbl.style.display = 'none';"
    "\n        var groupHtml;"
    "\n        if (_outMode === 'customer') {"
    "\n          groupHtml = _renderOutboundGroup(rows, function(r){ return r.customer || ''; }, '고객사: ', 'oc');"
    "\n        } else {"
    "\n          groupHtml = _renderOutboundGroup(rows, function(r){ return (r.sold_date || '').slice(0,10); }, '출고일: ', 'od');"
    "\n        }"
)

P2_NEW = E(
    "      // v869: 그룹 모드 분기 — container/bl/customer/date"
    "\n      if (_outMode === 'customer' || _outMode === 'date' || _outMode === 'container' || _outMode === 'bl') {"
    "\n        var tbl = document.getElementById('outbound-table');"
    "\n        if (tbl) tbl.style.display = 'none';"
    "\n        var groupHtml;"
    "\n        if (_outMode === 'customer') {"
    "\n          groupHtml = _renderOutboundGroup(rows, function(r){ return r.customer || '(미지정)'; }, '고객사: ', 'oc');"
    "\n        } else if (_outMode === 'container') {"
    "\n          groupHtml = _renderOutboundGroup(rows, function(r){ return r.container_no || '(CT 미지정)'; }, '컨테이너: ', 'cn');"
    "\n        } else if (_outMode === 'bl') {"
    "\n          groupHtml = _renderOutboundGroup(rows, function(r){ return r.bl_no || '(BL 미지정)'; }, 'BL: ', 'bl');"
    "\n        } else {"
    "\n          groupHtml = _renderOutboundGroup(rows, function(r){ return (r.sold_date || '').slice(0,10); }, '출고일: ', 'od');"
    "\n        }"
)

# ── Patch 3: _outboundModeBtn 앞에 _soldViewMenuHtml 헬퍼 삽입 ─
P3_OLD = E("  function _outboundModeBtn(val, label, cur) {")

P3_NEW = E(
    "  /* v869: SOLD 보기 드롭다운 헬퍼 ────────────────────────── */\n"
    "  function _soldViewMenuHtml(curMode) {\n"
    "    var labels = { lot: 'LOT별', container: '컨테이너별', bl: 'BL별', customer: '고객사별', date: '출고일별' };\n"
    "    var curLabel = labels[curMode] || 'LOT별';\n"
    "    function mi(val, icon, label) {\n"
    "      var isAct = curMode === val;\n"
    "      var actS = isAct ? 'background:rgba(59,130,246,.15);color:var(--accent);font-weight:700;' : 'color:var(--text);';\n"
    "      var leaveS = isAct ? 'rgba(59,130,246,.15)' : 'none';\n"
    "      return '<button style=\"display:block;width:100%;text-align:left;padding:7px 14px;background:none;border:none;cursor:pointer;font-size:13px;' + actS + '\"'\n"
    "        + ' onmouseenter=\"this.style.background=\\'rgba(59,130,246,.10)\\'\"'\n"
    "        + ' onmouseleave=\"this.style.background=\\'' + leaveS + '\\'\"'\n"
    "        + ' onclick=\"window._outboundViewMode=\\'' + val + '\\';window._closeSoldViewMenu();'\n"
    "        + (val === 'date' ? 'window._soldSetMonth();' : 'window._soldSearch();') + '\">'\n"
    "        + icon + '\\u00a0' + label + '</button>';\n"
    "    }\n"
    "    var subBtn = function(label, action) {\n"
    "      return '<button style=\"display:block;width:100%;text-align:left;padding:5px 14px 5px 26px;background:none;border:none;cursor:pointer;font-size:12px;color:var(--text-muted)\"'\n"
    "        + ' onmouseenter=\"this.style.color=\\'var(--accent)\\'\"'\n"
    "        + ' onmouseleave=\"this.style.color=\\'var(--text-muted)\\'\"'\n"
    "        + ' onclick=\"window._outboundViewMode=\\'date\\';window._closeSoldViewMenu();' + action + '\">' + label + '</button>';\n"
    "    };\n"
    "    var dateSect =\n"
    "      '<div style=\"border-top:1px solid var(--border);margin:4px 0 2px\">'\n"
    "      + '<div style=\"padding:5px 14px 2px;font-size:11px;color:var(--text-muted);text-transform:uppercase;letter-spacing:.05em\">출고일별</div>'\n"
    "      + subBtn('오늘', 'window._soldSetToday();')\n"
    "      + subBtn('이번주', 'window._soldSetWeek();')\n"
    "      + subBtn('이번달', 'window._soldSetMonth();')\n"
    "      + subBtn('기간 지정...', 'window._showSoldDateRange();window._soldSearch();')\n"
    "      + '</div>';\n"
    "    var menu =\n"
    "      '<div id=\"sold-view-menu\" style=\"display:none;position:absolute;top:calc(100% + 4px);left:0;z-index:9999;'\n"
    "      + 'background:var(--panel,#1e293b);border:1px solid var(--border,#334155);border-radius:7px;'\n"
    "      + 'min-width:165px;box-shadow:0 6px 20px rgba(0,0,0,.35);padding:4px 0\">'\n"
    "      + mi('lot', '📦', 'LOT별')\n"
    "      + mi('container', '🚢', '컨테이너별')\n"
    "      + mi('bl', '📄', 'BL별')\n"
    "      + mi('customer', '🏢', '고객사별')\n"
    "      + dateSect\n"
    "      + '</div>';\n"
    "    return '<div style=\"position:relative;display:inline-block;flex-shrink:0\">'\n"
    "      + '<button class=\"btn btn-primary\" style=\"font-size:13px;padding:4px 12px;font-weight:600\" onclick=\"window._soldViewToggle(event)\">보기 (' + curLabel + ') ▾</button>'\n"
    "      + menu\n"
    "      + '</div>';\n"
    "  }\n"
    "  window._soldViewToggle = function(e) {\n"
    "    e.stopPropagation();\n"
    "    var m = document.getElementById('sold-view-menu');\n"
    "    if (!m) return;\n"
    "    m.style.display = (m.style.display === 'none' || !m.style.display) ? 'block' : 'none';\n"
    "  };\n"
    "  window._closeSoldViewMenu = function() {\n"
    "    var m = document.getElementById('sold-view-menu');\n"
    "    if (m) m.style.display = 'none';\n"
    "  };\n"
    "  window._showSoldDateRange = function() {\n"
    "    var bar = document.getElementById('sold-date-range-bar');\n"
    "    if (bar) { bar.style.display = 'flex'; }\n"
    "  };\n"
    "  document.addEventListener('click', function() {\n"
    "    if (window._closeSoldViewMenu) window._closeSoldViewMenu();\n"
    "  });\n"
    "\n"
    "  function _outboundModeBtn(val, label, cur) {"
)

def apply(data, old, new_, tag):
    if old in data:
        return data.replace(old, new_, 1), 'LF'
    old_cr = old.replace(b'\n', b'\r\n')
    new_cr = new_.replace(b'\n', b'\r\n')
    if old_cr in data:
        return data.replace(old_cr, new_cr, 1), 'CRLF'
    return None, None

def main():
    if not os.path.exists(TARGET):
        print(f"❌ 파일 없음: {TARGET}"); sys.exit(1)

    with open(TARGET, 'rb') as f:
        data = f.read()

    if b'_soldViewMenuHtml' in data:
        print("ℹ️  이미 적용됨 — 스킵"); return

    bak = TARGET + '.bak_toolbar_' + datetime.now().strftime('%Y%m%d_%H%M%S')
    shutil.copy2(TARGET, bak)
    print(f"📦 백업: {bak}")

    # Patch 3 (헬퍼 추가) 먼저
    data, m3 = apply(data, P3_OLD, P3_NEW, 'P3')
    if data is None:
        print("❌ P3 앵커 없음 (_outboundModeBtn)")
        sys.exit(1)
    print(f"✅ P3 ({m3}): _soldViewMenuHtml 헬퍼 + 이벤트 추가")

    # Patch 1: 툴바 HTML
    data, m1 = apply(data, P1_OLD, P1_NEW, 'P1')
    if data is None:
        print("❌ P1 앵커 없음 (툴바 HTML)")
        idx = data.find(b'sold-date-from') if data else -1
        print(f"  sold-date-from @ {idx}")
        sys.exit(1)
    print(f"✅ P1 ({m1}): 툴바 HTML 재설계")

    # Patch 2: 그룹 렌더링
    data, m2 = apply(data, P2_OLD, P2_NEW, 'P2')
    if data is None:
        print("❌ P2 앵커 없음 (그룹 렌더링)")
        sys.exit(1)
    print(f"✅ P2 ({m2}): container/bl 그룹 모드 추가")

    with open(TARGET, 'wb') as f:
        f.write(data)
    print(f"💾 저장 완료 ({len(data)} bytes)")

    r = subprocess.run(['node', '--check', TARGET], capture_output=True, text=True)
    if r.returncode == 0:
        print("✅ node --check 통과")
    else:
        print("❌ node --check 실패 — 백업 복원")
        print(r.stderr[:800])
        shutil.copy2(bak, TARGET)
        sys.exit(1)

if __name__ == '__main__':
    main()
