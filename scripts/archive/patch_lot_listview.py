"""
patch_lot_listview.py  (v8.6.9)
LOT 리스트 화면 3가지 기능 추가 패치

① 컬럼 헤더 오름/내림차순 정렬 (sqm-listview.js)
② 하단 요약바 노란 배경 + 큰 폰트 (sqm-listview.js)
③ 톤백 = regular_bags + sample_bags 분리 표시 (actions.py + sqm-listview.js)

실행: python scripts/patch_lot_listview.py
"""
import re, sys, pathlib, shutil, datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent
ACTIONS = ROOT / "backend" / "api" / "actions.py"
LISTVIEW = ROOT / "frontend" / "js" / "sqm-listview.js"

TS = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def backup(p: pathlib.Path):
    bak = p.with_suffix(p.suffix + f".bak_lotpatch_{TS}")
    shutil.copy2(p, bak)
    print(f"  📦 백업: {bak.name}")


def patch_actions(src: str) -> str:
    """
    lot_list_json() 함수 안에서 inventory_tonbag 집계를 추가하고
    regular_bags / sample_bags 를 JSON 응답에 포함
    """
    OLD = (
        "        rows = _append_lot_candidate_summary(rows, con)\n"
        "        con.close()\n"
        "        data = []\n"
        "        for r in rows:\n"
        "            data.append({k: r[i] for i, k in enumerate(_LOT_LIST_JSON_HEADERS)})\n"
        "        return ok_response({\"rows\": data, \"count\": len(data),\n"
        "                            \"headers\": _LOT_LIST_JSON_HEADERS})"
    )
    NEW = (
        "        rows = _append_lot_candidate_summary(rows, con)\n"
        "        # v8.6.9: 톤백 regular/sample 분리 집계\n"
        "        try:\n"
        "            tb_summary = con.execute(\"\"\"\n"
        "                SELECT lot_no,\n"
        "                       SUM(CASE WHEN COALESCE(is_sample,0)=0 THEN 1 ELSE 0 END),\n"
        "                       SUM(CASE WHEN COALESCE(is_sample,0)=1 THEN 1 ELSE 0 END)\n"
        "                  FROM inventory_tonbag\n"
        "                 GROUP BY lot_no\n"
        "            \"\"\").fetchall()\n"
        "            tb_map = {r[0]: (int(r[1] or 0), int(r[2] or 0)) for r in tb_summary}\n"
        "        except Exception:\n"
        "            tb_map = {}\n"
        "        con.close()\n"
        "        data = []\n"
        "        for r in rows:\n"
        "            d = {k: r[i] for i, k in enumerate(_LOT_LIST_JSON_HEADERS)}\n"
        "            reg, smp = tb_map.get(d.get('lot_no', ''), (0, 0))\n"
        "            d['regular_bags'] = reg\n"
        "            d['sample_bags']  = smp\n"
        "            data.append(d)\n"
        "        return ok_response({\"rows\": data, \"count\": len(data),\n"
        "                            \"headers\": _LOT_LIST_JSON_HEADERS + [\"regular_bags\", \"sample_bags\"]})"
    )
    if OLD not in src:
        print("  ⚠️  actions.py: 대상 패턴 미발견 — 이미 패치됐거나 코드가 변경됨")
        return src
    result = src.replace(OLD, NEW, 1)
    print("  ✅  actions.py: lot_list_json() regular_bags/sample_bags 추가")
    return result


