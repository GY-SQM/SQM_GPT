# SQM v8.6.9 | PyWebView + FastAPI + SQLite

**작업 폴더:** `D:\program\SQM_inventory\sqm_v869_clean`
**GitHub:** `https://github.com/kidongnam1/sqm_3` (main)
**최종 갱신:** 2026-05-24

---

## STACK
PyWebView 5 · FastAPI 0.104 · Vanilla JS · SQLite WAL · Python 3.11

## ⛔ ABSOLUTE EDIT BAN (LLM/Codex 절대 금지 파일)
다음 파일은 IIFE/대형 폐쇄 구조라 Edit 툴 사용 시 사고 가능 → 무조건 `scripts/patch_*.py`:
- `frontend/js/sqm-inline.js`  (7,516줄, IIFE)
- `frontend/js/sqm-core.js`    (2,000줄+, IIFE)
- `})();` 로 끝나는 모든 JS 파일

## CORE RULES
- **Rule 5 (개정 2026-05-24)** — Edit 툴 사용 규칙:
  - ① **위 ABSOLUTE EDIT BAN 목록은 절대 Edit 금지** (사고 사례: 2026-05-15 sqm-inline.js IIFE 닫힘 10줄 손상)
  - ② 그 외 파일(Python 라인 수 무관, ES Module JS 등)은 Edit 허용
  - ③ Edit 전 **반드시 수정 대상 ±20줄 Read** (맥락 누락 방지)
  - ④ Edit 후 **즉시 syntax check**:
      - Python: `python -m py_compile <file>`
      - JS:     `node --check <file>`
  - ⑤ Edit 후 **즉시 `git diff <file>` 확인** (의도치 않은 변경 감지)
  - ⑥ 1000줄 이상 파일 Edit 시 **사전 `.bak` 백업 권장**:
      ```bash
      cp <file> <file>.bak.$(date +%Y%m%d-%H%M%S)
      ```
  - 📌 patch 스크립트는 (a) ABSOLUTE EDIT BAN 파일 또는 (b) 동일 패턴 다회 적용 시에만 작성 (1회용 patch 양산 금지)
- **Rule 6** — git commit/push은 Windows CMD에서만 (VM 금지)
- **방지책 ②** — 코드 + 주석 먼저 읽고 수정 (추측 금지) — Rule 5 ③과 통합
- **방지책 ④** — 세션 시작 시 py_compile + node --check 전수검사 — Rule 5 ④와 통합
  - 최근 통과 기록: 2026-05-17 Python 34/34, JS 22/22 ✅
- 색상/폰트 → `design-tokens.css` 변수만 (하드코딩 금지)

## STATUS 설계 (확정 2026-05-11)
```
PENDING   → 포트 입항, 창고 미반입 (파싱 직후)
AVAILABLE → 창고 반입 확정 (재고 집계 시작)
RESERVED  → 배정됨
PICKED    → 출고 작업 중 (취소 가능)
SOLD      → 차량 출발 = 거래 종료 (OUTBOUND 흡수, 취소 불가)
RETURN    → 반품
```
- `movement_type='OUTBOUND'` (stock_movement 이동 유형) — STATUS 아님, 유지
- `port_date` / `inbound_type('DIRECT'|'BOND')` 컬럼 inventory 테이블에 추가됨

## CURRENT STATE (2026-05-17)
- ✅ Phase 0 DB 복구 — sqm_inventory_pre_migrate_20260516_214211.db 교체, WAL 삭제
- ✅ Phase 1 Sprint A — showToast warn→warning(3), sqm-table→data-table(2), width:32→36px(12), 영문 빈메시지→한글(6) [scripts/patch_schema_a.py]
- ✅ Phase 2 Sprint B — sqmConfirm 추상화 래퍼 + 69곳 confirm→sqmConfirm, Loading…→로딩중(25곳) [scripts/patch_schema_b.py]
- ✅ Phase 3 D1 — window.SQM_STATUS_MAP 글로벌 상수 + sqm-inline.js statusColor 삼항 2곳 제거 [scripts/patch_schema_d1.py]
- ✅ Phase 4 Sprint C — Playwright 회귀 테스트 스크립트 생성 (tests/sqm_regression.spec.js); hex 자동변환 보류 (JS↔CSS 팔레트 불일치 → 수동 스프린트 필요)
- 🎯 다음: git commit(Windows CMD) → EXE 빌드

## BACKLOG (우선순위 순)
- **🥇 git commit** — Windows CMD에서: Phase 0~4 변경 내용 커밋 (Rule 6)
- **🥈 EXE 빌드 (Phase 5)** — PyInstaller 패키징
- **🥉 Playwright 회귀 실행** — `npx playwright test tests/sqm_regression.spec.js` (앱 실행 후)
- **P2-4 정합성 자동 수정 버튼** — /api/integrity/check 결과 일괄 SQL 처리
- **P2-5 PyWebView 디버그 모드 토글** — 운영(F12 OFF) vs 개발(F12 ON) 분기
- **hex 색상 CSS 변수화** — JS/CSS 팔레트 통일 후 재시도 (Sprint C 이월)

## REFERENCES (필요 시 로드)
- `@docs/Codex/Codex.layer2.md` — LAYER 2 작업 상세
- `@docs/Codex/Codex.test.md` — pytest / Playwright
- `@docs/Codex/Codex.history.md` — 학습 로그 + 사고 이력
- `@docs/Codex/Codex.plugins.md` — Codex CLI 9개 플러그인 + 4모드
- `@docs/Codex/Codex.full.md` — 원본 백업
- `@WORK_ORDER_P4P5P7P10_20260507.md` — 작업 지시서

## DON'T
- v864.2 원본 수정 (`engine_modules/`, `features/`, `parsers/`, `utils/`)
- Linux mount(VM)에서 git 작업
- 사과 / 장황한 설명 / 추측

## 용어 · 협업 — 「루비」
- **루비**: 사용자가 Cursor/이 AI를 부르는 **애칭**(호칭). 예전 문서의 `RUBY PERSONA` 응답 템플릿 이름과는 **다름**.
- **루비 제안대로**: 별도 지시가 없으면 AI가 제안한 순서·도구·절차·우선순위를 **기본으로 따름**. (이 파일의 **CORE RULES / DON'T**, `AGENTS.md`, 방지책과 **충돌하면 프로젝트 규칙 우선**.)

> 과거 `[Question][Intent][Response]`·비유·영/베트남어 고정 포맷은 **쓰지 않음** — 「루비」는 애칭만 해당.
