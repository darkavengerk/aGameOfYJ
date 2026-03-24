"""
카드 레이아웃 엔진
다양한 카드 타입의 레이아웃을 유연하게 처리하는 시스템
"""

from abc import ABC, abstractmethod
from PIL import Image, ImageDraw, ImageFont
import json
import os
from config import KOREAN_FONT as _KOREAN_FONT
from utils import wrap_text as _wrap_text

class CardLayout(ABC):
    """카드 레이아웃 추상 클래스"""
    
    def __init__(self, layout_config, colors_config):
        self.layout_config = layout_config
        self.colors_config = colors_config
        
    @abstractmethod
    def render(self, image, draw, card_data):
        """카드 렌더링"""
        pass
    
    def get_position(self, element_config, card_width, card_height):
        """위치 계산.
        position.x: 숫자, 'center', 'right'(margin 필드로 우측 여백 지정)
        position.y: 숫자, 'center', 'center_bottom'(offset), 'bottom'(offset)
        """
        pos = element_config['position']

        if isinstance(pos['x'], str) and pos['x'] == 'center':
            x = card_width // 2
        elif isinstance(pos['x'], str) and pos['x'] == 'right':
            x = card_width - pos.get('margin', 80)
        else:
            x = pos['x']

        if isinstance(pos['y'], str) and pos['y'] == 'center':
            y = card_height // 2
        elif isinstance(pos['y'], str) and pos['y'] == 'center_bottom':
            y = card_height // 2 + pos.get('offset', 50)
        elif isinstance(pos['y'], str) and pos['y'] == 'bottom':
            y = card_height - pos.get('offset', 100)
        else:
            y = pos['y']

        return x, y
    
    def get_font(self, font_config):
        """폰트 생성 — config.py 에서 탐색된 한글 폰트 경로를 사용."""
        font_size = font_config['size']
        candidates = []
        if 'name' in font_config:
            candidates.append(font_config['name'])
        if _KOREAN_FONT:
            candidates.append(_KOREAN_FONT)
        for path in candidates:
            try:
                return ImageFont.truetype(path, font_size)
            except Exception:
                continue
        return ImageFont.load_default()

