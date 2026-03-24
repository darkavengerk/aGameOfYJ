# 02 — 빌드 파이프라인 개선

## 문제

### build.py 단일 파일 문제

`build.py`는 770줄 단일 파일에 Step 1~5가 모두 들어있다.
새 컴포넌트 타입이 추가될 때마다:

- Step 1: 이미지 생성 로직 추가
- Step 2: 시트 생성에 포함될지 결정 및 코드 추가
- Step 4: TTS JSON에 오브젝트 추가
- Step 5: 미리보기 HTML 갱신

각 Step이 서로 다른 컴포넌트를 분산 처리하고, 어디서 무엇을 처리하는지 추적하기 어렵다.
컴포넌트가 늘어날수록 `build.py`가 끝없이 커진다.

### 증분 빌드 없음

`탕평책` 텍스트 한 글자를 수정하면:
1. 정책 카드 4장 전부 재생성
2. 갑자 카드 120장 전부 재생성
3. 보드 재생성
4. 모든 시트 재합성
5. TTS JSON + HTML 재생성

카드 수가 늘어날수록 CI 빌드 시간이 선형 증가한다.
플레이테스트 중 텍스트를 반복 수정할 때 특히 체감된다.

---

## 제안

### 1. ComponentHandler 등록 패턴

각 컴포넌트 타입이 자신의 빌드 로직을 캡슐화한다.

```python
# prototype/scripts/handlers/base.py
class ComponentHandler:
    def generate_images(self) -> list[str]:
        """PNG 경로 목록 반환"""
        raise NotImplementedError

    def create_tts_objects(self, sheet_info: dict) -> list[dict]:
        """TTS ObjectState 딕셔너리 목록 반환"""
        raise NotImplementedError

    def get_preview_items(self, sheet_info: dict) -> list[dict]:
        """미리보기 HTML용 아이템 목록 반환"""
        raise NotImplementedError
```

```python
# prototype/scripts/handlers/card_deck.py
class CardDeckHandler(ComponentHandler):
    def __init__(self, deck_name: str):
        self.deck_name = deck_name
    # ... 제네릭 구현
```

```python
# build.py — 핵심이 컴포넌트 등록 목록 관리만으로 축소
HANDLERS = [
    CardDeckHandler('policy_cards'),
    CardDeckHandler('event_cards'),
    GapjaHandler('noron_gapja'),
    GapjaHandler('soron_gapja'),
    BoardHandler('main_board'),
    TokenHandler('player_tokens'),
    # 새 타입 추가 = 여기 한 줄
]

def build():
    all_images   = [img for h in HANDLERS for img in h.generate_images()]
    tts_objects  = [obj for h in HANDLERS for obj in h.create_tts_objects(...)]
    preview_items = [item for h in HANDLERS for item in h.get_preview_items(...)]
    ...
```

`CardDeckHandler`가 제네릭하게 구현되어 있으면,
`character_cards.json`을 추가할 때 `CardDeckHandler('character_cards')` 한 줄만 추가하면 된다.
커스텀 레이아웃이 필요한 타입만 새 핸들러 클래스를 만든다.

### 2. 해시 기반 증분 빌드

```python
# .build_cache.json (gitignore에 추가)
{
  "policy_001": {
    "input_hash": "a3f9c2...",   ← 카드 JSON + 레이아웃 config를 합산한 해시
    "output_path": "prototype/images/cards/policy_cards/policy_001.png",
    "built_at": "2026-03-24T10:00:00"
  },
  ...
}
```

빌드 시 각 카드의 입력 데이터(JSON 내용 + 레이아웃 config 파일)를 해시해서 캐시와 비교:

```python
def should_rebuild(card_id: str, input_hash: str) -> bool:
    cached = cache.get(card_id)
    if not cached:
        return True
    if cached['input_hash'] != input_hash:
        return True
    if not os.path.exists(cached['output_path']):
        return True
    return False
```

**기대 효과:**
- 120장 중 1장 수정 → 1장만 재렌더링
- 레이아웃 config 수정 → 해당 레이아웃을 쓰는 카드만 재렌더링
- CI에서도 효과적: 캐시를 GitHub Actions artifact로 유지하면 연속 빌드가 빨라짐

### 3. 캐시 무효화 전략

| 변경 종류 | 재빌드 범위 |
|-----------|------------|
| 카드 JSON 특정 항목 수정 | 해당 카드 1장 |
| 레이아웃 JSON 수정 | 해당 레이아웃을 참조하는 모든 카드 |
| config.py (색상, 폰트) 수정 | 전체 |
| `--force` 플래그 | 전체 |

---

## 폴더 구조 변경

```
prototype/
  scripts/
    handlers/
      __init__.py
      base.py
      card_deck.py
      gapja.py
      board.py
      token.py
    card_layout_engine.py
    config.py
    utils.py
    data_generator.py     ← CardDeckHandler로 흡수 후 제거 가능
    gapja_generator.py    ← GapjaHandler로 흡수 후 제거 가능
```

---

## 구현 순서

1. `handlers/base.py` — `ComponentHandler` 추상 클래스 작성
2. `handlers/card_deck.py` — `data_generator.py` 로직 이전
3. `handlers/gapja.py` — `gapja_generator.py` 로직 이전
4. `handlers/board.py`, `handlers/token.py`
5. `build.py` 리팩토링 — `HANDLERS` 목록 기반으로 축소
6. `.build_cache.json` 증분 빌드 구현
7. GitHub Actions: `--force` 플래그 없으면 캐시 사용, 첫 빌드나 config 변경 시 전체 빌드
