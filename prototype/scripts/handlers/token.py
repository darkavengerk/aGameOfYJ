"""TokenHandler — 토큰 이미지 핸들러."""

import json
import os

from PIL import Image, ImageDraw, ImageFont
from config import CARD_CONFIG, COLORS, FONTS
from handlers.base import ComponentHandler

_PROJECT_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(__file__), '..', '..', '..')
)
_DATA_DIR  = os.path.join(_PROJECT_ROOT, 'data')
_PROTO_IMG = os.path.join(_PROJECT_ROOT, 'prototype', 'images')


class TokenHandler(ComponentHandler):
    """토큰 JSON 한 개를 담당한다.

    data/tokens/{token_name}.json 을 읽어
    prototype/images/tokens/{token_type}/*.png 를 출력한다.
    """

    def __init__(self, token_name: str):
        self.token_name  = token_name
        self._data_path  = os.path.join(_DATA_DIR, 'tokens', f'{token_name}.json')

    def _load_tokens(self) -> dict:
        with open(self._data_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def generate_images(self, cache: dict, force: bool = False) -> list:
        data       = self._load_tokens()
        token_type = data['type']
        output_dir = os.path.join(_PROTO_IMG, 'tokens', token_type)

        data_hash  = self._input_hash(data)
        cache_key  = f'token:{self.token_name}'
        cached     = cache.get(cache_key, {})

        # 토큰은 전체를 한 단위로 캐시 (개별 토큰보다 세트 단위가 실용적)
        existing = [
            os.path.join(output_dir, f'{t["id"]}.png')
            for t in data.get('tokens', [])
        ]
        all_exist = all(os.path.exists(p) for p in existing)

        if (not force
                and cached.get('input_hash') == data_hash
                and all_exist):
            print(f'    건너뜀: {token_type} 토큰 세트 (변경 없음)')
            return existing

        os.makedirs(output_dir, exist_ok=True)
        generated = []
        colors = COLORS
        fonts  = FONTS

        for token in data.get('tokens', []):
            out_path = os.path.join(output_dir, f'{token["id"]}.png')
            size = 60
            img  = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)

            color     = token['color']
            fill_clr  = colors.get(f'player_{color}', colors['accent'])
            draw.ellipse([5, 5, size - 5, size - 5],
                         fill=fill_clr, outline=colors['card_border'], width=2)

            try:
                font = ImageFont.truetype(fonts['small'][0], fonts['small'][1])
            except Exception:
                font = ImageFont.load_default()

            label = token['label']
            bbox  = draw.textbbox((0, 0), label, font=font)
            tx = (size - (bbox[2] - bbox[0])) // 2
            ty = (size - (bbox[3] - bbox[1])) // 2
            draw.text((tx, ty), label, fill='white', font=font)

            img.save(out_path, 'PNG')
            print(f'    생성: {token["id"]}.png')
            generated.append(out_path)

        cache[cache_key] = {'input_hash': data_hash, 'output_path': output_dir}
        return generated
