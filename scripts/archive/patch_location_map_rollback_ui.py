"""
patch_location_map_rollback_ui.py  (v8.6.9)
위치매핑 롤백 UI 추가 — 위치재고조회 엑셀 Import 모달

변경 대상:
  frontend/js/sqm-location-map-import.js  (334줄, IIFE → 패치 스크립트 처리)

변경 내용 2가지:
  ① 툴바에 🗑️ 최신 배치 롤백 버튼 추가 (💾 버튼 앞)
  ② _doRollback() 함수 추가 (공개 함수 섹션 바로 앞)
     - GET /api/location-map/latest → batch_id 확인
     - sqmConfirm 후 DELETE /api/location-map/batch/{id}
     - 성공 시 위치 초기화(B) 여부 추가 confirm
     - 위치 초기화: POST /api/inventory/clear-lot-locations

실행: python scripts/patch_location_map_rollback_ui.py
"""
import pathlib, shutil, datetime

ROOT   = pathlib.Path(__file__).resolve().parent.parent
TARGET = ROOT / "frontend" / "js" / "sqm-location-map-import.js"
TS     = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def backup(p: pathlib.Path):
    bak = p.with_suffix(p.suffix + f".bak_rollback_{TS}")
    shutil.copy2(p, bak)
    print(f"  📦 백업: {bak.name}")


