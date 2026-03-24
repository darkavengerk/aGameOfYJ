"""GapjaHandler — 60갑자 카드 덱 핸들러 (gapja_layout 계열)."""

import json
import os

from config import CARD_CONFIG
from card_layout_engine import CardRenderer
from handlers.base import ComponentHandler

_PROJECT_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(__file__), '..', '..', '..')
)
_DATA_DIR  = os.path.join(_PROJECT_ROOT, 'data')
_PROTO_IMG = os.path.join(_PROJECT_ROOT, 'prototype', 'images')


class GapjaHandler(ComponentHandler):
    """노론/소론 60갑자 카드 덱 핸들러.

    data/cards/{faction_name}.json + data/layouts/gapja_card.json +
    data/cards/ganzi_colors.json 을 읽어
    prototype/images/cards/{faction_name}/ 에 PNG를 출력한다.
    """

    def __init__(self, faction_name: str):
        self.faction_name = faction_name
        self._cards_path  = os.path.join(_DATA_DIR, 'cards', f'{faction_name}.json')
        self._layout_path = os.path.join(_DATA_DIR, 'layouts', 'gapja_card.json')
        self._colors_path = os.path.join(_DATA_DIR, 'cards', 'ganzi_colors.json')
        self._output_dir  = os.path.join(_PROTO_IMG, 'cards', faction_name)
        self._renderer    = CardRenderer(CARD_CONFIG['width'], CARD_CONFIG['height'])

    # ── 내부 로더 ──────────────────────────────────────────────

    def _load(self, path: str) -> dict:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    # ── 이미지 생성 ────────────────────────────────────────────

    def generate_images(self, cache: dict, force: bool = False) -> list:
        layout_cfg  = self._load(self._layout_path)
        colors_cfg  = self._load(self._colors_path)
        cards_data  = self._load(self._cards_path)

        layout_hash = self._input_hash(layout_cfg)
        colors_hash = self._input_hash(colors_cfg)
        os.makedirs(self._output_dir, exist_ok=True)

        generated = []
        skipped   = 0

        for card in cards_data.get('cards', []):
            # id 필드 없이 number 기반 파일명 사용
            card_id  = card.get('id') or f'{self.faction_name}_{card["number"]:03d}'
            out_path = os.path.join(self._output_dir, f'{card_id}.png')
            cache_key = f'{self.faction_name}:{card_id}'

            inp_hash = self._input_hash({
                'card': card,
                'layout_hash': layout_hash,
                'colors_hash': colors_hash,
            })
            cached = cache.get(cache_key, {})

            if (not force
                    and cached.get('input_hash') == inp_hash
                    and os.path.exists(out_path)):
                skipped += 1
                generated.append(out_path)
                continue

            image = self._renderer.render_card(card, layout_cfg, colors_cfg)
            image.save(out_path, 'PNG', dpi=(CARD_CONFIG['dpi'], CARD_CONFIG['dpi']))
            cache[cache_key] = {'input_hash': inp_hash, 'output_path': out_path}
            print(f'    생성: {self.faction_name}/{card_id}.png')
            generated.append(out_path)

        if skipped:
            print(f'    건너뜀: {self.faction_name} {skipped}장 (변경 없음)')
        return generated
