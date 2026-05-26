#!/usr/bin/env python3
"""
patch_toolbar_uniform.py
목적: Pending / Available / Allocation / Picked 툴바를 SOLD 스타일 칩버튼 한 줄로 통일
적용: 2026-05-25
주의: sqm-inventory.js / sqm-allocation.js 는 CRLF → \r\n 사용
      sqm-picked.js 는 이미 적용됨
"""
import sys, os

BASE = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'js')

def crlf(s):
    """LF → CRLF 변환 헬퍼"""
    return s.replace('\n', '\r\n')

def patch(fname, patches, label):
    path = os.path.normpath(os.path.join(BASE, fname))
    with open(path, 'rb') as f:
        data = f.read()
    orig = data
    for i, (old_s, new_s) in enumerate(patches):
        old_b = old_s.encode('utf-8')
        new_b = new_s.encode('utf-8')
        if old_b not in data:
            print(f'[MISS {label} #{i+1}] 검색 실패')
            print('  앞 80바이트:', repr(old_b[:80]))
            continue
        data = data.replace(old_b, new_b, 1)
        print(f'[OK  {label} #{i+1}]')
    if data != orig:
        with open(path, 'wb') as f:
            f.write(data)
        print(f'[저장] {fname}')
    else:
        print(f'[SKIP] {fname} 변경 없음')

