# 영조의나라 보드게임 프로젝트

## 프로젝트 개요
제2차 히트 게임즈 보드게임 공모전 2차 심사 제출을 위한 프로토타입 및 규칙서 개발 프로젝트

## 게임 정보
- **테마:** 조선시대 영조 시대 정치 보드게임
- **플레이 시간:** 60-90분
- **플레이어 수:** 2-4인
- **목표:** 한국적 정치 딜레마 체험과 전략적 결정

## 제출 기한
- **마감일:** 2025년 8월 23일
- **제출물:** 
  - Tabletop Simulator 프로토타입 (.json)
  - 완성된 규칙서 (PDF)

## 프로젝트 구조
```
영조보드게임/
├── data/                   # 게임 데이터 (JSON)
│   ├── cards/             # 카드 데이터
│   ├── tokens/            # 토큰 데이터
│   └── board/             # 보드 데이터
├── prototype/             # 프로토타입 관련
│   ├── images/            # 생성된 이미지 파일들
│   ├── scripts/           # 이미지 생성 스크립트
│   └── tabletop/          # Tabletop Simulator 파일
├── rulebook/              # 규칙서 관련
│   ├── src/               # 마크다운 소스
│   ├── build/             # 빌드된 HTML/PDF
│   └── assets/            # 규칙서 이미지 자산
└── tools/                 # 자동화 도구들
```

## 데이터 기반 시스템

### 데이터 구조
- **data/cards/**: 카드 정보를 JSON으로 관리
  - `policy_cards.json`: 정책 카드 데이터
  - `event_cards.json`: 사건 카드 데이터
- **data/tokens/**: 토큰 정보를 JSON으로 관리
  - `player_tokens.json`: 플레이어 토큰 데이터
- **data/board/**: 보드 정보를 JSON으로 관리
  - `main_board.json`: 메인 보드 데이터

### 이미지 생성
데이터 폴더 구조를 그대로 유지하여 이미지 생성:
```
data/cards/policy_cards.json → images/cards/policy_cards/
data/tokens/player_tokens.json → images/tokens/player_tokens/
data/board/main_board.json → images/board/
```

## 개발 환경
- Python 3.9+
- Pillow (이미지 생성)
- Markdown (규칙서 작성)
- Jinja2 (템플릿 엔진)
- JSON (데이터 관리)

## 빌드 명령어

### 데이터 기반 빌드 (권장)
```bash
# 전체 빌드 (데이터 기반)
python tools/build_data.py

# 이미지만 생성 (데이터 기반)
python prototype/scripts/data_generator.py
```

### 기존 빌드 (하위 호환성)
```bash
# 전체 빌드 (하드코딩)
python tools/build.py

# 이미지만 생성 (하드코딩)
python tools/quick_build.py
```

## 주요 기능
1. **데이터 분리:** 게임 컴포넌트 정보를 JSON으로 별도 관리
2. **자동 이미지 생성:** 데이터를 기반으로 카드, 토큰, 보드 이미지 자동 생성
3. **폴더 구조 유지:** 데이터 폴더 구조를 이미지 폴더 구조에 그대로 반영
4. **규칙서 자동화:** 구성품 목록 동기화, HTML/PDF 생성
5. **Tabletop Simulator 연동:** JSON 세이브 파일 자동 생성

## 데이터 수정 방법

### 카드 추가
1. `data/cards/` 폴더의 해당 JSON 파일에 카드 정보 추가
2. `python tools/build_data.py` 실행

### 토큰 수정
1. `data/tokens/player_tokens.json` 파일 수정
2. `python tools/build_data.py` 실행

### 보드 변경
1. `data/board/main_board.json` 파일 수정
2. `python tools/build_data.py` 실행

## 주요 특징
- **코드와 데이터 분리:** 게임 규칙 변경 시 JSON 파일만 수정
- **확장성:** 새로운 카드, 토큰, 보드를 데이터로 쉽게 추가
- **자동화:** 데이터 변경 시 모든 산출물 자동 업데이트
- **일관성:** 데이터 기반으로 모든 컴포넌트의 일관성 유지
