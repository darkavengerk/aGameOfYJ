"""
카드 레이아웃 엔진
다양한 카드 타입의 레이아웃을 유연하게 처리하는 시스템
"""

from abc import ABC, abstractmethod
from PIL import Image, ImageDraw, ImageFont
import json
import os

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
        """위치 계산"""
        pos = element_config['position']
        
        if isinstance(pos['x'], str) and pos['x'] == 'center':
            x = card_width // 2
        elif isinstance(pos['x'], str) and pos['x'] == 'right':
            x = card_width - 80
        else:
            x = pos['x']
            
        if isinstance(pos['y'], str) and pos['y'] == 'center':
            y = card_height // 2
        elif pos['y'] == 'center_bottom':
            y = card_height // 2 + 50
        elif pos['y'] == 'bottom':
            y = card_height - 100
        else:
            y = pos['y']
            
        return x, y
    
    def get_font(self, font_config):
        """폰트 생성"""
        try:
            font_name = font_config.get('name', 'malgun.ttf')
            font_size = font_config['size']
            font_weight = font_config.get('weight', 'normal')
            
            font = ImageFont.truetype(font_name, font_size)
            return font
        except:
            return ImageFont.load_default()

class GapjaCardLayout(CardLayout):
    """60갑자 카드 레이아웃"""
    
    def render(self, image, draw, card_data):
        """60갑자 카드 렌더링"""
        card_width, card_height = image.size
        
        # 배경색 설정 (간지 색상 기반)
        gan_color_info = self.colors_config['gan_colors'].get(card_data['gan'], {})
        gan_color = gan_color_info.get('color', '#F5F5DC')
        image.paste(gan_color, (0, 0, card_width, card_height))
        
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
        
        # 특수기능 (있는 경우)
        if card_data.get('special_ability'):
            self._draw_special_ability(draw, card_data, card_width, card_height)
    
    def _draw_border(self, draw, width, height):
        """테두리 그리기"""
        border_color = "#8B4513"
        border_width = 3
        margin = 10
        
        draw.rectangle([margin, margin, width - margin, height - margin], 
                      outline=border_color, width=border_width)
    
    def _get_text_color(self, card_data, element_config=None, force_auto_color=False):
        """텍스트 색상 결정 (개별 설정 우선, 특수기능 박스 제외)"""
        # 특수기능 박스는 항상 개별 설정 사용
        if element_config and 'color' in element_config and not force_auto_color:
            return element_config['color']
        
        # 배경색에 따른 자동 색상 결정
        gan_color_info = self.colors_config['gan_colors'].get(card_data['gan'], {})
        gan_color = gan_color_info.get('color', '#F5F5DC')
        
        # 어두운 배경 (청색, 적색, 흑색 계열)이면 흰색 텍스트
        dark_colors = ['#2F4F4F', '#191970', '#1E90FF', '#DC143C']
        if gan_color in dark_colors:
            return self.colors_config.get('text_colors', {}).get('dark_background', '#FFFFFF')
        else:
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
    
    def _draw_number(self, draw, card_data, width, height):
        """번호 그리기 (하위 호환성)"""
        pass
    
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
    
    def _draw_gapja_name(self, draw, card_data, width, height):
        """갑자 이름 그리기"""
        pass  # 더 이상 사용하지 않음
    
    def _draw_animal(self, draw, card_data, width, height):
        """동물 이름 그리기 (중앙)"""
        element_config = self.layout_config['elements']['animal']
        x, y = self.get_position(element_config, width, height)
        font = self.get_font(element_config['font'])
        color = self._get_text_color(card_data, element_config, force_auto_color=True)
        
        # 동물 이름만 표시
        text = card_data['animal']
        
        # 중앙 정렬
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        draw.text((x, y), text, fill=color, font=font)
    
    def _draw_special_ability(self, draw, card_data, width, height):
        """특수기능 그리기"""
        special = card_data['special_ability']
        element_config = self.layout_config['elements']['special_ability']
        
        # 박스 설정
        box_config = element_config['box']
        box_width = int(width * 0.9)
        box_height = box_config['height']
        box_x = (width - box_width) // 2
        box_y = height - box_height - box_config['margin']
        
        # 박스 그리기
        box_bg = box_config['background']
        box_border = box_config['border']
        
        draw.rectangle([box_x, box_y, box_x + box_width, box_y + box_height],
                      fill=box_bg, outline=box_border['color'], width=box_border['width'])
        
        # 텍스트 그리기
        font = self.get_font(element_config['font'])
        color = self._get_text_color(card_data, element_config)
        
        # 제목
        title_text = special['name']
        title_bbox = draw.textbbox((0, 0), title_text, font=font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = box_x + (box_width - title_width) // 2
        title_y = box_y + 10
        
        draw.text((title_x, title_y), title_text, fill=color, font=font)
        
        # 설명 (자동 줄바꿈)
        desc_text = special['description']
        lines = self._wrap_text(desc_text, font, box_width - 20)
        
        desc_y = title_y + 25
        for line in lines:
            draw.text((box_x + 10, desc_y), line, fill=color, font=font)
            desc_y += 18
    
    def _wrap_text(self, text, font, max_width):
        """텍스트 자동 줄바꿈"""
        lines = []
        words = text.split(' ')
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = ImageDraw.Draw(Image.new('RGB', (1, 1))).textbbox((0, 0), test_line, font=font)
            text_width = bbox[2] - bbox[0]
            
            if text_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    lines.append(word)
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines

class LayoutFactory:
    """레이아웃 팩토리"""
    
    @staticmethod
    def create_layout(layout_type, layout_config, colors_config):
        """레이아웃 생성"""
        if layout_type == 'gapja_layout':
            return GapjaCardLayout(layout_config, colors_config)
        else:
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
