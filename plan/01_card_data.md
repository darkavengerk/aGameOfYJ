# 01 — 카드 스키마 재설계 + 레이아웃 시스템 통합

## 문제

### 레이아웃 이중 구조

현재 카드 렌더링 경로가 두 가지로 분리되어 있다.

| 카드 타입 | 렌더링 방식 | 레이아웃 변경 시 |
|-----------|------------|-----------------|
| policy, event | `data_generator.py` Python 하드코딩 | Python 수정 |
| noron/soron_gapja | `gapja_cards.json` + `card_layout_engine.py` | JSON 수정 |

새 카드 타입 추가 시 어느 경로를 써야 하는지 불명확하고, 레이아웃을 바꾸려면 항상 코드가 필요하다.

### 카드 스키마 미숙

현재 `policy_cards.json`:
```json
{
  "content": "당파 간 균형을 맞춰 정국 안정. 영향력 2 획득.",
  "cost": { "influence": 1 },
  "effect": { "influence": 2 }
}
```

- `content`(자유 텍스트)와 `effect`(구조화 데이터)가 동기화되어야 한다 — 하나 수정하면 둘 다 고쳐야 함
- 특수능력 추가 시 담을 필드가 없어 임시 필드가 생김
- flavor text, 태그, 복수 효과 등 게임이 복잡해질수록 스키마가 계속 임시방편으로 늘어남

---

## 제안

### 1. 폴더 구조 변경

```
data/
  layouts/
    standard_card.json     ← policy, event 등 기본형 레이아웃
    gapja_card.json        ← 현재 gapja_cards.json 이동
    character_card.json    ← 미래 인물 카드 레이아웃
  cards/
    policy_cards.json
    event_cards.json
    noron_gapja.json
    soron_gapja.json
  board/
    main_board.json
  tokens/
    player_tokens.json
```

### 2. 카드 JSON에 레이아웃 참조 추가

```json
{
  "type": "policy_cards",
  "layout": "standard_card",    ← layouts/ 폴더의 파일명 참조
  "cards": [ ... ]
}
```

렌더러가 이 필드를 읽어 `layouts/standard_card.json`을 로드한다.
**새 카드 타입 추가 = JSON 파일 추가만으로 완결. Python 코드 수정 불필요.**

### 3. 구조화된 카드 스키마

```json
{
  "id": "policy_001",
  "title": "탕평책",
  "flavor_text": "영조가 당파를 초월한 인재 등용을 선언하다.",
  "cost": [
    { "type": "influence", "amount": 1 }
  ],
  "effects": [
    { "type": "gain", "resource": "influence", "amount": 2 }
  ],
  "special_ability": {
    "trigger": "on_play",
    "name": "균형의 지혜",
    "description": "이 카드를 낼 때 다른 파벌 카드 1장을 버려 영향력 1을 추가 획득한다."
  },
  "tags": ["policy", "court"]
}
```

**핵심 변화:**
- `effects` 배열 → 렌더러가 비용/효과 텍스트를 자동 생성. 수치만 바꾸면 카드 텍스트가 자동 갱신됨
- `flavor_text` 분리 → 배경 설명과 게임 효과를 명확히 구분
- `special_ability` 표준 필드 → 특수능력이 있는 카드/없는 카드를 일관되게 처리
- `tags` → 나중에 필터링, TTS 스크립팅, 편집기 분류에 활용

`effects` 복수 구조는 `"influence 1 획득 + knowledge 1 획득"` 같은 복합 효과를 자연스럽게 지원한다.

### 4. `standard_card.json` 레이아웃 예시

```json
{
  "type": "standard_layout",
  "elements": {
    "title": {
      "position": { "x": "center", "y": 30 },
      "font": { "size": 24, "weight": "bold" }
    },
    "flavor_text": {
      "position": { "x": 20, "y": 80 },
      "font": { "size": 12, "weight": "normal" },
      "color": "#654321",
      "max_width_ratio": 0.9
    },
    "effects": {
      "position": { "x": 20, "y": "auto" },
      "font": { "size": 13, "weight": "normal" }
    },
    "special_ability": {
      "position": { "x": "center", "y": "bottom", "offset": 100 },
      "box": { "height": 80, "background": "#F5F5DC",
               "border": { "color": "#8B4513", "width": 2 }, "margin": 20 },
      "font": { "size": 12 }
    },
    "cost_badge": {
      "position": { "x": "right", "y": 20, "margin": 50 },
      "font": { "size": 14, "weight": "bold" }
    }
  }
}
```

---

## 구현 순서

1. `data/layouts/` 폴더 생성, `gapja_cards.json` 이동 → `data/layouts/gapja_card.json`
2. `standard_card.json` 레이아웃 작성
3. `card_layout_engine.py`에 `StandardCardLayout` 클래스 추가 (기존 `GapjaCardLayout` 패턴 참고)
4. `LayoutFactory`에 `"standard_layout"` 등록
5. `data_generator.py`의 하드코딩 제거 → `CardRenderer` 통해 단일 렌더링 경로로 통합
6. `policy_cards.json`, `event_cards.json`에 `"layout": "standard_card"` 추가
7. 카드 스키마 마이그레이션 (기존 `content` → `flavor_text` + `effects` 분리)

---

## 기대 효과

| 작업 | 이전 | 이후 |
|------|------|------|
| 새 카드 타입 추가 | Python 코드 수정 필요 | JSON 파일 추가만으로 완결 |
| 카드 수치 변경 | `effect` + `content` 두 곳 수정 | `effects[].amount` 한 곳만 수정 |
| 레이아웃 조정 | Python 좌표 수정 | JSON position 수정 |
| 특수능력 추가 | 스키마에 필드 없어 임시방편 | `special_ability` 표준 필드 사용 |
