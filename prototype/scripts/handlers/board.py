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

    # ── 섹션 타입별 렌더 함수 ──────────────────────────────────

    @staticmethod
    def _get_font(fonts, key, size_override=None):
        path = fonts[key][0]
        size = size_override if size_override is not None else fonts[key][1]
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            return ImageFont.load_default()

    def _render_area_section(self, draw, section, margin, fonts, colors):
        sx = section['position']['x'] + margin
        sy = section['position']['y'] + margin
        sw = section['size']['width']
        sh = section['size']['height']
        style = section.get('style', {})

        bg     = style.get('background',   colors['background'])
        bc     = style.get('border_color', colors['accent'])
        bw     = style.get('border_width', 2)
        hc     = style.get('header_color', colors['accent'])
        hh     = style.get('header_height', 40)

        draw.rectangle([sx, sy, sx + sw, sy + sh], fill=bg, outline=bc, width=bw)

        # 헤더 배경
        draw.rectangle([sx, sy, sx + sw, sy + hh], fill=hc)

        font = self._get_font(fonts, 'title')
        name = section['name']
        bbox = draw.textbbox((0, 0), name, font=font)
        tx = sx + (sw - (bbox[2] - bbox[0])) // 2
        draw.text((tx, sy + (hh - (bbox[3] - bbox[1])) // 2),
                  name, fill=colors['text_primary'], font=font)

    def _render_track_section(self, draw, section, margin, fonts, colors):
        sx = section['position']['x'] + margin
        sy = section['position']['y'] + margin
        sw = section['size']['width']
        sh = section['size']['height']
        style      = section.get('style', {})
        slot_style = section.get('slot_style', {})
        slots      = section.get('slots', 8)

        bg = style.get('background',   colors['background'])
        bc = style.get('border_color', colors['accent'])
        bw = style.get('border_width', 2)
        hc = style.get('header_color', colors['accent'])
        hh = style.get('header_height', 35)

        # 트랙 배경 + 테두리
        draw.rectangle([sx, sy, sx + sw, sy + sh], fill=bg, outline=bc, width=bw)

        # 헤더
        draw.rectangle([sx, sy, sx + sw, sy + hh], fill=hc)
        font = self._get_font(fonts, 'subtitle')
        name = section['name']
        bbox = draw.textbbox((0, 0), name, font=font)
        tx = sx + (sw - (bbox[2] - bbox[0])) // 2
        draw.text((tx, sy + (hh - (bbox[3] - bbox[1])) // 2),
                  name, fill='#FFFFFF', font=font)

        # 슬롯 그리기
        slot_w   = sw // slots
        slot_bg  = slot_style.get('background',   '#F5F0E8')
        slot_bc  = slot_style.get('border_color', '#654321')
        slot_top = sy + hh

        for i in range(slots):
            slx = sx + i * slot_w
            draw.rectangle(
                [slx + 2, slot_top + 2, slx + slot_w - 2, sy + sh - 2],
                fill=slot_bg, outline=slot_bc, width=1,
            )
            # 슬롯 번호
            num_font = self._get_font(fonts, 'small')
            num = str(i + 1)
            nb  = draw.textbbox((0, 0), num, font=num_font)
            nx  = slx + (slot_w - (nb[2] - nb[0])) // 2
            ny  = slot_top + 6
            draw.text((nx, ny), num, fill=slot_bc, font=num_font)

    def _render_player_mat_section(self, draw, section, margin, fonts, colors):
        """플레이어 구역 — player_count 만큼 균등 분할"""
        sx = section['position']['x'] + margin
        sy = section['position']['y'] + margin
        sw = section['size']['width']
        sh = section['size']['height']
        style        = section.get('style', {})
        player_count = section.get('player_count', 4)

        bg = style.get('background',   colors['background'])
        bc = style.get('border_color', colors['accent'])
        bw = style.get('border_width', 2)
        hc = style.get('header_color', colors['accent'])
        hh = style.get('header_height', 35)

        draw.rectangle([sx, sy, sx + sw, sy + sh], fill=bg, outline=bc, width=bw)

        # 헤더
        draw.rectangle([sx, sy, sx + sw, sy + hh], fill=hc)
        font = self._get_font(fonts, 'subtitle')
        name = section['name']
        bbox = draw.textbbox((0, 0), name, font=font)
        tx = sx + (sw - (bbox[2] - bbox[0])) // 2
        draw.text((tx, sy + (hh - (bbox[3] - bbox[1])) // 2),
                  name, fill='#FFFFFF', font=font)

        # 플레이어별 구획선
        player_w = sw // player_count
        player_colors = [
            colors.get('player_red',    '#DC143C'),
            colors.get('player_blue',   '#4169E1'),
            colors.get('player_green',  '#228B22'),
            colors.get('player_yellow', '#FFD700'),
        ]
        for i in range(1, player_count):
            lx = sx + i * player_w
            draw.line([(lx, sy + hh), (lx, sy + sh)], fill=bc, width=2)

        # 플레이어 번호 표시
        num_font = self._get_font(fonts, 'body')
        for i in range(player_count):
            clr = player_colors[i % len(player_colors)]
            px  = sx + i * player_w
            label = f'P{i + 1}'
            lb = draw.textbbox((0, 0), label, font=num_font)
            lx = px + (player_w - (lb[2] - lb[0])) // 2
            ly = sy + hh + 10
            draw.text((lx, ly), label, fill=clr, font=num_font)

    _SECTION_RENDERERS = {
        'area':       '_render_area_section',
        'track':      '_render_track_section',
        'player_mat': '_render_player_mat_section',
    }

    def _render(self, board: dict, out_path: str):
        fonts  = FONTS
        colors = COLORS

        img  = Image.new('RGB', (board['width'], board['height']), colors['background'])
        draw = ImageDraw.Draw(img)

        margin    = board['margin']
        grid_size = board['grid_size']

        # 그리드
        for y in range(margin, board['height'] - margin, grid_size):
            draw.line([(margin, y), (board['width'] - margin, y)],
                      fill=colors['card_border'], width=1)
        for x in range(margin, board['width'] - margin, grid_size):
            draw.line([(x, margin), (x, board['height'] - margin)],
                      fill=colors['card_border'], width=1)

        # 섹션
        for section in board['sections']:
            sec_type  = section.get('type', 'area')
            method_name = self._SECTION_RENDERERS.get(sec_type, '_render_area_section')
            method = getattr(self, method_name)
            method(draw, section, margin, fonts, colors)

        # 보드 제목
        title_font = self._get_font(fonts, 'title', fonts['title'][1] * 2)
        title = board['title']
        bbox  = draw.textbbox((0, 0), title, font=title_font)
        tx    = (board['width'] - (bbox[2] - bbox[0])) // 2
        draw.text((tx, 30), title, fill=colors['text_primary'], font=title_font)

        img.save(out_path, 'PNG', dpi=(BOARD_CONFIG['dpi'], BOARD_CONFIG['dpi']))
