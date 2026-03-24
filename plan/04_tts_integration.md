# 04 — TTS 파이프라인 완결

## 현재 미완성 항목

### 1. 토큰이 TTS JSON에 없음

`prototype/images/tokens/`는 Step 1에서 생성되지만,
Step 2는 `cards/` 폴더만 순회하므로 토큰 이미지가 TTS 세이브 파일에 포함되지 않는다.
토큰 이미지는 생성되지만 TTS에서 쓸 수 없는 죽은 산출물.

### 2. 보드 Transform 하드코딩

```python
# build.py step4
'scaleX': 20.0, 'scaleY': 1.0, 'scaleZ': 15.0,
```

`main_board.json`에 `width: 2400, height: 1800`이 있지만 무시된다.
보드 크기가 바뀌면 코드도 수동으로 고쳐야 한다.

---

## 제안

### 1. 토큰 TTS 오브젝트 추가

TTS에서 토큰은 `Custom_Token` 타입으로 추가한다.
플레이어별로 색상이 다르므로 각 토큰 이미지를 개별 오브젝트로 배치.

```python
# handlers/token.py
def create_tts_objects(self, ...) -> list[dict]:
    objects = []
    for token in self.token_data['tokens']:
        img_url = f"{GITHUB_RAW}/tokens/{token['id']}.png"
        objects.append({
            'GUID': _make_guid(f"token:{token['id']}"),
            'Name': 'Custom_Token',
            'Transform': {
                'posX': ..., 'posY': 1.0, 'posZ': ...,
                'scaleX': 0.5, 'scaleY': 0.5, 'scaleZ': 0.5,
            },
            'Nickname': token['description'],
            'CustomImage': {
                'ImageURL': img_url,
                'ImageSecondaryURL': img_url,
            },
            'Tags': ['token', token['type']],
        })
    return objects
```

초기 배치 좌표는 `player_tokens.json`에 필드로 추가하거나 자동 계산:

```json
{
  "id": "influence_red",
  "tts_position": { "x": -8, "z": 6 }
}
```

### 2. 보드 Transform 자동 계산

```python
# 1 TTS unit = 몇 픽셀인지 상수화
PX_PER_TTS_UNIT = 120

scale_x = board_info['width']  / PX_PER_TTS_UNIT   # 2400 / 120 = 20
scale_z = board_info['height'] / PX_PER_TTS_UNIT    # 1800 / 120 = 15
```

`main_board.json`의 `width`/`height`가 바뀌면 TTS 스케일도 자동 반영된다.
`PX_PER_TTS_UNIT`은 `config.py`에 상수로 정의.

### 3. TTS 배치 좌표 관리

현재 덱 배치 좌표가 `build.py`에 하드코딩:

```python
deck_positions = [
    (-6, 1, -5), (-3, 1, -5), (0, 1, -5), (3, 1, -5),
    ...
]
```

컴포넌트가 늘어나면 위치가 겹칠 수 있다.
각 핸들러가 자신의 TTS 초기 위치를 선언하는 방식:

```python
class CardDeckHandler:
    DEFAULT_POSITION = (-6, 1, -5)   # 덱별로 offset 적용
```

또는 `data/tts_layout.json`으로 TTS 씬 레이아웃을 따로 관리.

---

## 구현 순서

1. 토큰 이미지 → `deploy/images/tokens/` 경로로 배포 복사 (Step 3 확장)
2. `handlers/token.py` — `Custom_Token` TTS 오브젝트 생성
3. 보드 Transform → `PX_PER_TTS_UNIT` 기반 자동 계산
4. 덱 배치 좌표 → `data/tts_layout.json` 또는 핸들러별 DEFAULT_POSITION
