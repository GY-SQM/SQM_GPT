# -*- coding: utf-8 -*-
"""
patch_wh_heatmap_locmap.py
==========================
warehouse_api.py 의 두 엔드포인트를 lot_location_map 테이블 기반으로 전환.

  변경 1) /rack-heatmap  — inventory_tonbag(ACTIVE 필터) → lot_location_map 집계
  변경 2) /cell-grid     — get_cell_state 결과에 lot_location_map LOT 오버라이드

배경: inventory_tonbag 의 위치 지정 톤백 400건이 모두 SOLD 상태이므로
      기존 ACTIVE 필터 쿼리는 0건 반환 → 히트맵 빈칸.
      lot_location_map(200행, 6동 05랙, 40 LOT)이 실제 재고 위치 정보 보유.
"""
import pathlib, sys, shutil, datetime

TARGET = pathlib.Path(__file__).parent.parent / 'backend' / 'api' / 'warehouse_api.py'
STAMP  = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

src = TARGET.read_text(encoding='utf-8')

# ── 변경 1: rack-heatmap — lot_location_map 쿼리로 교체 ───────────────
OLD1 = """\
        ACTIVE = ('AVAILABLE', 'RESERVED', 'PICKED')
        con = _db()
        try:
            rows = con.execute(\"\"\"
                SELECT
                    CAST(SUBSTR(location, 2, 1) AS INTEGER)  AS dong,
                    CAST(SUBSTR(location, 4, 2) AS INTEGER)  AS rack,
                    lot_no,
                    COUNT(*) AS cnt
                FROM inventory_tonbag
                WHERE location IS NOT NULL
                  AND location LIKE 'G_-__-__-__'
                  AND status IN ({placeholders})
                  AND COALESCE(is_sample, 0) = 0
                GROUP BY dong, rack, lot_no
                ORDER BY dong, rack, cnt DESC
            \"\"\".format(placeholders=','.join('?' * len(ACTIVE))), ACTIVE).fetchall()
        finally:
            con.close()"""

NEW1 = """\
        con = _db()
        try:
            rows = con.execute(\"\"\"
                SELECT dong, rack, lot_no, SUM(tonbag_count) AS cnt
                FROM lot_location_map
                WHERE dong IS NOT NULL AND rack IS NOT NULL AND lot_no IS NOT NULL
                GROUP BY dong, rack, lot_no
                ORDER BY dong, rack, cnt DESC
            \"\"\").fetchall()
        finally:
            con.close()"""

if OLD1 not in src:
    print('ERROR: rack-heatmap 쿼리 블록을 찾지 못함 (이미 적용됐을 수 있음)')
    sys.exit(1)
src = src.replace(OLD1, NEW1, 1)
print('  [1] rack-heatmap → lot_location_map 쿼리 교체 OK')

# ── 변경 2: cell-grid — lot_location_map 오버라이드 추가 ───────────────
OLD2 = """\
        con = _db()
        try:
            cells = []
            for col in range(COL_RANGE[0], COL_RANGE[1] + 1):
                for lv in range(1, max_lv + 1):
                    loc = format_cell_location(dong, rack, col, lv)
                    st  = get_cell_state(con, loc)
                    # lot_no / sub_lt — 첫 번째 활성 톤백 기준 (히트맵·툴팁용)
                    tbs = st.get('tonbags') or []
                    primary_lot = tbs[0]['lot_no'] if tbs else ''
                    primary_sub = tbs[0]['sub_lt'] if tbs else None
                    cells.append({
                        'location':     loc,
                        'col':          col,
                        'level':        lv,
                        'state':        st['state'],
                        'active_count': st['active_count'],
                        'capacity':     st['capacity'],
                        'packing_type': st['packing_type'],
                        'lot_no':       primary_lot,
                        'sub_lt':       primary_sub,
                    })
        finally:
            con.close()"""

NEW2 = """\
        con = _db()
        try:
            # lot_location_map: 해당 동·랙의 셀별 LOT 미리 조회 (실제 재고 위치 우선)
            loc_rows = con.execute(\"\"\"
                SELECT col, level, lot_no
                FROM lot_location_map
                WHERE dong=? AND rack=?
            \"\"\", (dong, rack)).fetchall()
            loc_map = {(int(r['col']), int(r['level'])): r['lot_no'] for r in loc_rows}

            cells = []
            for col in range(COL_RANGE[0], COL_RANGE[1] + 1):
                for lv in range(1, max_lv + 1):
                    loc = format_cell_location(dong, rack, col, lv)
                    st  = get_cell_state(con, loc)
                    # lot_location_map 우선 → 없으면 inventory_tonbag 폴백
                    map_lot = loc_map.get((col, lv))
                    if map_lot:
                        primary_lot = map_lot
                        primary_sub = None
                        cell_state  = 'OCCUPIED'
                    else:
                        tbs = st.get('tonbags') or []
                        primary_lot = tbs[0]['lot_no'] if tbs else ''
                        primary_sub = tbs[0]['sub_lt'] if tbs else None
                        cell_state  = st['state']
                    cells.append({
                        'location':     loc,
                        'col':          col,
                        'level':        lv,
                        'state':        cell_state,
                        'active_count': st['active_count'],
                        'capacity':     st['capacity'],
                        'packing_type': st['packing_type'],
                        'lot_no':       primary_lot,
                        'sub_lt':       primary_sub,
                    })
        finally:
            con.close()"""

if OLD2 not in src:
    print('ERROR: cell-grid 루프 블록을 찾지 못함 (이미 적용됐을 수 있음)')
    sys.exit(1)
src = src.replace(OLD2, NEW2, 1)
print('  [2] cell-grid → lot_location_map 오버라이드 추가 OK')

# ── 저장 ─────────────────────────────────────────────────────────────
bak = TARGET.with_suffix('.py.bak_locmap_' + STAMP)
shutil.copy2(TARGET, bak)
print(f'  백업: {bak.name}')

TARGET.write_text(src, encoding='utf-8')
print(f'  저장: {TARGET.name}  ({src.count(chr(10)) + 1} 줄)')
print('DONE.')