class GapjaCardLayout(CardLayout):
    """60갑자 카드 레이아웃"""
    
    def render(self, image, draw, card_data):
        """60갑자 카드 렌더링"""
        card_width, card_height = image.size

        # 배경색 설정 (간지 색상 기반)
        gan_color_info = self.colors_config['gan_colors'].get(card_data['gan'], {})
        gan_color = gan_color_info.get('color', '#F5F5DC')
        draw.rectangle([0, 0, card_width - 1, card_height - 1], fill=gan_color)
        
        # 테두리
        self._draw_border(draw, card_width, card_height)
        
        # 12지 번호
        self._draw_zhi_number(draw, card_data, card_width, card_height)
        
        # 60갑자 정보
        self._draw_gapja_info(draw, card_data, card_width, card_height)
        
        # 오행 정보
        self._draw_element(draw, card_data, card_width, card_height)
        
        # 동물 이름 (중앙)
        self._draw_animal(draw, card_data, card_width, card_height)
        
        # 메인 텍스트 (있는 경우)
        if card_data.get('main_text'):
            self._draw_main_text(draw, card_data, card_width, card_height)
    
    def _draw_border(self, draw, width, height):
        """테두리 그리기"""
        border_color = "#8B4513"
        border_width = 3
        margin = 10
        
        draw.rectangle([margin, margin, width - margin, height - margin], 
                      outline=border_color, width=border_width)
    
    @staticmethod
    def _luminance(hex_color: str) -> float:
        """hex 색상 문자열(#RRGGBB)의 상대 휘도를 반환 (0–255 범위)"""
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        return 0.299 * r + 0.587 * g + 0.114 * b

    def _get_text_color(self, card_data, element_config=None, force_auto_color=False):
        """텍스트 색상 결정 (개별 설정 우선).
        force_auto_color=False 이고 element_config에 color가 있으면 그 값을 사용한다.
        배경이 어두우면(휘도 < 128) 흰색, 밝으면 어두운 갈색을 반환한다.
        """
        if element_config and 'color' in element_config and not force_auto_color:
            return element_config['color']

        gan_color_info = self.colors_config['gan_colors'].get(card_data['gan'], {})
        gan_color = gan_color_info.get('color', '#F5F5DC')

        if self._luminance(gan_color) < 128:
            return self.colors_config.get('text_colors', {}).get('dark_background', '#FFFFFF')
        return self.colors_config.get('text_colors', {}).get('light_background', '#2C1810')
    
    def _draw_zhi_number(self, draw, card_data, width, height):
        """12지 번호 그리기"""
        element_config = self.layout_config['elements']['zhi_number']
        x, y = self.get_position(element_config, width, height)
        font = self.get_font(element_config['font'])
        color = self._get_text_color(card_data, element_config, force_auto_color=True)
        
        # 12지 인덱스 계산 (자=1, 축=2, ...)
        zhi_list = ['자', '축', '인', '묘', '진', '사', '오', '미', '신', '유', '술', '해']
        zhi_index = zhi_list.index(card_data['ji']) + 1
        
        text = str(zhi_index)
        draw.text((x, y), text, fill=color, font=font)
    
    def _draw_gapja_info(self, draw, card_data, width, height):
        """60갑자 정보 그리기"""
        element_config = self.layout_config['elements']['gapja_info']
        x, y = self.get_position(element_config, width, height)
        font = self.get_font(element_config['font'])
        color = self._get_text_color(card_data, element_config, force_auto_color=True)
        
        # 60갑자 번호와 갑자 이름
        text = f"{card_data['number']} {card_data['gapja_name']}"
        draw.text((x, y), text, fill=color, font=font)
    
    def _draw_element(self, draw, card_data, width, height):
        """오행 정보 그리기"""
        if 'element' not in self.layout_config['elements']:
            return
            
        element_config = self.layout_config['elements']['element']
        x, y = self.get_position(element_config, width, height)
        font = self.get_font(element_config['font'])
        color = self._get_text_color(card_data, element_config, force_auto_color=True)
        
        element_name = card_data['element']
        
        # 배경 박스가 비활성화된 경우 텍스트만 그리기
        if not element_config.get('background', {}).get('enabled', False):
            draw.text((x, y), element_name, fill=color, font=font)
            return
        
        # 배경 박스 그리기 (설정된 경우)
        bg_config = element_config['background']
        padding = bg_config['padding']
        border_color = bg_config['border_color']
        border_width = bg_config['border_width']
        
        # 텍스트 크기 계산
        bbox = draw.textbbox((0, 0), element_name, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # 박스 크기 및 위치
        box_x = x - padding
        box_y = y - padding
        box_width = text_width + padding * 2
        box_height = text_height + padding * 2
        
        # 박스 그리기
        draw.rectangle([box_x, box_y, box_x + box_width, box_y + box_height],
                      fill='white', outline=border_color, width=border_width)
        
        draw.text((x, y), element_name, fill=color, font=font)
    
    def _draw_animal(self, draw, card_data, width, height):
        """동물 이름 그리기 (수평·수직 중앙 정렬)"""
        element_config = self.layout_config['elements']['animal']
        font  = self.get_font(element_config['font'])
        color = self._get_text_color(card_data, element_config, force_auto_color=True)

        text = card_data['animal']
        bbox = draw.textbbox((0, 0), text, font=font)
        x = (width  - (bbox[2] - bbox[0])) // 2
        y = (height - (bbox[3] - bbox[1])) // 2

        draw.text((x, y), text, fill=color, font=font)
    
    def _draw_main_text(self, draw, card_data, width, height):
        """메인 텍스트(main_text)를 하단 박스에 그린다."""
        text = card_data.get('main_text', '')
        if not text:
            return
        element_config = self.layout_config['elements']['special_ability']

        box_config = element_config['box']
        box_width  = int(width * 0.9)
        box_height = box_config['height']
        box_x = (width  - box_width)  // 2
        box_y = height - box_height - box_config['margin']

        draw.rectangle(
            [box_x, box_y, box_x + box_width, box_y + box_height],
            fill=box_config['background'],
            outline=box_config['border']['color'],
            width=box_config['border']['width'],
        )

        font  = self.get_font(element_config['font'])
        color = self._get_text_color(card_data, element_config)

        lines = _wrap_text(text, font, box_width - 20)
        y = box_y + 10
        for line in lines:
            draw.text((box_x + 10, y), line, fill=color, font=font)
            y += 18

# ── 효과/자원/트리거 한국어 표기 ───────────────────────────────
_RESOURCE_KO = {
    'influence':     '영향력',
    'knowledge':     '지식',
    'defense':       '방어',
    'resource':      '자원',
    'action_tokens': '행동 토큰',
}
_TARGET_KO = {
    'all_players':    '모든 플레이어',
    'leading_player': '선두 플레이어',
    'self':           '본인',
}
_TRIGGER_KO = {
    'round_start': '라운드 시작',
    'round_end':   '라운드 종료',
    'on_play':     '카드 사용 시',
}


class StandardCardLayout(CardLayout):
    """표준 카드 레이아웃 (정책·사건 카드 등).

    카드 데이터 스키마: { title, main_text }
    """

    def render(self, image, draw, card_data):
        w, h = image.size
        card_cfg = self.layout_config.get('card', {})

        # 배경
        draw.rectangle([0, 0, w - 1, h - 1], fill=card_cfg.get('background', '#FFF8F0'))

        # 테두리
        bm = card_cfg.get('border_margin', 10)
        draw.rectangle(
            [bm, bm, w - bm - 1, h - bm - 1],
            outline=card_cfg.get('border_color', '#8B4513'),
            width=card_cfg.get('border_width', 3),
        )

        self._draw_title(draw, card_data, w, h)
        self._draw_main_text(draw, card_data, w, h)

    def _draw_title(self, draw, card_data, w, h):
        cfg = self.layout_config['elements']['title']
        font = self.get_font(cfg['font'])
        color = cfg.get('color', '#2C1810')
        text = card_data.get('title', '')
        bbox = draw.textbbox((0, 0), text, font=font)
        x = (w - (bbox[2] - bbox[0])) // 2
        y = cfg['position']['y']
        draw.text((x, y), text, fill=color, font=font)

    def _draw_main_text(self, draw, card_data, w, h):
        """main_text를 제목 아래에 자동 줄바꿈해 출력."""
        text = card_data.get('main_text', '')
        if not text:
            return
        cfg = self.layout_config['elements'].get('flavor_text',
              {'position': {'x': 20, 'y': 80}, 'font': {'size': 12, 'weight': 'normal'},
               'color': '#2C1810', 'max_width_ratio': 0.85})
        font = self.get_font(cfg['font'])
        color = cfg.get('color', '#2C1810')
        max_w = int(w * cfg.get('max_width_ratio', 0.85))
        x = cfg['position']['x']
        y = cfg['position']['y']

        lines = _wrap_text(text, font, max_w)
        lh = cfg.get('line_height', 20)
        for line in lines:
            draw.text((x, y), line, fill=color, font=font)
            y += lh


class LayoutFactory:
    """레이아웃 팩토리"""

    @staticmethod
    def create_layout(layout_type, layout_config, colors_config):
        """레이아웃 생성"""
        if layout_type == 'gapja_layout':
            return GapjaCardLayout(layout_config, colors_config)
        if layout_type == 'standard_layout':
            return StandardCardLayout(layout_config, colors_config)
        raise ValueError(f"Unknown layout type: {layout_type}")

class CardRenderer:
    """카드 렌더러"""
    
    def __init__(self, card_width=300, card_height=420):
        self.card_width = card_width
        self.card_height = card_height
        
    def render_card(self, card_data, layout_config, colors_config):
        """카드 렌더링"""
        # 이미지 생성
        image = Image.new('RGB', (self.card_width, self.card_height), '#FFFFFF')
        draw = ImageDraw.Draw(image)
        
        # 레이아웃 생성
        layout_type = layout_config['type']
        layout = LayoutFactory.create_layout(layout_type, layout_config, colors_config)
        
        # 렌더링
        layout.render(image, draw, card_data)
        
        return image
