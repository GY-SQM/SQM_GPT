# -*- coding: utf-8 -*-
"""
patch_warehouse_heatmap.py
==========================
warehouse_api.py 에 두 가지 변경 적용:
  1) cell-grid 셀에 lot_no / sub_lt 필드 추가 (히트맵·툴팁용)
  2) /rack-heatmap 신규 엔드포인트 추가 (대시보드 경량 집계)
"""
import pathlib, re, sys

TARGET = pathlib.Path(__file__).parent.parent / 'backend' / 'api' / 'warehouse_api.py'
src = TARGET.read_text(encoding='utf-8')

# ── 1) cell-grid : cells.append 블록에 lot_no / sub_lt 추가 ──────────
OLD_APPEND = """\
                    cells.append({
                        'location':     loc,
                        'col':          col,
                        'level':        lv,
                        'state':        st['state'],
                        'active_count': st['active_count'],
                        'capacity':     st['capacity'],
                        'packing_type': st['packing_type'],
                    })"""

NEW_APPEND = """\
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
                    })"""

if OLD_APPEND not in src:
    print('ERROR: cell-grid append 블록을 찾지 못함')
    sys.exit(1)
src = src.replace(OLD_APPEND, NEW_APPEND, 1)
print('  [1] cell-grid lot_no/sub_lt 추가 OK')

# ── 2) /rack-heatmap 엔드포인트 — cell-grid 엔드포인트 직후에 삽입 ──
# cell-grid except 블록 끝의 고유 패턴
INSERT_AFTER = """\
    except Exception as e:
        logger.error('cell-grid error: %s', e)
        return err_response(str(e))"""

HEATMAP_CODE = """

# ─────────────────────────────────────────────────────────────────────
# GET /api/warehouse/rack-heatmap
#   대시보드 히트맵용 — 랙별 지배 LOT + 점유 통계 (경량 단일 쿼리)
# ─────────────────────────────────────────────────────────────────────
@router.get('/rack-heatmap', summary='🗺 랙별 LOT 히트맵 (대시보드 임베드용)')
def api_rack_heatmap():
    \"\"\"
    전체 창고(5동/6동) 각 랙의 점유 현황과 지배 LOT 반환.
    셀 단위가 아닌 랙 단위 집계라 매우 빠름 — 대시보드 자동 갱신 적합.
    \"\"\"
    try:
        from engine_modules.warehouse_cell_logic import (
            LEVEL_BY_RACK, WAREHOUSE_DONGS, RACK_RANGE, COL_RANGE,
        )
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
            con.close()

        from collections import defaultdict
        rack_data = defaultdict(lambda: {'occupied': 0, 'lots': [], 'lot_counts': {}})
        for r in rows:
            d, rk = r['dong'], r['rack']
            lot, cnt = r['lot_no'] or '', r['cnt']
            key = (d, rk)
            rack_data[key]['occupied'] += cnt
            rack_data[key]['lot_counts'][lot] = cnt
            if lot and lot not in rack_data[key]['lots']:
                rack_data[key]['lots'].append(lot)

        result = []
        for dong in WAREHOUSE_DONGS:
            for rack in range(RACK_RANGE[0], RACK_RANGE[1] + 1):
                max_lv = LEVEL_BY_RACK.get(rack, 0)
                total_cells = (COL_RANGE[1] - COL_RANGE[0] + 1) * max_lv
                key = (dong, rack)
                info = rack_data.get(key, {})
                lot_counts = info.get('lot_counts', {})
                dominant = max(lot_counts, key=lot_counts.get) if lot_counts else ''
                result.append({
                    'dong':         dong,
                    'rack':         rack,
                    'rack_label':   f'{rack:02d}',
                    'dominant_lot': dominant,
                    'occupied':     info.get('occupied', 0),
                    'total':        total_cells,
                    'lots':         info.get('lots', []),
                })
        return ok_response({'racks': result})
    except Exception as e:
        logger.error('rack-heatmap error: %s', e)
        return err_response(str(e))
"""

if INSERT_AFTER not in src:
    print('ERROR: cell-grid except 블록을 찾지 못함')
    sys.exit(1)

# INSERT_AFTER 첫 번째 등장 위치 이후에 삽입
idx = src.index(INSERT_AFTER) + len(INSERT_AFTER)
src = src[:idx] + HEATMAP_CODE + src[idx:]
print('  [2] /rack-heatmap 엔드포인트 추가 OK')

TARGET.write_text(src, encoding='utf-8')
print(f'  저장: {TARGET}  ({src.count(chr(10))+1} 줄)')
print('DONE.')
