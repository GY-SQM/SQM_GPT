#!/usr/bin/env python3
"""
patch_footer_picked.py
======================
sqm-picked.js — Picked 테이블에 노란 합계 tfoot 추가 (v8.6.9)

앵커: document.getElementById('picked-table').style.display = '';
앞에 tfoot 생성 블록 삽입 (톤백수/중량/Available/Reserved/Packed 합계)

컬럼 순서 (18개):
  #, (expand), LOT No, +, 피킹No, 고객사, 톤백수, 중량(kg),
  MXBG, Available, Reserved, Packed, Total Bags, Remain Bags,
  AV, VR, AR, Title Transfer Date

대상: frontend/js/sqm-picked.js (IIFE, ABSOLUTE EDIT BAN)
방식: bytes 레벨 find & replace
"""
import sys, os, shutil, subprocess
from datetime import datetime

BASE   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(BASE, 'frontend', 'js', 'sqm-picked.js')

# 앵커: tbody.innerHTML 할당 직후 ~ table display 켜기
OLD = (
    b"      }).join('');\n"
    b"      document.getElementById('picked-table').style.display = '';\n"
)

NEW = (
    b"      }).join('');\n"
    b"      // v8.6.9 \xeb\x85\xb8\xeb\x9e\x80 tfoot \xed\x95\xa9\xea\xb3\x84\n"
    b"      (function() {\n"
    b"        var _sumTb = 0, _sumKg = 0, _sumAv = 0, _sumRv = 0, _sumPk = 0;\n"
    b"        rows.forEach(function(r) {\n"
    b"          _sumTb += Number(r.tonbag_count || 0);\n"
    b"          _sumKg += Number(r.total_kg     || 0);\n"
    b"          _sumAv += Number(r.tb_available || 0);\n"
    b"          _sumRv += Number(r.tb_reserved  || 0);\n"
    b"          _sumPk += Number(r.tb_picked    || 0);\n"
    b"        });\n"
    b"        var _tbl = document.getElementById('picked-table');\n"
    b"        if (_tbl && !_tbl.querySelector('tfoot')) {\n"
    b"          var _tf = document.createElement('tfoot');\n"
    b"          _tf.innerHTML =\n"
    b"            '<tr style=\"background:#FFD600;font-weight:800;color:#222;font-size:19px\">'\n"
    b"            + '<td colspan=\"6\" style=\"text-align:right;padding:6px 10px\">'\n"
    b"            + '\xed\x95\xa9\xea\xb3\x84 ' + rows.length + ' LOT</td>'\n"
    b"            + '<td class=\"mono-cell\" style=\"text-align:right;padding:6px 8px\">'\n"
    b"            + _sumTb.toLocaleString('ko-KR') + '</td>'\n"
    b"            + '<td class=\"mono-cell\" style=\"text-align:right;padding:6px 8px\">'\n"
    b"            + (typeof fmtN === 'function' ? fmtN(_sumKg) : _sumKg.toFixed(0)) + '</td>'\n"
    b"            + '<td></td>'\n"
    b"            + '<td class=\"mono-cell\" style=\"text-align:center;color:#22c55e\">'\n"
    b"            + _sumAv + '</td>'\n"
    b"            + '<td class=\"mono-cell\" style=\"text-align:center;color:#3b82f6\">'\n"
    b"            + _sumRv + '</td>'\n"
    b"            + '<td class=\"mono-cell\" style=\"text-align:center;color:#f59e0b\">'\n"
    b"            + _sumPk + '</td>'\n"
    b"            + '<td colspan=\"5\"></td>'\n"
    b"            + '</tr>';\n"
    b"          _tbl.appendChild(_tf);\n"
    b"        }\n"
    b"      })();\n"
    b"      document.getElementById('picked-table').style.display = '';\n"
)

def main():
    if not os.path.exists(TARGET):
        print(f"❌ 파일 없음: {TARGET}")
        sys.exit(1)

    with open(TARGET, 'rb') as f:
        data = f.read()

    if b'v8.6.9' in data and b'picked-table' in data and b'_sumTb' in data:
        print("ℹ️  이미 적용됨 — 스킵")
        return

    # LF/CRLF 시도
    if OLD in data:
        anchor, rep, mode = OLD, NEW, "LF"
    else:
        old_cr = OLD.replace(b'\n', b'\r\n')
        new_cr = NEW.replace(b'\n', b'\r\n')
        if old_cr in data:
            anchor, rep, mode = old_cr, new_cr, "CRLF"
        else:
            print("❌ 앵커 없음")
            idx = data.find(b"picked-table').style.display = ''")
            if idx != -1:
                print(f"  → 위치 {idx}:", repr(data[max(0,idx-80):idx+60]))
            sys.exit(1)

    count = data.count(anchor)
    if count > 1:
        print(f"⚠️  앵커 {count}개 — 첫 번째만 치환")

    bak = TARGET + '.bak_footer_picked_' + datetime.now().strftime('%Y%m%d_%H%M%S')
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
