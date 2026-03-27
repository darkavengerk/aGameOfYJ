"""BoardHandler — 보드 이미지 핸들러."""

import json
import os

from PIL import Image, ImageDraw, ImageFont
from config import BOARD_CONFIG, COLORS, FONTS
from handlers.base import ComponentHandler

_PROJECT_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(__file__), '..', '..', '..')
)
_DATA_DIR  = os.path.join(_PROJECT_ROOT, 'data')
_PROTO_IMG = os.path.join(_PROJECT_ROOT, 'prototype', 'images')


class BoardHandler(ComponentHandler):
    """보드 JSON 한 개를 담당한다.

    data/board/{board_name}.json 을 읽어
    prototype/images/board/{board_id}.png 를 출력한다.
    스냅 포인트는 {board_id}_snap.json 에 함께 저장된다.
    """

    def __init__(self, board_name: str):
        self.board_name  = board_name
        self._data_path  = os.path.join(_DATA_DIR, 'board', f'{board_name}.json')
        self._output_dir = os.path.join(_PROTO_IMG, 'board')

    def _load_board(self) -> dict:
        with open(self._data_path, 'r', encoding='utf-8') as f:
            return json.load(f)['board']

    def generate_images(self, cache: dict, force: bool = False) -> list:
        board = self._load_board()
        out_path  = os.path.join(self._output_dir, f'{board["id"]}.png')
        cache_key = f'board:{self.board_name}'
        inp_hash  = self._input_hash(board)
        cached    = cache.get(cache_key, {})

        if (not force
                and cached.get('input_hash') == inp_hash
                and os.path.exists(out_path)):
            print(f'    건너뜀: {board["id"]}.png (변경 없음)')
            return [out_path]

        os.makedirs(self._output_dir, exist_ok=True)
        self._render(board, out_path)
        cache[cache_key] = {'input_hash': inp_hash, 'output_path': out_path}
        print(f'    생성: {board["id"]}.png')
        return [out_path]

    # ── 유틸리티 ────────────────────────────────────────────────

    @staticmethod
    def _get_font(fonts, key, size_override=None):
        path = fonts[key][0]
        size = size_override if size_override is not None else fonts[key][1]
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            return ImageFont.load_default()

    def _draw_card_slot(self, draw, x, y, slot_w=None):
        """카드 슬롯 — 둥근 직사각형 플레이스홀더.
        slot_w 를 지정하면 해당 너비를 사용, 없으면 기본 self._csw.
        """
        w = slot_w if slot_w is not None else self._csw
        draw.rounded_rectangle(
            [x, y, x + w, y + self._csh],
            radius=self._csr,
            fill=self._fill,
            outline=self._ink,
            width=2,
        )

    def _draw_rotated_text(self, img, text, font, color, bx, by, bw, bh, angle):
        """angle 도 회전한 텍스트를 (bx,by,bw,bh) 박스 중앙에 그린다.

        angle=90  → PIL 90° CCW  → 오른쪽 사이드 플레이어가 읽기 편한 방향
        angle=270 → PIL 270° CCW → 왼쪽 사이드 플레이어가 읽기 편한 방향
        """
        tmp = Image.new('RGBA', (1, 1))
        tmp_d = ImageDraw.Draw(tmp)
        bbox = tmp_d.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]

        txt_img = Image.new('RGBA', (tw + 4, th + 4), (0, 0, 0, 0))
        ImageDraw.Draw(txt_img).text((2, 2), text, font=font, fill=color)

        rotated = txt_img.rotate(angle, expand=True)
        rw, rh = rotated.size

        px = bx + (bw - rw) // 2
        py = by + (bh - rh) // 2
        img.paste(rotated, (px, py), rotated)

    # ── 섹션 렌더러 ─────────────────────────────────────────────

    def _render_open_area(self, img, draw, section, fonts, colors, snaps):
        """카드를 자유롭게 놓는 열린 영역 (정책 영역, 핵심 정책 등).
        고정 슬롯 없음 — 스냅 포인트 미생성.
        """
        x, y = section['position']['x'], section['position']['y']
        w, h = section['size']['width'], section['size']['height']
        label_h = 50

        draw.rectangle([x, y, x + w, y + h], fill=self._fill, outline=self._ink, width=2)
        draw.line([(x, y + label_h), (x + w, y + label_h)], fill=self._ink, width=2)

        font = self._get_font(fonts, 'title')
        bbox = draw.textbbox((0, 0), section['name'], font=font)
        tx = x + (w - (bbox[2] - bbox[0])) // 2
        ty = y + (label_h - (bbox[3] - bbox[1])) // 2
        draw.text((tx, ty), section['name'], fill=self._ink, font=font)

    def _render_side_panel(self, img, draw, section, fonts, colors, snaps):
        """세로 패널 — 회전 텍스트 + 카드 슬롯 1개.

        rotation=270 : 왼쪽 사이드 플레이어가 보기 편한 방향 (아래→위)
        rotation=90  : 오른쪽 사이드 플레이어가 보기 편한 방향 (위→아래)
        """
        x, y = section['position']['x'], section['position']['y']
        w, h = section['size']['width'], section['size']['height']

        draw.rectangle([x, y, x + w, y + h], fill=self._fill, outline=self._ink, width=2)

        # 카드 슬롯: 좌우 10px 인셋, 상하 중앙 정렬
        slot_w = min(self._csw, w - 20)
        cx = x + (w - slot_w) // 2
        cy = y + (h - self._csh) // 2
        self._draw_card_slot(draw, cx, cy, slot_w=slot_w)
        snaps.append({
            'label':   section['id'],
            'pixel_x': cx + slot_w // 2,
            'pixel_y': cy + self._csh // 2,
        })

        # 회전 라벨 — 카드 높이 1/4 크기 폰트
        angle = section.get('rotation', 270)
        font  = self._get_font(fonts, 'title', self._csh // 4)
        self._draw_rotated_text(
            img, section['name'], font, self._ink,
            x, y, w, h, angle,
        )

    def _render_card_row(self, img, draw, section, fonts, colors, snaps):
        """헤더 + 카드 슬롯 N개 가로 배열.
        slot_labels: 각 슬롯 안에 표시할 레이블 리스트 (옵션).
        slot_width : 슬롯 개별 너비 오버라이드 (옵션, 기본=board.card_slot_width).
        """
        x, y = section['position']['x'], section['position']['y']
        w, h = section['size']['width'], section['size']['height']
        s      = section.get('style', {})
        n      = section.get('card_count', 3)
        labels = section.get('slot_labels', [])
        slot_w = section.get('slot_width', self._csw)
        hh     = s.get('header_height', 55)

        draw.rectangle([x, y, x + w, y + h], fill=self._fill, outline=self._ink, width=2)
        draw.line([(x, y + hh), (x + w, y + hh)], fill=self._ink, width=2)

        font = self._get_font(fonts, 'title')
        bbox = draw.textbbox((0, 0), section['name'], font=font)
        draw.text(
            (x + (w - (bbox[2] - bbox[0])) // 2,
             y + (hh - (bbox[3] - bbox[1])) // 2),
            section['name'], fill=self._ink, font=font,
        )

        # 슬롯 가로 균등 배치
        spacing  = (w - n * slot_w) // (n + 1)
        slot_y   = y + hh + (h - hh - self._csh) // 2
        lbl_font = self._get_font(fonts, 'title', self._csh // 4)

        for i in range(n):
            sx = x + spacing + i * (slot_w + spacing)
            self._draw_card_slot(draw, sx, slot_y, slot_w=slot_w)

            # 슬롯 레이블 (카드 높이 1/4 크기)
            if i < len(labels):
                lbl = labels[i]
                lb  = draw.textbbox((0, 0), lbl, font=lbl_font)
                lx  = sx + (slot_w - (lb[2] - lb[0])) // 2
                ly  = slot_y + (self._csh - (lb[3] - lb[1])) // 2
                draw.text((lx, ly), lbl, fill=self._ink, font=lbl_font)

            snaps.append({
                'label':   f'{section["id"]}_slot{i + 1}',
                'pixel_x': sx + slot_w // 2,
                'pixel_y': slot_y + self._csh // 2,
            })

    def _render_info_box(self, img, draw, section, fonts, colors, snaps):
        """헤더 + 빈 영역 (카드 슬롯 없음)."""
        x, y = section['position']['x'], section['position']['y']
        w, h = section['size']['width'], section['size']['height']
        hh    = section.get('style', {}).get('header_height', 55)

        draw.rectangle([x, y, x + w, y + h], fill=self._fill, outline=self._ink, width=2)
        draw.line([(x, y + hh), (x + w, y + hh)], fill=self._ink, width=2)

        font = self._get_font(fonts, 'title')
        bbox = draw.textbbox((0, 0), section['name'], font=font)
        draw.text(
            (x + (w - (bbox[2] - bbox[0])) // 2,
             y + (hh - (bbox[3] - bbox[1])) // 2),
            section['name'], fill=self._ink, font=font,
        )

    def _render_card_box(self, img, draw, section, fonts, colors, snaps):
        """헤더 + 카드 슬롯 1개 (이조전랑, 비변사 등).
        slot_width: 슬롯 너비 오버라이드 (박스가 카드보다 좁을 때 사용).
        """
        x, y = section['position']['x'], section['position']['y']
        w, h = section['size']['width'], section['size']['height']
        hh    = section.get('style', {}).get('header_height', 55)

        draw.rectangle([x, y, x + w, y + h], fill=self._fill, outline=self._ink, width=2)
        draw.line([(x, y + hh), (x + w, y + hh)], fill=self._ink, width=2)

        font = self._get_font(fonts, 'title')
        bbox = draw.textbbox((0, 0), section['name'], font=font)
        draw.text(
            (x + (w - (bbox[2] - bbox[0])) // 2,
             y + (hh - (bbox[3] - bbox[1])) // 2),
            section['name'], fill=self._ink, font=font,
        )

        # 카드 슬롯 (나머지 공간 중앙)
        slot_w = section.get('slot_width', self._csw)
        slot_w = min(slot_w, w - 10)
        cx = x + (w - slot_w) // 2
        remaining = h - hh
        cy = y + hh + (remaining - self._csh) // 2
        self._draw_card_slot(draw, cx, cy, slot_w=slot_w)
        snaps.append({
            'label':   section['id'],
            'pixel_x': cx + slot_w // 2,
            'pixel_y': cy + self._csh // 2,
        })

    # ── 렌더러 디스패치 테이블 ───────────────────────────────────

    _SECTION_RENDERERS = {
        'open_area':  '_render_open_area',
        'side_panel': '_render_side_panel',
        'card_row':   '_render_card_row',
        'info_box':   '_render_info_box',
        'card_box':   '_render_card_box',
    }

    # ── 메인 렌더 ────────────────────────────────────────────────

    def _render(self, board: dict, out_path: str):
        fonts  = FONTS
        colors = COLORS

        # 카드 슬롯 공통 크기
        self._csw = board.get('card_slot_width',  300)
        self._csh = board.get('card_slot_height', 360)
        self._csr = board.get('card_slot_radius',  15)

        # 흑백 팔레트
        self._fill = '#FFFFFF'
        self._ink  = '#000000'

        # 보드 배경 — 흰색
        img  = Image.new('RGB', (board['width'], board['height']), self._fill)
        draw = ImageDraw.Draw(img)

        # 외곽 테두리
        draw.rectangle(
            [4, 4, board['width'] - 4, board['height'] - 4],
            outline=self._ink, width=3,
        )

        snaps = []

        for section in board['sections']:
            sec_type    = section.get('type', 'info_box')
            method_name = self._SECTION_RENDERERS.get(sec_type)
            if method_name:
                getattr(self, method_name)(img, draw, section, fonts, colors, snaps)

        # 스냅 포인트 저장
        snap_path = out_path.replace('.png', '_snap.json')
        with open(snap_path, 'w', encoding='utf-8') as f:
            json.dump(
                {
                    'board_width':  board['width'],
                    'board_height': board['height'],
                    'snap_points':  snaps,
                },
                f, ensure_ascii=False, indent=2,
            )

        img.save(out_path, 'PNG', dpi=(BOARD_CONFIG['dpi'], BOARD_CONFIG['dpi']))