# ──────────────────────────────────────────────
#  1. sqm-inventory.js  (Pending + Available)  — CRLF
# ──────────────────────────────────────────────
INV_PATCHES = [
    # P1: _pendingModeBtn — border-color → border + border-radius, padding 4→3
    (
        crlf(
            "      ? 'background:var(--accent,#3b82f6);color:#fff;border-color:var(--accent,#3b82f6);'\n"
            "      : 'background:var(--surface,#1e293b);color:var(--text-muted);border-color:var(--border,#334155);';\n"
            "    return '<button class=\"btn\" style=\"font-size:12px;padding:4px 10px;' + active + '\" '\n"
            "      + 'onclick=\"window._pendingViewMode=\\'' + val + '\\';window.loadPendingPage()\">' + label + '</button>';"
        ),
        crlf(
            "      ? 'background:var(--accent,#3b82f6);color:#fff;border:1px solid var(--accent,#3b82f6);border-radius:4px;'\n"
            "      : 'background:var(--surface,#1e293b);color:var(--text-muted);border:1px solid var(--border,#334155);border-radius:4px;';\n"
            "    return '<button class=\"btn\" style=\"font-size:12px;padding:3px 10px;cursor:pointer;' + active + '\" '\n"
            "      + 'onclick=\"window._pendingViewMode=\\'' + val + '\\';window.loadPendingPage()\">' + label + '</button>';"
        )
    ),
    # P2: Pending 툴바 HTML 블록
    (
        crlf(
            "      var html = '<section style=\"padding:12px 16px\">'\n"
            "        + '<div style=\"display:flex;align-items:center;gap:8px;margin-bottom:8px;flex-wrap:wrap\">'\n"
            "        + '<h2 style=\"margin:0;font-size:16px;color:#94a3b8\">⏳ Pending — 포트 입항 대기 (참고용, 재고 미포함)</h2>'\n"
            "        + '<span style=\"font-size:12px;color:var(--text-muted)\">' + rows.length + ' LOT</span>'\n"
            "        + (window.SQMSummary ? window.SQMSummary.buildHeaderHTML(window.SQMSummary.compute(rows, {qtyField:function(r){return Number(r.net_weight||0)/1000;}, tonbagCountField:'mxbg_pallet'})) : '')\n"
            "        + '<div style=\"display:flex;gap:4px;margin-left:auto\">'\n"
            "        + _pendingModeBtn('date', '📅 도착일별', mode)\n"
            "        + _pendingModeBtn('container', '📦 컨테이너별', mode)\n"
            "        + _pendingModeBtn('lot', '🔢 LOT별', mode)\n"
            "        + '</div>'\n"
            "        + '<button class=\"btn btn-ghost\" style=\"font-size:12px\" onclick=\"window.loadPendingPage()\">🔄 새로고침</button>'\n"
            "        + '<button class=\"btn btn-secondary\" style=\"font-size:12px;padding:4px 12px\" onclick=\"window.exportPendingExcel()\" title=\"현재 화면 Pending 데이터를 Excel로 내보냅니다\">📊 Excel 내보내기</button>'\n"
            "        + '<button class=\"btn\" style=\"background:var(--accent,#3b82f6);color:#fff;font-size:12px;padding:4px 12px\" onclick=\"window.bulkConfirmPending()\">✅ 선택 일괄 확정</button>'\n"
            "        + '</div>';"
        ),
        crlf(
            "      var html = '<section style=\"padding:12px 16px\">'\n"
            "        + '<div style=\"display:flex;align-items:center;gap:6px;padding:8px 0 10px;flex-wrap:wrap\">'\n"
            "        + '<h2 style=\"margin:0;font-size:14px;white-space:nowrap;flex-shrink:0\">⏳ PENDING</h2>'\n"
            "        + '<span style=\"font-size:11px;color:var(--text-muted);flex-shrink:0\">그룹:</span>'\n"
            "        + _pendingModeBtn('date', '도착일별', mode)\n"
            "        + _pendingModeBtn('container', '컨테이너별', mode)\n"
            "        + _pendingModeBtn('lot', 'LOT별', mode)\n"
            "        + '<span style=\"flex:1\"></span>'\n"
            "        + '<button class=\"btn\" style=\"font-size:12px;padding:3px 10px;background:var(--accent,#3b82f6);color:#fff;border:1px solid var(--accent,#3b82f6);border-radius:4px\" onclick=\"window.bulkConfirmPending()\">✅ 일괄확정</button>'\n"
            "        + '<button class=\"btn\" style=\"font-size:12px;padding:3px 10px;border-radius:4px\" onclick=\"window.exportPendingExcel()\">📊 Excel</button>'\n"
            "        + '<button class=\"btn\" style=\"font-size:12px;padding:3px 10px;border-radius:4px\" onclick=\"window.loadPendingPage()\">🔄 새로고침</button>'\n"
            "        + '</div>';"
        )
    ),
    # P3: _availModeBtn — border-color → border + border-radius, padding 4→3
    (
        crlf(
            "      ? 'background:var(--accent,#3b82f6);color:#fff;border-color:var(--accent,#3b82f6);'\n"
            "      : 'background:var(--surface,#1e293b);color:var(--text-muted);border-color:var(--border,#334155);';\n"
            "    return '<button class=\"btn\" style=\"font-size:12px;padding:4px 10px;' + active + '\" '\n"
            "      + 'onclick=\"window._availViewMode=\\'' + val + '\\';window.loadAvailablePage()\">' + label + '</button>';"
        ),
        crlf(
            "      ? 'background:var(--accent,#3b82f6);color:#fff;border:1px solid var(--accent,#3b82f6);border-radius:4px;'\n"
            "      : 'background:var(--surface,#1e293b);color:var(--text-muted);border:1px solid var(--border,#334155);border-radius:4px;';\n"
            "    return '<button class=\"btn\" style=\"font-size:12px;padding:3px 10px;cursor:pointer;' + active + '\" '\n"
            "      + 'onclick=\"window._availViewMode=\\'' + val + '\\';window.loadAvailablePage()\">' + label + '</button>';"
        )
    ),
    # P4: Available 툴바 HTML 블록
    (
        crlf(
            "        + '<div style=\"display:flex;align-items:center;gap:12px;margin-bottom:8px;flex-wrap:wrap\">'\n"
            "        + '<h2 style=\"margin:0;font-size:16px;color:#22c55e\">✅ Available 재고 — 판매 가능 물량</h2>'\n"
            "        + '<span style=\"font-size:12px;color:var(--text-muted)\">' + rows.length + ' LOT · 📦 ' + fmtN(sumBal - sumSampleMt) + ' MT' + (sumSampleMt > 0 ? ' + 🧪 샘플 ' + fmtN(sumSampleMt) + ' MT' : '') + '</span>'\n"
            "        + '<button class=\"btn btn-ghost\" style=\"font-size:12px;margin-left:auto\" onclick=\"window.loadAvailablePage()\">🔄 새로고침</button>'\n"
            "        + '<button class=\"btn\" style=\"font-size:12px;padding:4px 10px;background:rgba(239,68,68,0.15);color:#ef4444;border:1px solid #ef444455\" onclick=\"window.availCancelSelected()\">↩️ 선택 취소(→PENDING)</button>'\n"
            "        + '<div style=\"display:flex;gap:4px\">' + _availModeBtn('lot','LOT별') + _availModeBtn('container','컨테이너별') + _availModeBtn('date','입고일별') + '</div>'\n"
            "        + '</div>'"
        ),
        crlf(
            "        + '<div style=\"display:flex;align-items:center;gap:6px;padding:8px 0 10px;flex-wrap:wrap\">'\n"
            "        + '<h2 style=\"margin:0;font-size:14px;white-space:nowrap;flex-shrink:0\">✅ AVAILABLE</h2>'\n"
            "        + '<span style=\"font-size:11px;color:var(--text-muted);flex-shrink:0\">그룹:</span>'\n"
            "        + _availModeBtn('lot','LOT별') + _availModeBtn('container','컨테이너별') + _availModeBtn('date','입고일별')\n"
            "        + '<span style=\"flex:1\"></span>'\n"
            "        + '<button class=\"btn\" style=\"font-size:12px;padding:3px 10px;background:rgba(239,68,68,0.15);color:#ef4444;border:1px solid #ef444455;border-radius:4px\" onclick=\"window.availCancelSelected()\">↩️ →PENDING</button>'\n"
            "        + '<button class=\"btn\" style=\"font-size:12px;padding:3px 10px;border-radius:4px\" onclick=\"window.loadAvailablePage()\">🔄 새로고침</button>'\n"
            "        + '</div>'"
        )
    ),
]

