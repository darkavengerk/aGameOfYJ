#!/usr/bin/env python3
"""
영조의나라 통합 빌드 스크립트
실행 순서:
  Step 1 - 개별 이미지 생성  (카드 · 토큰 · 보드)
  Step 2 - TTS 카드 시트 생성  (생성규칙.md 준수)
  Step 3 - 보드 배포 이미지 생성
  Step 4 - TTS JSON 세이브 파일 생성
  Step 5 - deploy/index.html 생성 (미리보기 페이지)
모든 배포 파일은 deploy/ 폴더에 저장됩니다.
"""

import os
import sys
import json
import math
import hashlib
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# ─── 경로 설정 ────────────────────────────────────────────────
PROJECT_ROOT     = os.path.dirname(os.path.abspath(__file__))
PROTOTYPE_SCRIPTS = os.path.join(PROJECT_ROOT, 'prototype', 'scripts')
DATA_DIR         = os.path.join(PROJECT_ROOT, 'data')
PROTO_IMAGES_DIR = os.path.join(PROJECT_ROOT, 'prototype', 'images')
DEPLOY_DIR       = os.path.join(PROJECT_ROOT, 'deploy')
DEPLOY_IMAGES    = os.path.join(DEPLOY_DIR, 'images')

sys.path.insert(0, PROTOTYPE_SCRIPTS)

from config import KOREAN_FONT  # 폰트 탐색 로직은 config.py 에서 일원화
from handlers import CardDeckHandler, GapjaHandler, BoardHandler, TokenHandler

# ─── 컴포넌트 핸들러 등록 ─────────────────────────────────────
# 새 컴포넌트 추가 = 이 목록에 한 줄 추가
HANDLERS = [
    CardDeckHandler('policy_cards'),
    CardDeckHandler('event_cards'),
    GapjaHandler('noron_gapja'),
    GapjaHandler('soron_gapja'),
    BoardHandler('main_board'),
    TokenHandler('player_tokens'),
]

# ─── 증분 빌드 캐시 ───────────────────────────────────────────
_BUILD_CACHE_PATH = os.path.join(PROJECT_ROOT, '.build_cache.json')


