"""
patch_alloc_header_simple.py  (v8.6.9)
Allocation 헤더 심플화 — Available 스타일로 통일

변경 내용:
  - 기존: 헤더 + 11버튼 툴바 + 단계되돌리기 + 상태필터(4탭)
  - 변경: 헤더 한 줄 (타이틀 + 요약 + 핵심 5버튼)

유지 버튼: 📂 Excel 업로드 / ❌ 배정 취소 / 📦 PICKED / 🔒 SOLD / 🔁 새로고침
제거: 승인분 반영, 승인 대기, LOT 초기화, 전체 초기화, SALE REF 취소,
      LOT 현황, Excel 내보내기, 단계 되돌리기 행, 상태 필터 탭

실행: python scripts/patch_alloc_header_simple.py
"""
import pathlib, shutil, datetime

ROOT   = pathlib.Path(__file__).resolve().parent.parent
TARGET = ROOT / "frontend" / "js" / "sqm-allocation.js"
TS     = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def backup(p):
    bak = p.with_suffix(p.suffix + f".bak_allochdr_{TS}")
    shutil.copy2(p, bak)
    print(f"  📦 백업: {bak.name}")


def patch(src: str) -> str:
    OLD = (
        '<div class="alloc-header" style="display:flex;align-items:center;gap:12px;padding:8px 0 8px">\',\n'
        '      \'  <h2 style="margin:0">📋 판매 배정 (Allocation)</h2>\',\n'
        '      \'  <span id="alloc-summary-label" style="color:var(--text-muted);font-size:.9rem"></span>\',\n'
        '      \'  <button class="btn btn-secondary" onclick="renderPage(\\\'allocation\\\')" style="margin-left:auto">🔁 새로고침</button>\',\n'
        '      \'</div>\',\n'
        '      /* ── 액션 툴바 (v864-2 AllocationDialog primary_buttons 매핑) ── */\n'
        '      \'<div class="alloc-toolbar" style="display:flex;flex-wrap:wrap;align-items:center;gap:6px;padding:8px 10px;background:var(--panel);border:1px solid var(--panel-border);border-radius:6px;margin-bottom:8px">\',\n'
        '      \'  <button class="btn btn-primary" onclick="window.allocUploadExcel()">📂 Excel 업로드</button>\',\n'
        '      \'  <button class="btn" onclick="window.allocApplyApproved()">📌 승인분 반영</button>\',\n'
        '      \'  <button class="btn" onclick="window.allocShowApprovalQueue()">✅ 승인 대기</button>\',\n'
        '      \'  <span style="width:1px;height:22px;background:var(--panel-border);margin:0 4px"></span>\',\n'
        '      \'  <button class="btn btn-danger" onclick="window.allocCancelSelected()">❌ 선택 배정 취소</button>\',\n'
        '      \'  <span style="width:1px;height:22px;background:var(--panel-border);margin:0 4px"></span>\',\n'
        '      /* 백엔드 엔드포인트 미구현 — Sprint 1-1-E에서 연결 */\n'
        '      \'  <button class="btn" onclick="window.allocPickSelected()" title="RESERVED → PICKED">📦 출고 실행 (PICKED)</button>\',\n'
        '      \'  <button class="btn" onclick="window.allocConfirmSelected()" title="PICKED → SOLD">🔒 출고 확정 (SOLD)</button>\',\n'
        '      \'  <button class="btn" onclick="window.allocResetSelected()" title="LOT 배정 완전 삭제">🧹 LOT 초기화</button>\',\n'
        '      \'  <span style="width:1px;height:22px;background:var(--panel-border);margin:0 4px"></span>\',\n'
        '      \'  <button class="btn btn-danger" onclick="window.allocResetAll()" title="모든 배정 취소 + AVAILABLE 원복">⚠️ 전체 초기화</button>\',\n'
        '      \'  <button class="btn" onclick="window.allocCancelBySaleRef()" title="SALE REF 입력 후 해당 배정 전체 취소">🔖 SALE REF 취소</button>\',\n'
        '      \'  <button class="btn" onclick="window.allocOpenLotOverview()" title="LOT별 배정 현황 팝업">📦 LOT 현황</button>\',\n'
        '      \'  <button class="btn btn-secondary" onclick="window.allocExportExcel()" title="현재 배정 데이터 Excel 다운로드">📊 Excel 내보내기</button>\',\n'
        '      \'</div>\',\n'
        '      /* ── 단계 되돌리기 버튼 행 ── */\n'
        '      \'<div style="display:flex;flex-wrap:wrap;gap:6px;align-items:center;padding:6px 8px;background:var(--panel);border:1px solid var(--panel-border);border-radius:6px;margin-bottom:8px">\',\n'
        '      \'  <span style="font-size:12px;font-weight:600;white-space:nowrap">&#x21A9; 단계 되돌리기:</span>\',\n'
        "      '  <button class=\"btn\" onclick=\"window.allocRevertStep(\\'RESERVED\\')\" style=\"font-size:12px\">RESERVED &rarr; AVAILABLE</button>',\n"
        '      \'</div>\',\n'
        '      /* ── 상태 필터 ── */\n'
        '      \'<div class="alloc-filter" style="display:flex;gap:4px;margin-bottom:8px">\',\n'
        "      '  <button class=\"alloc-filter-btn active\" data-filter=\"all\" onclick=\"window.allocFilterBy(\\'all\\')\">전체</button>',\n"
        "      '  <button class=\"alloc-filter-btn\" data-filter=\"RESERVED\" onclick=\"window.allocFilterBy(\\'RESERVED\\')\">RESERVED</button>',\n"
        "      '  <button class=\"alloc-filter-btn\" data-filter=\"PICKED\" onclick=\"window.allocFilterBy(\\'PICKED\\')\">PICKED</button>',\n"
        "      '  <button class=\"alloc-filter-btn\" data-filter=\"SOLD\" onclick=\"window.allocFilterBy(\\'SOLD\\')\">SOLD</button>',\n"
        "      '</div>',"
    )

    NEW = (
        '<div class="alloc-header" style="display:flex;align-items:center;gap:12px;padding:8px 0 8px">\',\n'
        '      \'  <h2 style="margin:0">📋 판매 배정 (Allocation)</h2>\',\n'
        '      \'  <span id="alloc-summary-label" style="color:var(--text-muted);font-size:.9rem"></span>\',\n'
        '      \'  <div style="margin-left:auto;display:flex;gap:6px;align-items:center">\',\n'
        '      \'    <button class="btn btn-primary" onclick="window.allocUploadExcel()">📂 Excel 업로드</button>\',\n'
        '      \'    <button class="btn btn-danger" onclick="window.allocCancelSelected()">❌ 배정 취소</button>\',\n'
        '      \'    <button class="btn" onclick="window.allocPickSelected()" title="RESERVED → PICKED">📦 PICKED</button>\',\n'
        '      \'    <button class="btn" onclick="window.allocConfirmSelected()" title="PICKED → SOLD">🔒 SOLD</button>\',\n'
        '      \'    <button class="btn btn-secondary" onclick="renderPage(\\\'allocation\\\')">🔁 새로고침</button>\',\n'
        '      \'  </div>\',\n'
        "      '</div>',"
    )

    if OLD in src:
        result = src.replace(OLD, NEW, 1)
        print("  ✅  헤더 심플화 완료 (툴바 11버튼 + 단계되돌리기 + 필터탭 제거)")
        return result
    else:
        print("  ⚠️  패턴 미발견 — 수동 확인 필요")
        return src


def main():
    print("\n=== patch_alloc_header_simple.py 시작 ===\n")
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