# ──────────────────────────────────────────────
#  2. sqm-allocation.js  (Allocation 헤더) — CRLF
# ──────────────────────────────────────────────
ALLOC_PATCHES = [
    (
        crlf(
            "      '<div class=\"alloc-header\" style=\"display:flex;align-items:center;gap:12px;padding:8px 0 8px\">',\n"
            "      '  <h2 style=\"margin:0\">📋 판매 배정 (Allocation)</h2>',\n"
            "      '  <span id=\"alloc-summary-label\" style=\"color:var(--text-muted);font-size:.9rem\"></span>',\n"
            "      '  <div style=\"margin-left:auto;display:flex;gap:6px;align-items:center\">',\n"
            "      '    <button class=\"btn btn-primary\" onclick=\"window.allocUploadExcel()\">📂 Excel 업로드</button>',\n"
            "      '    <button class=\"btn btn-secondary\" onclick=\"renderPage(\\'allocation\\')\">🔁 새로고침</button>',\n"
            "      '  </div>',\n"
            "      '</div>',"
        ),
        crlf(
            "      '<div class=\"alloc-header\" style=\"display:flex;align-items:center;gap:6px;padding:8px 0 10px;flex-wrap:wrap\">',\n"
            "      '  <h2 style=\"margin:0;font-size:14px;white-space:nowrap;flex-shrink:0\">📋 ALLOCATION</h2>',\n"
            "      '  <span id=\"alloc-summary-label\" style=\"font-size:11px;color:var(--text-muted)\"></span>',\n"
            "      '  <span style=\"flex:1\"></span>',\n"
            "      '  <button class=\"btn\" style=\"font-size:12px;padding:3px 10px;background:var(--accent,#3b82f6);color:#fff;border:1px solid var(--accent,#3b82f6);border-radius:4px\" onclick=\"window.allocUploadExcel()\">📂 Excel 업로드</button>',\n"
            "      '  <button class=\"btn\" style=\"font-size:12px;padding:3px 10px;border-radius:4px\" onclick=\"renderPage(\\'allocation\\')\">🔁 새로고침</button>',\n"
            "      '</div>',"
        )
    ),
]

patch('sqm-inventory.js',  INV_PATCHES,   'INV')
patch('sqm-allocation.js', ALLOC_PATCHES, 'ALLOC')
print('\n완료.')
