"""CardDeckHandler — 표준 레이아웃 카드 덱 핸들러 (standard_layout 계열)."""

import json
import os

from config import CARD_CONFIG
from card_layout_engine import CardRenderer
from handlers.base import ComponentHandler

# handlers/ → scripts/ → prototype/ → project root
_PROJECT_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(__file__), '..', '..', '..')
)
_DATA_DIR  = os.path.join(_PROJECT_ROOT, 'data')
_PROTO_IMG = os.path.join(_PROJECT_ROOT, 'prototype', 'images')


class CardDeckHandler(ComponentHandler):
    """JSON 데이터 파일 한 개 = 카드 덱 한 개를 담당한다.

    data/cards/{deck_name}.json 을 읽어
    prototype/images/cards/{deck_name}/ 에 PNG를 출력한다.
    """

    def __init__(self, deck_name: str):
        self.deck_name = deck_name
        self._cards_path  = os.path.join(_DATA_DIR, 'cards', f'{deck_name}.json')
        self._output_dir  = os.path.join(_PROTO_IMG, 'cards', deck_name)
        self._renderer    = CardRenderer(CARD_CONFIG['width'], CARD_CONFIG['height'])
        self._layout_cache: dict = {}

    # ── 내부 로더 ──────────────────────────────────────────────

    def _load_deck(self) -> dict:
        with open(self._cards_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_layout(self, layout_name: str) -> dict:
        if layout_name not in self._layout_cache:
            path = os.path.join(_DATA_DIR, 'layouts', f'{layout_name}.json')
            with open(path, 'r', encoding='utf-8') as f:
                self._layout_cache[layout_name] = json.load(f)
        return self._layout_cache[layout_name]

    # ── 이미지 생성 ────────────────────────────────────────────

    def generate_images(self, cache: dict, force: bool = False) -> list:
        deck = self._load_deck()

        # gapja 계열은 GapjaHandler 가 담당
        if deck.get('layout') == 'gapja_card':
            return []

        layout_name = deck.get('layout')
        if not layout_name or 'cards' not in deck:
            return []

        layout_cfg  = self._load_layout(layout_name)
        layout_hash = self._input_hash(layout_cfg)
        os.makedirs(self._output_dir, exist_ok=True)

        generated = []
        skipped   = 0

        for idx, card in enumerate(deck['cards']):
            # id 필드가 없으면 인덱스 기반 파일명 사용
            card_id  = card.get('id') or f'{self.deck_name}_{idx + 1:03d}'
            out_path = os.path.join(self._output_dir, f'{card_id}.png')
            cache_key = f'{self.deck_name}:{card_id}'

            inp_hash = self._input_hash({'card': card, 'layout_hash': layout_hash})
            cached   = cache.get(cache_key, {})

            if (not force
                    and cached.get('input_hash') == inp_hash
                    and os.path.exists(out_path)):
                skipped += 1
                generated.append(out_path)
                continue

            image = self._renderer.render_card(card, layout_cfg, {})
            image.save(out_path, 'PNG', dpi=(CARD_CONFIG['dpi'], CARD_CONFIG['dpi']))
            cache[cache_key] = {'input_hash': inp_hash, 'output_path': out_path}
            print(f'    생성: {self.deck_name}/{card_id}.png')
            generated.append(out_path)

        if skipped:
            print(f'    건너뜀: {self.deck_name} {skipped}장 (변경 없음)')
        return generated
