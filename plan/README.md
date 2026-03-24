# 영조의나라 — 개발 계획

## 로드맵 개요

코드 분석 및 논의를 바탕으로 정리한 개선 계획.
각 문서는 독립적으로 읽을 수 있으나, 의존 관계가 있는 항목은 아래 표에 표시.

---

## 문서 목록

| 문서 | 주제 | 우선순위 | 의존 |
|------|------|----------|------|
| [01_card_data.md](01_card_data.md) | 카드 스키마 재설계 + 레이아웃 시스템 통합 | ★★★ 높음 | 없음 |
| [02_build_pipeline.md](02_build_pipeline.md) | 증분 빌드 + 컴포넌트 핸들러 패턴 | ★★☆ 중간 | 01 완료 후 |
| [03_board_system.md](03_board_system.md) | 보드 섹션 타입 시스템 | ★★☆ 중간 | 없음 |
| [04_tts_integration.md](04_tts_integration.md) | TTS 파이프라인 완결 (토큰, 보드 스케일) | ★☆☆ 낮음 | 02 완료 후 |
| [05_build_legacy.md](05_build_legacy.md) | tools/ 레거시 빌드 스크립트 정리 | ★☆☆ 낮음 | 02 완료 후 |
| [06_web_editor.md](06_web_editor.md) | GitHub Pages 웹 에디터 + 발행 시스템 | ★★★ 높음 | 01 완료 후 |

---

## 현재 상태 요약

```
data/               ← 게임 데이터 (JSON)
prototype/scripts/  ← 이미지 생성 Python 코드
build.py            ← 빌드 오케스트레이터 (700줄+, 단일 파일)
deploy/             ← CI가 자동 생성하는 배포 산출물
```

**잘 되어 있는 것**
- JSON 데이터 분리 — 게임 내용과 렌더링 코드가 분리됨
- GitHub Actions CI — push 시 자동 빌드
- 60갑자 카드의 JSON 기반 레이아웃 (`gapja_cards.json`)

**핵심 병목**
- 일반 카드 레이아웃이 Python에 하드코딩 → 새 카드 타입마다 코드 수정 필요
- 매 빌드마다 전체 이미지 재생성 → 텍스트 한 줄 수정도 120장 전부 재렌더링
- 웹 편집 수단 없음 → 텍스트 수정도 git commit + push 필요

---

## 최종 목표 아키텍처

```
[GitHub Pages 웹 에디터]
    ↓ 카드 텍스트/능력 수정
    ↓ 발행 버튼
    ↓ GitHub Contents API로 JSON 커밋
    ↓ GitHub Actions 자동 트리거
[build.py — ComponentHandler 기반]
    ↓ 변경된 데이터만 증분 렌더링
    ↓ TTS 시트 + JSON 생성
[GitHub Pages 정적 배포]
    ↓ 미리보기 페이지 + TTS 다운로드
```