def _load_build_cache() -> dict:
    try:
        with open(_BUILD_CACHE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_build_cache(cache: dict):
    with open(_BUILD_CACHE_PATH, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

# ─── GitHub 설정 ─────────────────────────────────────────────
GITHUB_USER   = 'darkavengerk'
GITHUB_REPO   = 'aGameOfYJ'
GITHUB_PAGES  = f'https://{GITHUB_USER}.github.io/{GITHUB_REPO}'
GITHUB_RAW    = f'{GITHUB_PAGES}/images'   # GitHub Pages 서빙 URL

# ─── TTS 스케일 상수 (생성규칙.md §3) ────────────────────────
PX_PER_TTS_UNIT = 120   # 1 TTS 유닛 = 120px (보드 스케일 자동 계산용)

# ─── TTS 시트 규칙 (생성규칙.md §2) ──────────────────────────
MAX_COLS       = 10    # 최대 가로 칸 수
MAX_ROWS       = 7     # 최대 세로 칸 수  →  최대 70장/시트
CARD_W         = 300   # 개별 카드 픽셀 너비
CARD_H         = 420   # 개별 카드 픽셀 높이
JPEG_QUALITY   = 85    # 초기 JPEG 압축률
MAX_FILE_MB    = 2.0   # 파일당 최대 크기 (MB)

# ─── GUID 유니크 보장 (생성규칙.md §3) ───────────────────────
_used_guids: set = set()

def _make_guid(context: str) -> str:
    """context 문자열 기반 결정론적 6자리 GUID 생성.
    같은 context는 항상 같은 GUID를 반환하므로 빌드 간 불필요한 diff가 발생하지 않는다.
    충돌 시 :{n} suffix를 붙여 재시도.
    """
    for i in range(100):
        key = context if i == 0 else f'{context}:{i}'
        g = hashlib.sha1(key.encode()).hexdigest()[:6]
        if g not in _used_guids:
            _used_guids.add(g)
            return g
    raise RuntimeError(f'GUID 충돌 해소 실패: {context}')


# ═══════════════════════════════════════════════════════════════
#  Step 1 – 개별 이미지 생성 (ComponentHandler 기반)
# ═══════════════════════════════════════════════════════════════
def step1_generate_images(force: bool = False):
    """HANDLERS 목록의 각 핸들러가 자신의 이미지를 생성한다.
    증분 빌드: 입력 해시가 동일하고 출력 파일이 존재하면 건너뜀.
    force=True 이면 캐시를 무시하고 전부 재생성.
    """
    print('\n=== Step 1: 개별 이미지 생성 ===')
    cache = _load_build_cache()

    for handler in HANDLERS:
        name = type(handler).__name__
        label = getattr(handler, 'deck_name',
                getattr(handler, 'faction_name',
                getattr(handler, 'board_name',
                getattr(handler, 'token_name', '?'))))
        print(f'  [{name}] {label}')
        handler.generate_images(cache, force=force)

    _save_build_cache(cache)
    print('개별 이미지 생성 완료')


# ═══════════════════════════════════════════════════════════════
#  Step 2 – TTS 카드 시트 생성
# ═══════════════════════════════════════════════════════════════
def _load_png_paths(directory: str) -> list:
    """디렉터리에서 PNG 파일 경로 목록을 정렬하여 반환"""
    if not os.path.isdir(directory):
        return []
    return sorted(
        os.path.join(directory, f)
        for f in os.listdir(directory)
        if f.lower().endswith('.png')
    )


def _make_hidden_card(w: int, h: int) -> Image.Image:
    """시트 마지막 슬롯용 숨김 카드 이미지 생성 (생성규칙.md §2 참조)"""
    img = Image.new('RGB', (w, h), '#2C1810')
    draw = ImageDraw.Draw(img)
    draw.rectangle([6, 6, w - 6, h - 6], outline='#D4AF37', width=3)
    try:
        font = ImageFont.truetype(KOREAN_FONT, 36) if KOREAN_FONT else ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()
    text = '영조의나라'
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((w - tw) // 2, (h - th) // 2), text, fill='#D4AF37', font=font)
    return img


def _make_back_image() -> Image.Image:
    """공용 카드 뒷면 이미지 생성"""
    img = Image.new('RGB', (CARD_W, CARD_H), '#2C1810')
    draw = ImageDraw.Draw(img)
    draw.rectangle([8, 8, CARD_W - 8, CARD_H - 8], outline='#D4AF37', width=4)
    draw.rectangle([16, 16, CARD_W - 16, CARD_H - 16], outline='#8B4513', width=2)
    cx, cy = CARD_W // 2, CARD_H // 2
    r = 45
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline='#D4AF37', width=3)
    try:
        font = ImageFont.truetype(KOREAN_FONT, 28) if KOREAN_FONT else ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()
    text = '王'
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((CARD_W - tw) // 2, (CARD_H - th) // 2), text, fill='#D4AF37', font=font)
    return img


def _save_optimized(img: Image.Image, path: str) -> float:
    """이미지를 JPEG로 저장하며 MAX_FILE_MB 이하가 될 때까지 품질을 낮춤"""
    quality = JPEG_QUALITY
    while quality >= 50:
        img.save(path, 'JPEG', quality=quality, optimize=True)
        size_mb = os.path.getsize(path) / (1024 ** 2)
        if size_mb <= MAX_FILE_MB:
            return size_mb
        quality -= 5
    return os.path.getsize(path) / (1024 ** 2)


def create_sheet(card_paths: list, deck_name: str) -> dict | None:
    """
    카드 이미지 목록을 하나의 TTS 시트로 합친다.
    생성규칙.md §2 준수:
      - 마지막 슬롯 = 숨김 이미지
      - 최대 10×7 = 70 슬롯
      - RGB, JPEG, ≤2MB
    반환: {cols, rows, count, path, url}  /  카드 없으면 None
    """
    n = len(card_paths)
    if n == 0:
        return None

    # 슬롯 = 카드 수 + 숨김 1장
    total_slots = n + 1
    cols = min(MAX_COLS, total_slots)
    rows = math.ceil(total_slots / cols)

    # 최대 규격 초과 처리
    if rows > MAX_ROWS:
        max_cards = MAX_COLS * MAX_ROWS - 1
        print(f'  [!] {deck_name}: 카드 수({n}) > 최대({max_cards}), 초과분 제외')
        n = max_cards
        card_paths = card_paths[:n]
        cols, rows = MAX_COLS, MAX_ROWS
        total_slots = MAX_COLS * MAX_ROWS

    sheet_w = cols * CARD_W
    sheet_h = rows * CARD_H
    sheet = Image.new('RGB', (sheet_w, sheet_h), '#111111')

    hidden = _make_hidden_card(CARD_W, CARD_H)

    # 카드 붙여넣기
    for i, path in enumerate(card_paths):
        col = i % cols
        row = i // cols
        try:
            card_img = Image.open(path).convert('RGB').resize(
                (CARD_W, CARD_H), Image.LANCZOS
            )
        except Exception as e:
            print(f'  [!] 카드 로드 실패: {path} ({e})')
            card_img = Image.new('RGB', (CARD_W, CARD_H), '#555555')
        sheet.paste(card_img, (col * CARD_W, row * CARD_H))

    # 숨김 카드 → 마지막 슬롯
    last = n  # 0-indexed slot index
    sheet.paste(hidden, ((last % cols) * CARD_W, (last // cols) * CARD_H))

    # 저장
    os.makedirs(DEPLOY_IMAGES, exist_ok=True)
    out_path = os.path.join(DEPLOY_IMAGES, f'{deck_name}.jpg')
    size_mb = _save_optimized(sheet, out_path)
    print(f'  시트: {deck_name}.jpg  ({cols}×{rows}, {n}장, {size_mb:.2f}MB)')

    return {
        'cols': cols,
        'rows': rows,
        'count': n,
        'path': out_path,
        'url': f'{GITHUB_RAW}/{deck_name}.jpg',
    }


def step2_create_tts_sheets() -> dict:
    """Step 2: prototype/images/cards/ 하위 각 덱 폴더 → TTS 시트"""
    print('\n=== Step 2: TTS 카드 시트 생성 ===')

    deck_info: dict = {}
    cards_base = os.path.join(PROTO_IMAGES_DIR, 'cards')

    if os.path.isdir(cards_base):
        for deck_name in sorted(os.listdir(cards_base)):
            deck_dir = os.path.join(cards_base, deck_name)
            if not os.path.isdir(deck_dir):
                continue
            card_paths = _load_png_paths(deck_dir)
            if not card_paths:
                continue
            result = create_sheet(card_paths, deck_name)
            if result:
                deck_info[deck_name] = result

    # 공용 카드 뒷면
    back_path = os.path.join(DEPLOY_IMAGES, 'card_back.jpg')
    _make_back_image().save(back_path, 'JPEG', quality=90)
    print(f'  뒷면: card_back.jpg')

    return deck_info


# ═══════════════════════════════════════════════════════════════
#  Step 3 – 보드 + 토큰 배포 이미지 생성
# ═══════════════════════════════════════════════════════════════
def step3_deploy_board() -> tuple:
    """Step 3: prototype/images/{board,tokens}/ → deploy/images/
    반환: (board_info, token_info)
    """
    print('\n=== Step 3: 보드 + 토큰 배포 이미지 생성 ===')

    board_info: dict = {}
    token_info: dict = {}

    # ── 보드 이미지 ──────────────────────────────────────────
    board_src = os.path.join(PROTO_IMAGES_DIR, 'board')
    if os.path.isdir(board_src):
        for fname in sorted(os.listdir(board_src)):
            if not fname.lower().endswith('.png'):
                continue
            name = os.path.splitext(fname)[0]
            src  = os.path.join(board_src, fname)
            dst  = os.path.join(DEPLOY_IMAGES, f'{name}.jpg')

            img = Image.open(src).convert('RGB')
            size_mb = _save_optimized(img, dst)
            print(f'  보드: {name}.jpg  ({img.width}×{img.height}, {size_mb:.2f}MB)')

            board_info[name] = {
                'path': dst,
                'url': f'{GITHUB_RAW}/{name}.jpg',
                'width': img.width,
                'height': img.height,
            }
    else:
        print('  [!] 보드 이미지 없음, 건너뜀')

    # ── 토큰 이미지 ──────────────────────────────────────────
    tokens_src = os.path.join(PROTO_IMAGES_DIR, 'tokens')
    if os.path.isdir(tokens_src):
        for token_type in sorted(os.listdir(tokens_src)):
            type_dir = os.path.join(tokens_src, token_type)
            if not os.path.isdir(type_dir):
                continue
            deploy_token_dir = os.path.join(DEPLOY_IMAGES, 'tokens', token_type)
            os.makedirs(deploy_token_dir, exist_ok=True)

            for fname in sorted(os.listdir(type_dir)):
                if not fname.lower().endswith('.png'):
                    continue
                token_id = os.path.splitext(fname)[0]
                src = os.path.join(type_dir, fname)
                dst = os.path.join(deploy_token_dir, fname)

                img = Image.open(src).convert('RGB')
                img.save(dst, 'PNG')

                token_info[token_id] = {
                    'path': dst,
                    'url': f'{GITHUB_RAW}/tokens/{token_type}/{fname}',
                    'type': token_type,
                }
            print(f'  토큰: {token_type} → deploy/images/tokens/{token_type}/')

    return board_info, token_info


# ═══════════════════════════════════════════════════════════════
#  Step 4 – TTS JSON 생성
# ═══════════════════════════════════════════════════════════════
def _add_token_objects(object_states: list, token_info: dict):
    """토큰 이미지 → TTS Custom_Token 오브젝트로 변환해 object_states에 추가."""
    # 보드 옆 우측에 3열 그리드 배치
    token_ids = sorted(token_info.keys())
    cols = 3
    for idx, token_id in enumerate(token_ids):
        info = token_info[token_id]
        col = idx % cols
        row = idx // cols
        pos_x = 14.0 + col * 1.2
        pos_z = -6.0 + row * 1.2

        object_states.append({
            'GUID': _make_guid(f'token:{token_id}'),
            'Name': 'Custom_Token',
            'Transform': {
                'posX': pos_x, 'posY': 1.0, 'posZ': pos_z,
                'rotX': 0.0,   'rotY': 0.0, 'rotZ': 0.0,
                'scaleX': 0.5, 'scaleY': 0.5, 'scaleZ': 0.5,
            },
            'Nickname': token_id,
            'Description': info.get('type', ''),
            'CustomImage': {
                'ImageURL': info['url'],
                'ImageSecondaryURL': info['url'],
            },
            'Tags': ['token', info.get('type', '')],
        })


def step4_generate_tts_json(deck_info: dict, board_info: dict,
                             token_info: dict | None = None) -> str:
    """
    Step 4: Tabletop Simulator 세이브 파일 생성 (생성규칙.md §3 준수)
    - CustomDeck: FaceURL / BackURL / NumWidth / NumHeight
    - 모든 객체에 6자리 고유 GUID
    - URL = raw.githubusercontent.com 경로
    """
    print('\n=== Step 4: TTS JSON 생성 ===')

    back_url = f'{GITHUB_RAW}/card_back.jpg'

    tts = {
        'SaveName': '영조의나라',
        'Date': datetime.now().isoformat(),
        'VersionNumber': '1.0',
        'GameMode': '영조의나라',
        'Table': '',
        'Sky': 'Sky_Box',
        'Note': '영조의나라 보드게임 — Tabletop Simulator 배포용',
        'Rules': '',
        'ObjectStates': [],
    }

    # ── 보드 추가 (스케일 자동 계산) ────────────────────────
    for board_name, info in board_info.items():
        scale_x = info['width']  / PX_PER_TTS_UNIT
        scale_z = info['height'] / PX_PER_TTS_UNIT

        # 스냅 포인트 — 보드 핸들러가 생성한 _snap.json 읽기
        snap_points = []
        snap_path = os.path.join(PROTO_IMAGES_DIR, 'board', f'{board_name}_snap.json')
        if os.path.exists(snap_path):
            with open(snap_path, 'r', encoding='utf-8') as _sf:
                snap_data = json.load(_sf)
            bw = snap_data['board_width']
            bh = snap_data['board_height']
            for sp in snap_data['snap_points']:
                sx = (sp['pixel_x'] - bw / 2) / PX_PER_TTS_UNIT
                sz = (sp['pixel_y'] - bh / 2) / PX_PER_TTS_UNIT
                snap_points.append({
                    'Position': {'x': round(sx, 4), 'y': 0.1, 'z': round(sz, 4)},
                    'Rotation': {'x': 0.0, 'y': 0.0, 'z': 0.0},
                    'Tags': [],
                })
            print(f'  스냅 포인트: {board_name} {len(snap_points)}개')

        board_obj = {
            'GUID': _make_guid(f'board:{board_name}'),
            'Name': 'Custom_Tile',
            'Transform': {
                'posX': 0.0, 'posY': 1.0, 'posZ': 0.0,
                'rotX': 0.0, 'rotY': 0.0, 'rotZ': 0.0,
                'scaleX': scale_x, 'scaleY': 1.0, 'scaleZ': scale_z,
            },
            'Nickname': board_name,
            'Description': '메인 보드',
            'CustomImage': {
                'ImageURL': info['url'],
                'ImageSecondaryURL': info['url'],
                'WidthScale': 0.0,
            },
            'Locked': True,
            'Tags': ['Board'],
        }
        if snap_points:
            board_obj['SnapPoints'] = snap_points
        tts['ObjectStates'].append(board_obj)

    # ── 토큰 추가 ────────────────────────────────────────────
    if token_info:
        _add_token_objects(tts['ObjectStates'], token_info)

    # ── 덱 배치 좌표 사전 설정 ───────────────────────────────
    deck_positions = [
        (-6, 1, -5), (-3, 1, -5), (0, 1, -5), (3, 1, -5),
        (6, 1, -5), (-6, 1, 5), (-3, 1, 5), (0, 1, 5),
    ]

    # ── 덱 추가 ──────────────────────────────────────────────
    for deck_idx, (deck_name, info) in enumerate(sorted(deck_info.items())):
        cols     = info['cols']
        rows     = info['rows']
        count    = info['count']
        face_url = info['url']
        pos      = deck_positions[deck_idx % len(deck_positions)]
        cdk_id   = deck_idx + 1          # CustomDeck 키 (정수)

        contained = []
        for i in range(count):
            contained.append({
                'GUID': _make_guid(f'card:{deck_name}:{i}'),
                'Name': 'Card',
                'CardID': cdk_id * 100 + i,
                'Nickname': f'{deck_name}_{i + 1:03d}',
                'Description': '',
                'Transform': {
                    'posX': 0.0, 'posY': 0.0, 'posZ': 0.0,
                    'rotX': 0.0, 'rotY': 0.0, 'rotZ': 180.0,
                    'scaleX': 1.0, 'scaleY': 1.0, 'scaleZ': 1.0,
                },
                'CustomDeck': {
                    str(cdk_id): {
                        'FaceURL': face_url,
                        'BackURL': back_url,
                        'NumWidth': cols,
                        'NumHeight': rows,
                        'BackIsHidden': True,
                        'UniqueBack': False,
                    },
                },
                'Tags': [deck_name],
            })

        tts['ObjectStates'].append({
            'GUID': _make_guid(f'deck:{deck_name}'),
            'Name': 'Deck',
            'Transform': {
                'posX': float(pos[0]), 'posY': float(pos[1]),
                'posZ': float(pos[2]),
                'rotX': 0.0, 'rotY': 0.0, 'rotZ': 0.0,
                'scaleX': 1.0, 'scaleY': 1.0, 'scaleZ': 1.0,
            },
            'Nickname': deck_name,
            'Description': f'{count}장',
            'DeckIDs': [cdk_id * 100 + i for i in range(count)],
            'CustomDeck': {
                str(cdk_id): {
                    'FaceURL': face_url,
                    'BackURL': back_url,
                    'NumWidth': cols,
                    'NumHeight': rows,
                    'BackIsHidden': True,
                    'UniqueBack': False,
                },
            },
            'ContainedObjects': contained,
            'Tags': [deck_name],
        })

    out_path = os.path.join(DEPLOY_DIR, 'yeongjo_kingdom.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(tts, f, ensure_ascii=False, indent=2)

    total_cards = sum(d['count'] for d in deck_info.values())
    print(f'  TTS JSON: yeongjo_kingdom.json')
    print(f'  덱 수: {len(deck_info)}  총 카드: {total_cards}장')
    return out_path


# ═══════════════════════════════════════════════════════════════
#  Step 5 – index.html 생성
# ═══════════════════════════════════════════════════════════════
def _render_html(deck_info: dict, board_info: dict,
                 images_dir: str, json_file: str,
                 editor_link: str = 'editor/index.html') -> str:
    """HTML 미리보기 문자열 생성.
    images_dir : 이미지 상대 경로 접두사 (e.g. 'images' 또는 'deploy/images')
    json_file  : TTS JSON 상대 경로 (e.g. 'yeongjo_kingdom.json' 또는 'deploy/...')
    """
    build_time  = datetime.now().strftime('%Y년 %m월 %d일 %H:%M:%S')
    total_cards = sum(d['count'] for d in deck_info.values())
    back_url_full = f'{GITHUB_RAW}/card_back.jpg'

    def _sheet_card(deck_name, info):
        img_rel    = f'{images_dir}/{deck_name}.jpg'
        size_label = f'{info["cols"]}×{info["rows"]} 그리드 / {info["count"]}장'
        return f'''
        <div class="card-item">
          <div class="card-header">
            <span class="item-name">{deck_name}</span>
            <span class="item-badge">{size_label}</span>
          </div>
          <a href="{img_rel}" target="_blank" title="클릭하면 원본 크기로 열림">
            <img src="{img_rel}" alt="{deck_name}" loading="lazy">
          </a>
          <div class="card-footer">
            <code>{info["url"]}</code>
          </div>
        </div>'''

    def _board_card(board_name, info):
        img_rel    = f'{images_dir}/{board_name}.jpg'
        size_label = f'{info["width"]}×{info["height"]}px'
        return f'''
        <div class="card-item">
          <div class="card-header">
            <span class="item-name">{board_name}</span>
            <span class="item-badge">{size_label}</span>
          </div>
          <a href="{img_rel}" target="_blank" title="클릭하면 원본 크기로 열림">
            <img src="{img_rel}" alt="{board_name}" loading="lazy">
          </a>
          <div class="card-footer">
            <code>{info["url"]}</code>
          </div>
        </div>'''

    sheets_html = ''.join(
        _sheet_card(name, info)
        for name, info in sorted(deck_info.items())
    )
    boards_html = ''.join(
        _board_card(name, info)
        for name, info in sorted(board_info.items())
    )
    back_img = f'{images_dir}/card_back.jpg'

    return f'''<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>영조의나라 — TTS 배포 파일</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    body {{
      font-family: 'Malgun Gothic', 'Noto Sans KR', sans-serif;
      background: #120b06;
      color: #e8d5b0;
      min-height: 100vh;
    }}

    /* ── 헤더 ── */
    header {{
      background: linear-gradient(135deg, #2c1810 0%, #4a2c1a 100%);
      border-bottom: 3px solid #d4af37;
      padding: 28px 36px 20px;
    }}
    header h1 {{ font-size: 2rem; color: #d4af37; margin-bottom: 6px; }}
    header .meta {{ color: #a07850; font-size: 0.85rem; }}

    /* ── 통계 바 ── */
    .stats-bar {{
      display: flex;
      gap: 0;
      background: #1e100a;
      border-bottom: 1px solid #3a1f10;
    }}
    .stat {{
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 14px 0;
      border-right: 1px solid #3a1f10;
    }}
    .stat:last-child {{ border-right: none; }}
    .stat-value {{ font-size: 1.8rem; font-weight: 700; color: #d4af37; }}
    .stat-label {{ font-size: 0.72rem; color: #7a5530; margin-top: 2px; }}

    /* ── 메인 ── */
    main {{ padding: 36px; }}

    section {{ margin-bottom: 52px; }}
    section h2 {{
      font-size: 1.25rem;
      color: #d4af37;
      border-bottom: 2px solid #3a1f10;
      padding-bottom: 8px;
      margin-bottom: 22px;
    }}

    /* ── 그리드 ── */
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
      gap: 18px;
    }}

    /* ── 카드 아이템 ── */
    .card-item {{
      background: #2c1810;
      border: 1px solid #3a1f10;
      border-radius: 10px;
      overflow: hidden;
      transition: border-color 0.2s, transform 0.15s;
    }}
    .card-item:hover {{
      border-color: #d4af37;
      transform: translateY(-2px);
    }}

    .card-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 9px 14px;
      background: #1a0f0a;
      border-bottom: 1px solid #3a1f10;
    }}
    .item-name {{ font-weight: 700; font-size: 0.9rem; }}
    .item-badge {{
      font-size: 0.72rem;
      color: #a07850;
      background: #3a1f10;
      padding: 2px 9px;
      border-radius: 12px;
      white-space: nowrap;
    }}

    .card-item a {{ display: block; }}
    .card-item img {{
      width: 100%;
      height: 190px;
      object-fit: contain;
      background: #0d0703;
      display: block;
      transition: opacity 0.15s;
    }}
    .card-item a:hover img {{ opacity: 0.85; }}

    .card-footer {{
      padding: 8px 14px 10px;
      background: #1a0f0a;
    }}
    .card-footer code {{
      font-size: 0.68rem;
      color: #5a8cbf;
      word-break: break-all;
      display: block;
      line-height: 1.4;
    }}

    /* ── JSON 섹션 ── */
    .json-box {{
      background: #2c1810;
      border: 1px solid #3a1f10;
      border-radius: 10px;
      padding: 22px 26px;
    }}
    .json-box p {{ color: #a07850; margin-bottom: 14px; line-height: 1.7; }}
    .json-box code {{ color: #d4af37; }}
    .dl-btn {{
      display: inline-block;
      background: #d4af37;
      color: #1a0f0a;
      text-decoration: none;
      padding: 10px 26px;
      border-radius: 6px;
      font-weight: 700;
      font-size: 0.95rem;
      transition: background 0.2s;
    }}
    .dl-btn:hover {{ background: #f0d060; }}

    /* ── 헤더 내비 ── */
    .header-nav {{
      margin-top: 10px;
    }}
    .nav-link {{
      display: inline-block;
      border: 1px solid #3a1f10;
      color: #a07850;
      text-decoration: none;
      padding: 5px 14px;
      border-radius: 6px;
      font-size: 0.82rem;
      transition: border-color .2s, color .2s;
    }}
    .nav-link:hover {{
      border-color: #d4af37;
      color: #d4af37;
    }}

    /* ── 푸터 ── */
    footer {{
      text-align: center;
      padding: 22px;
      color: #3a1f10;
      font-size: 0.78rem;
      border-top: 1px solid #1e100a;
    }}
  </style>
</head>
<body>

<header>
  <h1>영조의나라 — Tabletop Simulator 배포 파일</h1>
  <div class="meta">
    빌드: {build_time} &nbsp;|&nbsp;
    저장소: {GITHUB_USER}/{GITHUB_REPO}
  </div>
  <nav class="header-nav">
    <a href="https://github.com/{GITHUB_USER}/{GITHUB_REPO}" class="nav-link" target="_blank">← GitHub 저장소</a>
    <a href="{editor_link}" class="nav-link">카드 에디터 →</a>
  </nav>
</header>

<div class="stats-bar">
  <div class="stat">
    <span class="stat-value">{len(deck_info)}</span>
    <span class="stat-label">카드 시트</span>
  </div>
  <div class="stat">
    <span class="stat-value">{total_cards}</span>
    <span class="stat-label">총 카드 수</span>
  </div>
  <div class="stat">
    <span class="stat-value">{len(board_info)}</span>
    <span class="stat-label">보드</span>
  </div>
  <div class="stat">
    <span class="stat-value">{len(deck_info) + len(board_info) + 1}</span>
    <span class="stat-label">총 이미지</span>
  </div>
</div>

<main>

  <section>
    <h2>카드 시트 (Card Sheets)</h2>
    <div class="grid">
      {sheets_html}
    </div>
  </section>

  <section>
    <h2>보드 (Board)</h2>
    <div class="grid">
      {boards_html}
    </div>
  </section>

  <section>
    <h2>카드 뒷면 (Card Back)</h2>
    <div class="grid">
      <div class="card-item">
        <div class="card-header">
          <span class="item-name">card_back</span>
          <span class="item-badge">공용 뒷면</span>
        </div>
        <a href="{back_img}" target="_blank">
          <img src="{back_img}" alt="card_back" loading="lazy">
        </a>
        <div class="card-footer">
          <code>{back_url_full}</code>
        </div>
      </div>
    </div>
  </section>

  <section>
    <h2>TTS 세이브 파일 (Save File)</h2>
    <div class="json-box">
      <p>
        아래 파일을 Tabletop Simulator 세이브 폴더에 복사하면<br>
        게임을 바로 불러올 수 있습니다.<br>
        <code>~/Documents/My Games/Tabletop Simulator/Saves/</code>
      </p>
      <a href="{json_file}" download class="dl-btn">
        yeongjo_kingdom.json 다운로드
      </a>
    </div>
  </section>

</main>

<footer>
  영조의나라 &copy; {datetime.now().year} &nbsp;|&nbsp;
  Tabletop Simulator 배포용 자동 빌드
</footer>

</body>
</html>
'''


def step5_generate_index_html(deck_info: dict, board_info: dict) -> str:
    """Step 5: deploy/index.html 생성 (GitHub Pages 배포용)"""
    print('\n=== Step 5: index.html 생성 ===')

    deploy_html = _render_html(deck_info, board_info,
                               images_dir='images',
                               json_file='yeongjo_kingdom.json',
                               editor_link='../editor/index.html')
    out_path = os.path.join(DEPLOY_DIR, 'index.html')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(deploy_html)

    print(f'  deploy/index.html 생성 완료')
    return out_path


# ═══════════════════════════════════════════════════════════════
#  메인
# ═══════════════════════════════════════════════════════════════
def main():
    force = '--force' in sys.argv

    print('=' * 60)
    print('영조의나라 통합 빌드 시작')
    print(f'출력 경로: {DEPLOY_DIR}')
    if force:
        print('모드: 강제 전체 재빌드 (--force)')
    else:
        print('모드: 증분 빌드 (변경된 항목만 재생성)')
    print('=' * 60)

    os.makedirs(DEPLOY_DIR, exist_ok=True)
    os.makedirs(DEPLOY_IMAGES, exist_ok=True)

    start = datetime.now()

    try:
        step1_generate_images(force=force)
        deck_info              = step2_create_tts_sheets()
        board_info, token_info = step3_deploy_board()
        step4_generate_tts_json(deck_info, board_info, token_info)
        step5_generate_index_html(deck_info, board_info)

        elapsed = (datetime.now() - start).total_seconds()
        total   = sum(d['count'] for d in deck_info.values())

        print(f'\n{"=" * 60}')
        print(f'빌드 완료!  ({elapsed:.1f}초)')
        print(f'')
        print(f'  deploy/')
        print(f'  ├─ index.html              ← 미리보기 페이지')
        print(f'  ├─ yeongjo_kingdom.json    ← TTS 세이브 파일')
        print(f'  └─ images/')
        for name in sorted(deck_info.keys()):
            info = deck_info[name]
            print(f'     ├─ {name}.jpg  ({info["count"]}장)')
        for name in sorted(board_info.keys()):
            print(f'     ├─ {name}.jpg  (보드)')
        print(f'     └─ card_back.jpg  (뒷면)')
        print(f'')
        print(f'  카드 시트: {len(deck_info)}개 덱, 총 {total}장')
        print('=' * 60)

    except Exception as e:
        print(f'\n빌드 실패: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
