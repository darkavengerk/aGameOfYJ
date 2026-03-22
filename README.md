# 영조의나라 보드게임 프로젝트

## 게임 정보
- **테마:** 조선시대 영조 시대 정치 보드게임
- **플레이어 수:** 2–4인
- **플레이 시간:** 60–90분

---

## 빠른 시작

```bash
pip install Pillow
python build.py
```

`deploy/` 폴더에 Tabletop Simulator용 파일이 생성됩니다.

---

## 프로젝트 구조

```
aGameOfYJ/
├── build.py                  # 통합 빌드 스크립트 (진입점)
├── data/                     # 게임 데이터 (JSON)
│   ├── cards/                # 카드 데이터
│   │   ├── policy_cards.json
│   │   ├── event_cards.json
│   │   ├── noron_gapja.json  # 노론 60갑자 카드 (60장)
│   │   ├── soron_gapja.json  # 소론 60갑자 카드 (60장)
│   │   └── gapja_cards.json  # 갑자 카드 레이아웃 설정
│   ├── tokens/
│   │   └── player_tokens.json
│   └── board/
│       └── main_board.json
├── prototype/
│   └── scripts/              # 이미지 생성 모듈
│       ├── config.py         # 카드 크기·색상·폰트 설정
│       ├── data_generator.py # 정책·사건·토큰·보드 생성
│       ├── gapja_generator.py# 60갑자 카드 생성
│       └── card_layout_engine.py  # 갑자 카드 레이아웃 엔진
├── docs/
│   └── 생성규칙.md           # Tabletop Simulator 이미지 규칙
├── deploy/                   # ⚠ 자동 생성 (gitignore됨)
│   ├── index.html            # 생성 파일 미리보기 페이지
│   ├── yeongjo_kingdom.json  # TTS 세이브 파일
│   └── images/               # TTS용 카드 시트·보드 이미지
└── .github/
    └── workflows/
        └── build.yml         # GitHub Actions 자동 빌드
```

---

## 빌드 파이프라인

`python build.py` 한 번으로 아래 5단계가 순서대로 실행됩니다.

| Step | 작업 | 출력 |
|------|------|------|
| 1 | 개별 카드·보드·토큰 이미지 생성 | `prototype/images/` |
| 2 | TTS 카드 시트 생성 | `deploy/images/*.jpg` |
| 3 | 보드 배포 이미지 변환 | `deploy/images/main_board.jpg` |
| 4 | TTS 세이브 파일 생성 | `deploy/yeongjo_kingdom.json` |
| 5 | 미리보기 페이지 생성 | `deploy/index.html`, `index.html` |

### TTS 카드 시트 규칙 (`docs/생성규칙.md` 준수)
- 최대 10×7 그리드 (70슬롯), **마지막 슬롯 = 숨김 카드**
- RGB 모드 JPEG, 파일당 2MB 이하 (초과 시 품질 자동 조정)
- CustomDeck: `FaceURL` / `BackURL` / `NumWidth` / `NumHeight` 시트와 정확히 일치
- 6자리 고유 GUID 자동 생성, URL은 `raw.githubusercontent.com` 형식

---

## GitHub Actions 자동 배포

`master` 브랜치에 push하면 GitHub Actions가 자동으로 빌드 후 `deploy/` 를 커밋합니다.

```
코드 push → Actions 실행 → python build.py → deploy/ 커밋 → TTS 로드 가능
```

### 초기 설정 (1회)

저장소 **Settings → Actions → General → Workflow permissions**
→ **"Read and write permissions"** 선택 후 저장

### 확인 방법

저장소 **Actions 탭** → "Build TTS Deploy Assets" 워크플로에서 실행 로그 확인

---

## 데이터 수정 방법

### 카드 추가·수정
`data/cards/` 의 JSON 파일을 수정한 뒤 push하면 Actions가 자동으로 반영합니다.

```jsonc
// policy_cards.json 예시
{
  "type": "policy_cards",
  "cards": [
    { "id": "policy_001", "title": "탕평책", "content": "..." }
  ]
}
```

### 60갑자 카드 레이아웃 변경
`data/cards/gapja_cards.json` 의 `layout` 섹션에서 각 요소의 위치·폰트 크기를 조정합니다.

---

## 개발 환경

- Python 3.9+
- [Pillow](https://pillow.readthedocs.io/) — 이미지 생성
- 한글 폰트: 시스템에서 자동 탐색 (맑은 고딕 / WenQuanYi / IPA Gothic / Noto CJK)
