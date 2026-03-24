# 03 — 보드 섹션 타입 시스템

## 문제

현재 `main_board.json`의 모든 섹션이 동일한 구조를 가진다:

```json
{ "id": "court", "name": "조정", "position": {...}, "size": {...}, "description": "..." }
```

렌더러(`create_board_from_data()`)는 모든 섹션을 똑같이 처리한다:
- 금색 테두리 + 이름 텍스트

`policy_track`(긴 가로 트랙)도 `court`(정사각형 영역)도 시각적으로 동일하다.
섹션 스타일을 바꾸려면 Python 코드를 수정해야 한다.

---

## 제안

### 섹션 타입 + 스타일 필드 추가

```json
{
  "sections": [
    {
      "id": "court",
      "name": "조정",
      "type": "area",
      "style": {
        "background": "#FFF8F0",
        "border_color": "#8B4513",
        "border_width": 3,
        "header_color": "#D4AF37",
        "header_height": 40
      },
      "position": { "x": 0, "y": 0 },
      "size": { "width": 800, "height": 600 },
      "description": "왕과 대신들이 활동하는 중심 공간"
    },
    {
      "id": "policy_track",
      "name": "정책 추진",
      "type": "track",
      "slots": 8,
      "slot_style": {
        "background": "#F5F0E8",
        "border_color": "#654321"
      },
      "style": {
        "background": "#EDE0C8",
        "border_color": "#8B4513",
        "border_width": 2,
        "header_color": "#D4AF37",
        "header_height": 35
      },
      "position": { "x": 0, "y": 600 },
      "size": { "width": 2400, "height": 300 }
    }
  ]
}
```

### 섹션 타입 목록

| 타입 | 용도 | 전용 속성 |
|------|------|-----------|
| `area` | 일반 구역 (조정, 지방, 외교) | 없음 |
| `track` | 진행 트랙 (정책 추진, 사건 기록) | `slots`, `slot_style` |
| `card_zone` | 카드를 올려놓는 자리 | `card_count`, `card_size` |
| `player_mat` | 플레이어별 구역 | `player_index`, `player_color` |
| `label` | 텍스트 표시만 (범례, 제목) | `text_align` |

### 렌더러 변경

```python
# 타입별 렌더 함수 분기
SECTION_RENDERERS = {
    'area':       render_area_section,
    'track':      render_track_section,
    'card_zone':  render_card_zone_section,
    'player_mat': render_player_mat_section,
    'label':      render_label_section,
}

def create_board_from_data(board_data, output_dir):
    for section in board_data['sections']:
        renderer = SECTION_RENDERERS.get(section.get('type', 'area'), render_area_section)
        renderer(draw, section)
```

새 섹션 타입 추가: 렌더 함수 하나 작성 + `SECTION_RENDERERS`에 등록.

---

## 기대 효과

| 작업 | 이전 | 이후 |
|------|------|------|
| 섹션 추가 | Python에서 위치/크기 하드코딩 후 재빌드 | JSON에 항목 추가 후 재빌드 |
| 섹션 스타일 변경 | Python 코드 수정 | JSON `style` 수정 |
| 섹션 삭제 | JSON + Python 양쪽 수정 | JSON 항목 제거만 |
| 트랙 슬롯 수 변경 | 코드에 반영되어 있지 않음 | `"slots": 8` 수정 |

---

## 향후 확장

보드가 복잡해지면 이미지(배경 텍스처, 아이콘) 지원도 고려:

```json
{
  "id": "court",
  "type": "area",
  "background_image": "assets/court_bg.png",
  "icon": "assets/crown_icon.png",
  ...
}
```

배경 이미지를 지원하면 Python 렌더링 대신 실제 아트워크를 사용할 수 있다.
이때도 JSON 필드 추가만으로 활성화되므로 구조적 변경은 불필요하다.