def patch(src: str) -> str:
    total_applied = 0

    # ── ① 툴바: 💾 버튼 앞에 🗑️ 롤백 버튼 삽입 ─────────────────────
    OLD1 = (
        "      + '  <button id=\"lmi-commit\" class=\"btn\" disabled '\n"
        "      +     'style=\"background:#27ae60;color:#fff;\">💾 위치 후보 저장</button>'\n"
        "      + '</div>'\n"
    )
    NEW1 = (
        "      + '  <button id=\"lmi-rollback\" class=\"btn\" '\n"
        "      +     'style=\"background:#c0392b;color:#fff;\" '\n"
        "      +     'title=\"최신 import batch 삭제 + (선택) 톤백 위치 초기화\">🗑️ 최신 배치 롤백</button>'\n"
        "      + '  <button id=\"lmi-commit\" class=\"btn\" disabled '\n"
        "      +     'style=\"background:#27ae60;color:#fff;\">💾 위치 후보 저장</button>'\n"
        "      + '</div>'\n"
    )
    if OLD1 in src:
        src = src.replace(OLD1, NEW1, 1)
        print("  ✅  [①] 🗑️ 최신 배치 롤백 버튼 삽입")
        total_applied += 1
    else:
        print("  ⚠️  [①] 툴바 버튼 패턴 미발견")

    # ── ① 이벤트 바인딩: _ensureModal 내 commit onclick 뒤에 rollback onclick 추가 ──
    OLD1b = "    document.getElementById('lmi-commit').onclick = _doCommit;\n"
    NEW1b = (
        "    document.getElementById('lmi-commit').onclick = _doCommit;\n"
        "    document.getElementById('lmi-rollback').onclick = _doRollback;\n"
    )
    if OLD1b in src:
        src = src.replace(OLD1b, NEW1b, 1)
        print("  ✅  [①b] rollback onclick 바인딩 추가")
        total_applied += 1
    else:
        print("  ⚠️  [①b] commit onclick 패턴 미발견")

    # ── ② _doRollback 함수: 공개 함수 섹션 바로 앞에 삽입 ────────────
    OLD2 = "  /* 공개 함수 */\n"
    NEW2 = (
        "  /* ── 롤백: 최신 batch 삭제 + (선택) 톤백 위치 초기화 ── */\n"
        "  function _doRollback() {\n"
        "    if (_state.busy) return;\n"
        "    // ① 최신 batch 정보 조회\n"
        "    fetch(_api() + '/api/location-map/latest')\n"
        "      .then(function (r) { return r.json(); })\n"
        "      .then(function (res) {\n"
        "        if (!res || !res.ok) {\n"
        "          _toast('error', '배치 정보 조회 실패: ' + (res && res.error || '알 수 없음'));\n"
        "          return;\n"
        "        }\n"
        "        var d = res.data || {};\n"
        "        var batchId = d.batch_id;\n"
        "        if (!batchId) {\n"
        "          _toast('warning', '삭제할 import 배치가 없습니다');\n"
        "          return;\n"
        "        }\n"
        "        var lotCount = d.count || 0;\n"
        "        var msg = '⚠️ 최신 배치 #' + batchId + ' 를 삭제합니다.\\n'\n"
        "          + 'LOT ' + lotCount + '개의 위치 후보(매핑 데이터)가 제거됩니다.\\n\\n'\n"
        "          + '계속할까요?';\n"
        "        if (!window.sqmConfirm(msg)) return;\n"
        "        // ② batch 삭제 API 호출\n"
        "        _state.busy = true;\n"
        "        fetch(_api() + '/api/location-map/batch/' + batchId, { method: 'DELETE' })\n"
        "          .then(function (r) { return r.json(); })\n"
        "          .then(function (res2) {\n"
        "            _state.busy = false;\n"
        "            if (!res2 || !res2.ok) {\n"
        "              _toast('error', '배치 삭제 실패: ' + (res2 && res2.error || '알 수 없음'));\n"
        "              return;\n"
        "            }\n"
        "            var d2 = res2.data || {};\n"
        "            var lotNos = d2.lot_nos || [];\n"
        "            _toast('success', d2.message || '배치 삭제 완료');\n"
        "            // ③ 위치 초기화(B) 여부 추가 확인\n"
        "            if (lotNos.length > 0) {\n"
        "              var msg2 = '배치가 삭제되었습니다.\\n\\n'\n"
        "                + '추가로 해당 LOT ' + lotNos.length + '개의\\n'\n"
        "                + '톤백 실제 위치(inventory_tonbag.location)도\\n'\n"
        "                + '초기화(NULL)할까요?\\n\\n'\n"
        "                + '※ 위치 후보만 지우고 실제 위치는 유지하려면 [취소]';\n"
        "              if (window.sqmConfirm(msg2)) {\n"
        "                fetch(_api() + '/api/inventory/clear-lot-locations', {\n"
        "                  method: 'POST',\n"
        "                  headers: { 'Content-Type': 'application/json' },\n"
        "                  body: JSON.stringify({ lot_nos: lotNos }),\n"
        "                })\n"
        "                  .then(function (r) { return r.json(); })\n"
        "                  .then(function (res3) {\n"
        "                    if (res3 && res3.ok) {\n"
        "                      _toast('success', '위치 초기화 완료 — 톤백 ' + (res3.tonbag_cleared || 0) + '개');\n"
        "                    } else {\n"
        "                      _toast('error', '위치 초기화 실패: ' + (res3 && res3.error || '알 수 없음'));\n"
        "                    }\n"
        "                  })\n"
        "                  .catch(function (e) { _toast('error', '위치 초기화 요청 실패: ' + e.message); });\n"
        "              }\n"
        "            }\n"
        "            // 모달 body 초기화\n"
        "            document.getElementById('lmi-body').innerHTML =\n"
        "              '<div style=\"text-align:center;padding:40px;color:#a5d6a7;\">'\n"
        "              + '✅ 배치 #' + batchId + ' 삭제 완료 — 새 엑셀을 다시 업로드하세요.</div>';\n"
        "            document.getElementById('lmi-commit').disabled = true;\n"
        "            document.getElementById('lmi-force-wrap').style.display = 'none';\n"
        "            _state.report = null;\n"
        "          })\n"
        "          .catch(function (e) {\n"
        "            _state.busy = false;\n"
        "            _toast('error', '배치 삭제 요청 실패: ' + e.message);\n"
        "          });\n"
        "      })\n"
        "      .catch(function (e) { _toast('error', '배치 정보 조회 실패: ' + e.message); });\n"
        "  }\n"
        "\n"
        "  /* 공개 함수 */\n"
    )
    if OLD2 in src:
        src = src.replace(OLD2, NEW2, 1)
        print("  ✅  [②] _doRollback() 함수 추가")
        total_applied += 1
    else:
        print("  ⚠️  [②] 공개 함수 섹션 패턴 미발견")

    print(f"\n  📊 총 {total_applied}/3 패치 적용")
    return src


def main():
    print("\n=== patch_location_map_rollback_ui.py 시작 ===\n")
    print(f"[{TARGET.name}]")
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
