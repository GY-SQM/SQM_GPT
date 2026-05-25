# -*- coding: utf-8 -*-
"""
patch_barcode_sold_modal.py — v8.6.9 (2026-05-25)

frontend/js/sqm-upload-modals.js (476줄, IIFE) 에 바코드 SOLD 확정 모달 추가.
2단계 워크플로우: dry_run preview → 사용자 확인 → 실제 적용.

Rule 5 ABSOLUTE EDIT BAN (IIFE 파일) → patch script 사용.
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "frontend" / "js" / "sqm-upload-modals.js"

OLD = """  window.showBarcodeScanUploadModal = showBarcodeScanUploadModal;

  window._showExcelUploadModal = _showExcelUploadModal;
  window._showPdfUploadModal = _showPdfUploadModal;
})();"""

NEW = """  window.showBarcodeScanUploadModal = showBarcodeScanUploadModal;

  /* ═══════════════════════════════════════════════════════════════
     v8.6.9 (2026-05-25): 바코드 스캔 → SOLD 확정 모달
     2단계: dry_run preview → 사용자 확인 → 실제 적용
     ═══════════════════════════════════════════════════════════════ */
  function showBarcodeSoldConfirmModal() {
    var overlay = document.createElement('div');
    overlay.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.6);z-index:99998;display:flex;align-items:center;justify-content:center;';
    var box = document.createElement('div');
    box.style.cssText = 'background:var(--panel,#1e293b);border:1px solid var(--panel-border,#334155);border-radius:10px;padding:24px;width:680px;max-width:90vw;max-height:88vh;overflow-y:auto;color:var(--text,#e2e8f0);box-shadow:0 16px 50px rgba(0,0,0,0.5);';
    box.innerHTML =
      '<h2 style="margin:0 0 8px 0;font-size:18px;display:flex;align-items:center;gap:8px">' +
      '<span>📦</span> 바코드 스캔 → SOLD 확정' +
      '<span style="background:#ef4444;color:#fff;font-size:11px;padding:2px 8px;border-radius:4px;margin-left:auto">취소 불가 (final)</span>' +
      '</h2>' +
      '<p style="color:var(--text-muted,#94a3b8);font-size:13px;margin:0 0 16px 0">' +
      '현장에서 출고 시 톤백 바코드를 스캔한 Excel(.xlsx) 파일을 업로드하면 매칭된 톤백을 PICKED → SOLD 로 확정합니다.' +
      '<br>먼저 미리보기로 매칭 결과를 확인한 후 SOLD 확정을 진행하세요.' +
      '</p>' +
      '<div style="border:2px dashed var(--panel-border,#334155);border-radius:8px;padding:20px;text-align:center;margin-bottom:12px" id="bcs-dropzone">' +
      '<input type="file" id="bcs-file" accept=".xlsx,.xls" style="display:none">' +
      '<button id="bcs-pick" class="btn btn-primary" style="padding:8px 20px">📁 Excel 파일 선택</button>' +
      '<div id="bcs-fname" style="margin-top:10px;font-size:13px;color:var(--text-muted,#94a3b8)">선택된 파일 없음</div>' +
      '</div>' +
      '<div id="bcs-result" style="display:none;background:var(--bg,#0f172a);border:1px solid var(--panel-border,#334155);border-radius:6px;padding:14px;font-size:13px;margin-bottom:12px"></div>' +
      '<div style="display:flex;gap:8px;justify-content:flex-end">' +
      '<button id="bcs-close" class="btn">닫기</button>' +
      '<button id="bcs-preview" class="btn btn-primary" disabled>🔍 미리보기 (dry_run)</button>' +
      '<button id="bcs-apply" class="btn" style="display:none;background:#ef4444;color:#fff;font-weight:700">✅ SOLD 확정 진행</button>' +
      '</div>';
    overlay.appendChild(box);
    document.body.appendChild(overlay);

    var fileInput = box.querySelector('#bcs-file');
    var fname     = box.querySelector('#bcs-fname');
    var resultEl  = box.querySelector('#bcs-result');
    var btnPick   = box.querySelector('#bcs-pick');
    var btnClose  = box.querySelector('#bcs-close');
    var btnPrev   = box.querySelector('#bcs-preview');
    var btnApply  = box.querySelector('#bcs-apply');

    btnPick.onclick = function() { fileInput.click(); };
    fileInput.onchange = function() {
      if (fileInput.files && fileInput.files[0]) {
        fname.textContent = '📄 ' + fileInput.files[0].name + ' (' + (fileInput.files[0].size/1024).toFixed(1) + ' KB)';
        btnPrev.disabled = false;
        btnApply.style.display = 'none';
        resultEl.style.display = 'none';
      }
    };
    btnClose.onclick = function() { document.body.removeChild(overlay); };

    function _renderResult(d, isPreview) {
      var s = d.summary || {};
      var matched = (d.preview && d.preview.matched) || [];
      var mismatch = (d.preview && d.preview.mismatch_status) || [];
      var notFound = (d.preview && d.preview.not_found) || [];
      var locChanged = matched.filter(function(m){ return m.location_changed; }).length;

      var html = '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:10px">' +
        '<div style="padding:8px;background:rgba(34,197,94,0.1);border:1px solid #22c55e44;border-radius:4px;text-align:center"><div style="color:#22c55e;font-weight:800;font-size:18px">' + (s.match||0) + '</div><div style="font-size:11px;color:var(--text-muted,#94a3b8)">매칭 OK</div></div>' +
        '<div style="padding:8px;background:rgba(245,158,11,0.1);border:1px solid #f59e0b44;border-radius:4px;text-align:center"><div style="color:#f59e0b;font-weight:800;font-size:18px">' + (s.mismatch_status||0) + '</div><div style="font-size:11px;color:var(--text-muted,#94a3b8)">상태 불일치</div></div>' +
        '<div style="padding:8px;background:rgba(239,68,68,0.1);border:1px solid #ef444444;border-radius:4px;text-align:center"><div style="color:#ef4444;font-weight:800;font-size:18px">' + (s.not_found||0) + '</div><div style="font-size:11px;color:var(--text-muted,#94a3b8)">DB에 없음</div></div>' +
        '<div style="padding:8px;background:rgba(59,130,246,0.1);border:1px solid #3b82f644;border-radius:4px;text-align:center"><div style="color:#3b82f6;font-weight:800;font-size:18px">' + (s.total||0) + '</div><div style="font-size:11px;color:var(--text-muted,#94a3b8)">총 행</div></div>' +
        '</div>';
      if (locChanged > 0) {
        html += '<div style="background:rgba(245,158,11,0.15);border-left:3px solid #f59e0b;padding:6px 10px;margin-bottom:8px;font-size:12px">📍 위치 변경 예정: <strong>' + locChanged + '</strong>건 (직원이 스캔한 실제 위치로 갱신)</div>';
      }
      if (!isPreview && s.applied != null) {
        html += '<div style="background:rgba(34,197,94,0.15);border-left:3px solid #22c55e;padding:8px 10px;margin-bottom:8px;font-weight:700;font-size:14px">✅ SOLD 확정 완료: <strong>' + s.applied + '</strong>건</div>';
      }
      function _list(title, rows, color, fmtFn) {
        if (!rows.length) return '';
        var inner = rows.slice(0, 10).map(fmtFn).join('');
        var more = rows.length > 10 ? '<div style="font-size:11px;color:var(--text-muted,#94a3b8);padding:4px 8px">... 외 ' + (rows.length - 10) + '건</div>' : '';
        return '<details style="margin-top:6px"><summary style="cursor:pointer;color:' + color + ';font-weight:600">' + title + ' (' + rows.length + ')</summary>' +
               '<div style="font-family:monospace;font-size:11px;max-height:140px;overflow-y:auto;background:rgba(0,0,0,0.2);padding:6px;border-radius:4px;margin-top:4px">' + inner + more + '</div></details>';
      }
      html += _list('⚠️ 상태 불일치 (PICKED 아님 — 처리 안 됨)', mismatch, '#f59e0b', function(it){
        return '<div>' + (it.tonbag_uid||'-') + ' · 현재: ' + (it.current_status||'?') + ' · 위치: ' + (it.actual_location||'-') + '</div>';
      });
      html += _list('❌ DB에 없는 톤백 (처리 안 됨)', notFound, '#ef4444', function(it){
        return '<div>' + (it.tonbag_uid||'-') + ' · LOT: ' + (it.lot_no||'-') + ' · SubLT: ' + (it.sub_lt||'-') + '</div>';
      });
      if (d.warnings && d.warnings.length) {
        html += _list('🟡 파싱 경고', d.warnings.map(function(w){return {w:w};}), '#94a3b8', function(it){ return '<div>' + it.w + '</div>'; });
      }
      return html;
    }

    function _upload(dryRun, onDone) {
      if (!fileInput.files || !fileInput.files[0]) return;
      var fd = new FormData();
      fd.append('file', fileInput.files[0]);
      resultEl.style.display = 'block';
      resultEl.innerHTML = '<div style="text-align:center;padding:20px;color:var(--text-muted,#94a3b8)">⏳ ' + (dryRun ? '미리보기' : 'SOLD 확정') + ' 중...</div>';
      btnPrev.disabled = true;
      btnApply.disabled = true;
      fetch('/api/outbound/barcode-confirm-sold?dry_run=' + (dryRun ? 'true' : 'false'), {
        method: 'POST', body: fd
      }).then(function(r){ return r.json(); }).then(function(d){
        resultEl.innerHTML = _renderResult(d, dryRun);
        btnPrev.disabled = false;
        btnApply.disabled = false;
        if (onDone) onDone(d);
      }).catch(function(e){
        resultEl.innerHTML = '<div style="color:#ef4444;font-weight:700">❌ 실패: ' + (e.message||String(e)) + '</div>';
        btnPrev.disabled = false;
      });
    }

    btnPrev.onclick = function() {
      _upload(true, function(d) {
        var s = d.summary || {};
        if ((s.match||0) > 0) {
          btnApply.style.display = '';
          btnApply.textContent = '✅ SOLD 확정 진행 (' + s.match + '건)';
        }
      });
    };
    btnApply.onclick = function() {
      if (!confirm('정말 ' + (btnApply.textContent.match(/\\d+/) || [0]) + '건을 SOLD 로 확정하시겠습니까?\\n\\n⚠️ SOLD 는 취소할 수 없습니다 (차량 출발 = 거래 종료).')) return;
      _upload(false, function() {
        btnApply.style.display = 'none';
        btnPrev.disabled = true;
      });
    };
  }
  window.showBarcodeSoldConfirmModal = showBarcodeSoldConfirmModal;

  window._showExcelUploadModal = _showExcelUploadModal;
  window._showPdfUploadModal = _showPdfUploadModal;
})();"""


def main() -> int:
    if not TARGET.exists():
        print(f"[ERROR] 대상 없음: {TARGET}")
        return 1
    src = TARGET.read_text(encoding="utf-8")
    if OLD not in src:
        print("[ERROR] OLD 문자열 매칭 실패 — 파일이 이미 수정되었거나 버전이 다름")
        return 2
    if src.count(OLD) > 1:
        print(f"[ERROR] OLD 다중 매칭 ({src.count(OLD)})")
        return 3
    src2 = src.replace(OLD, NEW, 1)
    backup = TARGET.with_suffix(TARGET.suffix + ".bak_barcode_sold")
    backup.write_text(TARGET.read_text(encoding="utf-8"), encoding="utf-8")
    TARGET.write_text(src2, encoding="utf-8")
    print(f"[BACKUP] {backup.name}")
    print(f"[WRITE]  {TARGET.name}  ({len(src)} -> {len(src2)} bytes)")

    import subprocess
    r = subprocess.run(["node", "--check", str(TARGET)], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"[node --check] FAIL:\n{r.stderr}")
        return 4
    print("[node --check] OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