def patch_listview(src: str) -> str:
    """
    sqm-listview.js 3곳 수정:
    A. 모듈 레벨 sort 상태 변수 추가
    B. _renderTable 헤더에 정렬 클릭 기능 추가
    C. _renderLotFooter 스타일 + 톤백/샘플 분리
    """

    # ── A. sort 상태 변수 ──────────────────────────────────────────────
    OLD_A = "  /* ── 공통 모달 ── */\n  var _modalEl = null;"
    NEW_A = (
        "  /* ── sort 상태 (모듈 레벨) ── */\n"
        "  var _lvAllRows   = [];   // 현재 모달의 전체 행 캐시\n"
        "  var _lvCols      = [];   // 현재 컬럼 정의\n"
        "  var _lvOnClick   = null; // 행 클릭 핸들러\n"
        "  var _lvSortKey   = '';   // 현재 정렬 컬럼 key\n"
        "  var _lvSortDir   = 1;    // 1=오름, -1=내림\n"
        "  var _lvFootFn    = null; // 현재 footer 렌더 함수\n"
        "  var _lvFootEl    = null; // footer DOM 요소\n\n"
        "  /* ── 공통 모달 ── */\n"
        "  var _modalEl = null;"
    )

    if OLD_A not in src:
        print("  ⚠️  sqm-listview.js(A): sort 변수 패턴 미발견")
    else:
        src = src.replace(OLD_A, NEW_A, 1)
        print("  ✅  sqm-listview.js(A): sort 상태 변수 추가")

    # ── B. _renderTable 헤더 정렬 기능 ────────────────────────────────
    OLD_B = (
        "  function _renderTable(cols, rows, container, onRowClick) {\n"
        "    if (!rows || rows.length === 0) {\n"
        "      container.innerHTML = '<div style=\"text-align:center;color:var(--text-muted);padding:40px;\">📭 데이터가 없습니다.</div>';\n"
        "      return;\n"
        "    }\n"
        "    var thead = cols.map(function(c) {\n"
        "      var align = c.align ? 'text-align:' + c.align + ';' : '';\n"
        "      return '<th style=\"padding:6px 8px;background:var(--bg-hover);color:var(--accent);'\n"
        "        + 'font-size:11px;font-weight:700;border-bottom:2px solid var(--accent);'\n"
        "        + 'position:sticky;top:0;z-index:1;white-space:nowrap;' + align\n"
        "        + (c.w ? 'min-width:' + c.w + 'px;' : '') + '\">' + _esc(c.h) + '</th>';\n"
        "    }).join('');"
    )
    NEW_B = (
        "  /* v8.6.9: sort helper */\n"
        "  function _sortRows(rows, key, dir) {\n"
        "    return rows.slice().sort(function(a, b) {\n"
        "      var va = a[key], vb = b[key];\n"
        "      if (va == null) va = '';\n"
        "      if (vb == null) vb = '';\n"
        "      var na = Number(va), nb = Number(vb);\n"
        "      if (!isNaN(na) && !isNaN(nb)) return (na - nb) * dir;\n"
        "      return String(va).localeCompare(String(vb), 'ko') * dir;\n"
        "    });\n"
        "  }\n\n"
        "  function _renderTable(cols, rows, container, onRowClick) {\n"
        "    /* v8.6.9: 모듈 레벨 캐시 갱신 */\n"
        "    _lvCols    = cols;\n"
        "    _lvOnClick = onRowClick || null;\n"
        "    if (!rows || rows.length === 0) {\n"
        "      container.innerHTML = '<div style=\"text-align:center;color:var(--text-muted);padding:40px;\">📭 데이터가 없습니다.</div>';\n"
        "      return;\n"
        "    }\n"
        "    /* v8.6.9: 정렬 적용 */\n"
        "    var displayRows = (_lvSortKey)\n"
        "      ? _sortRows(rows, _lvSortKey, _lvSortDir)\n"
        "      : rows;\n"
        "    var thead = cols.map(function(c) {\n"
        "      var align = c.align ? 'text-align:' + c.align + ';' : '';\n"
        "      var isActive = (c.k === _lvSortKey);\n"
        "      var arrow = isActive ? (_lvSortDir === 1 ? ' ▲' : ' ▼') : ' ⇅';\n"
        "      var arrowColor = isActive ? 'color:#FFD700;' : 'color:rgba(255,255,255,0.3);';\n"
        "      return '<th data-sort-key=\"' + _esc(c.k) + '\" '\n"
        "        + 'style=\"padding:6px 8px;background:var(--bg-hover);color:var(--accent);'\n"
        "        + 'font-size:11px;font-weight:700;border-bottom:2px solid var(--accent);'\n"
        "        + 'position:sticky;top:0;z-index:1;white-space:nowrap;cursor:pointer;'\n"
        "        + 'user-select:none;' + align\n"
        "        + (c.w ? 'min-width:' + c.w + 'px;' : '') + '\">'\n"
        "        + _esc(c.h)\n"
        "        + '<span style=\"font-size:9px;margin-left:2px;' + arrowColor + '\">' + arrow + '</span>'\n"
        "        + '</th>';\n"
        "    }).join('');"
    )

    # tbody 부분도 rows → displayRows 로 교체
    OLD_B2 = (
        "    var clickable = (typeof onRowClick === 'function');\n"
        "    var tbody = rows.map(function(r, ri) {"
    )
    NEW_B2 = (
        "    var clickable = (typeof onRowClick === 'function');\n"
        "    var tbody = displayRows.map(function(r, ri) {"
    )

    # onRowClick 도 displayRows 기반으로
    OLD_B3 = (
        "        tr.addEventListener('click', function() {\n"
        "          var idx = parseInt(tr.dataset.rowIdx, 10);\n"
        "          onRowClick(rows[idx]);\n"
        "        });"
    )
    NEW_B3 = (
        "        tr.addEventListener('click', function() {\n"
        "          var idx = parseInt(tr.dataset.rowIdx, 10);\n"
        "          onRowClick(displayRows[idx]);\n"
        "        });"
    )

    # 헤더 클릭 → 정렬 이벤트 추가 (container.innerHTML 설정 직후)
    OLD_B4 = (
        "    /* v8.6.9: 행 클릭 핸들러 (drilldown) */\n"
        "    if (clickable) {"
    )
    NEW_B4 = (
        "    /* v8.6.9: 헤더 클릭 → 정렬 */\n"
        "    container.querySelectorAll('thead th[data-sort-key]').forEach(function(th) {\n"
        "      th.addEventListener('click', function() {\n"
        "        var key = th.dataset.sortKey;\n"
        "        if (_lvSortKey === key) {\n"
        "          _lvSortDir = _lvSortDir * -1;\n"
        "        } else {\n"
        "          _lvSortKey = key;\n"
        "          _lvSortDir = 1;\n"
        "        }\n"
        "        /* 현재 컨테이너의 allRows 는 부모 스코프에 없으므로\n"
        "           container 에 저장된 전체 행 캐시를 재활용 */\n"
        "        var body = document.getElementById('sqm-listview-body');\n"
        "        var foot = document.getElementById('sqm-listview-foot');\n"
        "        _renderTable(_lvCols, _lvAllRows, body, _lvOnClick);\n"
        "        if (_lvFootFn && foot) _lvFootFn(foot, _lvAllRows);\n"
        "      });\n"
        "    });\n"
        "    /* v8.6.9: 행 클릭 핸들러 (drilldown) */\n"
        "    if (clickable) {"
    )

    if OLD_B not in src:
        print("  ⚠️  sqm-listview.js(B): _renderTable 헤더 패턴 미발견")
    else:
        src = src.replace(OLD_B, NEW_B, 1)
        print("  ✅  sqm-listview.js(B-1): _renderTable 헤더 정렬 추가")

    if OLD_B2 not in src:
        print("  ⚠️  sqm-listview.js(B-2): tbody rows 패턴 미발견")
    else:
        src = src.replace(OLD_B2, NEW_B2, 1)
        print("  ✅  sqm-listview.js(B-2): tbody displayRows 교체")

    if OLD_B3 not in src:
        print("  ⚠️  sqm-listview.js(B-3): onRowClick rows[idx] 패턴 미발견")
    else:
        src = src.replace(OLD_B3, NEW_B3, 1)
        print("  ✅  sqm-listview.js(B-3): onRowClick displayRows[idx] 교체")

    if OLD_B4 not in src:
        print("  ⚠️  sqm-listview.js(B-4): 헤더 클릭 이벤트 삽입 패턴 미발견")
    else:
        src = src.replace(OLD_B4, NEW_B4, 1)
        print("  ✅  sqm-listview.js(B-4): 헤더 클릭 sort 이벤트 삽입")

    # ── C. _renderLotFooter: 노란 배경 + 큰 폰트 + 톤백/샘플 분리 ────
    OLD_C = (
        "  /* -- LOT footer totals bar ---------------------------------------- */\n"
        "  function _renderLotFooter(foot, rows) {\n"
        "    var totalNet = 0, totalCur = 0, totalTonbag = 0;\n"
        "    rows.forEach(function(r) {\n"
        "      totalNet    += Number(r.net_weight     || 0);\n"
        "      totalCur    += Number(r.current_weight || 0);\n"
        "      totalTonbag += Number(r.tonbag_count   || 0);\n"
        "    });\n"
        "    var s = 'display:inline-block;padding:2px 14px;margin-right:8px;'\n"
        "          + 'background:rgba(79,195,247,0.13);border-radius:6px;'\n"
        "          + 'font-size:12px;color:var(--accent,#4fc3f7);font-weight:700;';\n"
        "    var hint = 'font-size:11px;color:var(--text-muted);margin-left:6px;';\n"
        "    foot.innerHTML =\n"
        "        '<span style=\"' + s + '\">📦 LOT ' + rows.length.toLocaleString('ko-KR') + ' 건</span>'\n"
        "      + '<span style=\"' + s + '\">⚖ 순중량 ' + totalNet.toLocaleString('ko-KR', {maximumFractionDigits:2}) + ' kg</span>'\n"
        "      + '<span style=\"' + s + '\">📊 현재 ' + totalCur.toLocaleString('ko-KR', {maximumFractionDigits:2}) + ' kg</span>'\n"
        "      + '<span style=\"' + s + '\">🎒 톤백 ' + totalTonbag.toLocaleString('ko-KR') + ' 개</span>'\n"
        "      + '<span style=\"' + hint + '\">※ 행 클릭 → 톤백 상세 보기 · 엑셀 다운로드는 우상단 버튼</span>';\n"
        "  }"
    )
    NEW_C = (
        "  /* -- LOT footer totals bar (v8.6.9: 노란배경·큰폰트·톤백/샘플 분리) -- */\n"
        "  function _renderLotFooter(foot, rows) {\n"
        "    /* v8.6.9: 모듈 레벨 캐시에 footer 함수 등록 */\n"
        "    _lvFootFn = _renderLotFooter;\n"
        "    _lvFootEl = foot;\n"
        "    var totalNet = 0, totalCur = 0, totalReg = 0, totalSmp = 0;\n"
        "    rows.forEach(function(r) {\n"
        "      totalNet += Number(r.net_weight     || 0);\n"
        "      totalCur += Number(r.current_weight || 0);\n"
        "      totalReg += Number(r.regular_bags   || 0);\n"
        "      totalSmp += Number(r.sample_bags    || 0);\n"
        "    });\n"
        "    /* 노란 배경 강조 스타일 */\n"
        "    var s = 'display:inline-block;padding:4px 18px;margin-right:10px;'\n"
        "          + 'background:#FFD600;border-radius:8px;'\n"
        "          + 'font-size:14px;color:#222;font-weight:800;'\n"
        "          + 'box-shadow:0 1px 4px rgba(0,0,0,.25);';\n"
        "    var hint = 'font-size:11px;color:var(--text-muted);margin-left:4px;';\n"
        "    /* 톤백 분리: regular + sample */\n"
        "    var tbStr = totalReg > 0 || totalSmp > 0\n"
        "      ? totalReg.toLocaleString('ko-KR') + '개 + 🧪 샘플 ' + totalSmp.toLocaleString('ko-KR') + '개'\n"
        "      : (totalReg + totalSmp).toLocaleString('ko-KR') + '개';\n"
        "    foot.innerHTML =\n"
        "        '<span style=\"' + s + '\">📦 LOT ' + rows.length.toLocaleString('ko-KR') + ' 건</span>'\n"
        "      + '<span style=\"' + s + '\">⚖ 순중량 ' + totalNet.toLocaleString('ko-KR', {maximumFractionDigits:2}) + ' kg</span>'\n"
        "      + '<span style=\"' + s + '\">📊 현재 ' + totalCur.toLocaleString('ko-KR', {maximumFractionDigits:2}) + ' kg</span>'\n"
        "      + '<span style=\"' + s + '\">🧱 톤백 ' + tbStr + '</span>'\n"
        "      + '<span style=\"' + hint + '\">※ 행 클릭 → 톤백 상세 보기 · 엑셀 다운로드는 우상단 버튼</span>';\n"
        "  }"
    )

    if OLD_C not in src:
        print("  ⚠️  sqm-listview.js(C): _renderLotFooter 패턴 미발견")
    else:
        src = src.replace(OLD_C, NEW_C, 1)
        print("  ✅  sqm-listview.js(C): _renderLotFooter 노란배경+분리 표시")

    # ── D. showLotListModal: _lvAllRows 갱신 + sort 초기화 ───────────
    OLD_D = (
        "          var rows = (res && res.data && res.data.rows) || res.rows || [];\n"
        "          allRows = rows;\n"
        "          cnt.textContent = '— ' + rows.length + ' 건';\n"
        "          _renderTable(LOT_COLS, rows, body, _onLotRowClick);\n"
        "          _renderLotFooter(foot, rows);"
    )
    NEW_D = (
        "          var rows = (res && res.data && res.data.rows) || res.rows || [];\n"
        "          allRows = rows;\n"
        "          _lvAllRows  = rows;   /* v8.6.9: sort 캐시 */\n"
        "          _lvSortKey  = '';     /* sort 초기화 */\n"
        "          _lvSortDir  = 1;\n"
        "          cnt.textContent = '— ' + rows.length + ' 건';\n"
        "          _renderTable(LOT_COLS, rows, body, _onLotRowClick);\n"
        "          _renderLotFooter(foot, rows);"
    )

    if OLD_D not in src:
        print("  ⚠️  sqm-listview.js(D): showLotListModal allRows 패턴 미발견")
    else:
        src = src.replace(OLD_D, NEW_D, 1)
        print("  ✅  sqm-listview.js(D): showLotListModal _lvAllRows 갱신")

    # ── E. fInp.oninput 에서도 _lvAllRows 갱신 ───────────────────────
    OLD_E = (
        "    fInp.oninput = function() {\n"
        "      var _lotFiltered = _applyFilter(allRows, this.value);\n"
        "      _renderTable(LOT_COLS, _lotFiltered, body, _onLotRowClick);\n"
        "      _renderLotFooter(foot, _lotFiltered);\n"
        "    };"
    )
    NEW_E = (
        "    fInp.oninput = function() {\n"
        "      var _lotFiltered = _applyFilter(allRows, this.value);\n"
        "      _lvAllRows = _lotFiltered;  /* v8.6.9: 필터 후 sort 캐시 갱신 */\n"
        "      _lvSortKey = '';            /* 필터 변경 시 sort 초기화 */\n"
        "      _renderTable(LOT_COLS, _lotFiltered, body, _onLotRowClick);\n"
        "      _renderLotFooter(foot, _lotFiltered);\n"
        "    };"
    )

    if OLD_E not in src:
        print("  ⚠️  sqm-listview.js(E): fInp.oninput LOT 패턴 미발견")
    else:
        src = src.replace(OLD_E, NEW_E, 1)
        print("  ✅  sqm-listview.js(E): fInp.oninput _lvAllRows 갱신")

    return src


def main():
    print("\n=== patch_lot_listview.py 시작 ===\n")

    # ── actions.py ───────────────────────────────────────────────────
    print("[1/2] actions.py 패치")
    src = ACTIONS.read_text(encoding="utf-8")
    backup(ACTIONS)
    patched = patch_actions(src)
    if patched != src:
        ACTIONS.write_text(patched, encoding="utf-8")
        print("  💾  actions.py 저장 완료\n")
    else:
        print("  ℹ️   변경 없음\n")

    # ── sqm-listview.js ──────────────────────────────────────────────
    print("[2/2] sqm-listview.js 패치")
    src = LISTVIEW.read_text(encoding="utf-8")
    backup(LISTVIEW)
    patched = patch_listview(src)
    if patched != src:
        LISTVIEW.write_text(patched, encoding="utf-8")
        print("  💾  sqm-listview.js 저장 완료\n")
    else:
        print("  ℹ️   변경 없음\n")

    print("=== 패치 완료 ===")
    print("다음: python scripts/patch_lot_listview.py 실행 후 앱 재시작")


if __name__ == "__main__":
    main()
