"""
영조의나라 데이터 기반 이미지 생성기
JSON 데이터 파일을 읽어와서 폴더 구조를 유지하며 이미지를 생성합니다.
"""

import json
import os
from PIL import Image, ImageDraw, ImageFont
from config import CARD_CONFIG, BOARD_CONFIG, COLORS, FONTS
from utils import wrap_text
from card_layout_engine import CardRenderer, LayoutFactory

class DataImageGenerator:
    def __init__(self, data_dir="../../data", output_dir="../images"):
        self.data_dir = os.path.join(os.path.dirname(__file__), data_dir)
        self.output_dir = os.path.join(os.path.dirname(__file__), output_dir)
        self.card_config = CARD_CONFIG
        self.board_config = BOARD_CONFIG
        self.colors = COLORS
        self.fonts = FONTS
        self._renderer = CardRenderer(CARD_CONFIG['width'], CARD_CONFIG['height'])
        self._layout_cache: dict = {}   # layout name → layout config dict
        
    def _load_layout(self, layout_name: str) -> dict:
        """data/layouts/{name}.json 을 로드 (캐시 사용)"""
        if layout_name not in self._layout_cache:
            path = os.path.join(self.data_dir, 'layouts', f'{layout_name}.json')
            with open(path, 'r', encoding='utf-8') as f:
                self._layout_cache[layout_name] = json.load(f)
        return self._layout_cache[layout_name]

    def generate_cards(self):
        """카드 데이터를 기반으로 이미지 생성"""
        print("카드 이미지 생성...")

        cards_dir = os.path.join(self.data_dir, 'cards')
        output_cards_dir = os.path.join(self.output_dir, 'cards')
        os.makedirs(output_cards_dir, exist_ok=True)

        for filename in sorted(os.listdir(cards_dir)):
            if filename.endswith('.json'):
                filepath = os.path.join(cards_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # gapja 계열은 gapja_generator 가 담당 — skip
                if data.get('layout') == 'gapja_card':
                    continue

                # cards 키가 있는지 확인
                if 'cards' in data:
                    card_type = data['type']
                    layout_name = data.get('layout')
                    layout_config = self._load_layout(layout_name) if layout_name else None
                    card_output_dir = os.path.join(output_cards_dir, card_type)
                    os.makedirs(card_output_dir, exist_ok=True)

                    for card in data['cards']:
                        if layout_config:
                            self._create_card_with_layout(card, layout_config, card_output_dir)
                        else:
                            self.create_card_from_data(card, card_type, card_output_dir)

    def _create_card_with_layout(self, card_data: dict, layout_config: dict, output_dir: str):
        """레이아웃 엔진을 통한 카드 이미지 생성"""
        image = self._renderer.render_card(card_data, layout_config, {})
        filename = f"{card_data['id']}.png"
        output_path = os.path.join(output_dir, filename)
        image.save(output_path, 'PNG', dpi=(self.card_config['dpi'], self.card_config['dpi']))
        print(f"생성: {output_path}")
        return output_path
    
    def create_card_from_data(self, card_data, card_type, output_dir):
        """카드 데이터로부터 이미지 생성"""
        # 캔버스 생성
        img = Image.new('RGB', 
                       (self.card_config['width'], self.card_config['height']), 
                       self.colors['background'])
        draw = ImageDraw.Draw(img)
        
        # 테두리 그리기
        border_rect = [
            self.card_config['margin'], 
            self.card_config['margin'],
            self.card_config['width'] - self.card_config['margin'],
            self.card_config['height'] - self.card_config['margin']
        ]
        draw.rectangle(border_rect, outline=self.colors['card_border'], 
                      width=self.card_config['border_width'])
        
        # 제목 그리기 (title 또는 gapja_name 사용)
        try:
            title_font = ImageFont.truetype(self.fonts['title'][0], 
                                          self.fonts['title'][1])
        except:
            title_font = ImageFont.load_default()
            
        # 60갑자 카드인지 확인
        if 'gapja_name' in card_data:
            title = card_data['gapja_name']
        else:
            title = card_data['title']
            
        title_bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (self.card_config['width'] - title_width) // 2
        title_y = self.card_config['margin'] + 20
        
        draw.text((title_x, title_y), title, 
                 fill=self.colors['text_primary'], font=title_font)
        
        # 내용 그리기
        try:
            body_font = ImageFont.truetype(self.fonts['body'][0], 
                                         self.fonts['body'][1])
        except:
            body_font = ImageFont.load_default()
            
        # 60갑자 카드인지 확인
        if 'content' in card_data:
            content = card_data['content']
        else:
            content = f"{card_data.get('animal', '')} {card_data.get('gan', '')}{card_data.get('ji', '')}"
            
        lines = wrap_text(content, body_font,
                          self.card_config['width'] - 2 * self.card_config['margin'] - 40)
        
        y_offset = title_y + 50
        for line in lines:
            draw.text((self.card_config['margin'] + 20, y_offset), line,
                     fill=self.colors['text_secondary'], font=body_font)
            y_offset += 25
        
        # 비용/효과 정보 추가 (있는 경우)
        if 'cost' in card_data:
            cost_text = "비용: " + ", ".join([f"{k} {v}" for k, v in card_data['cost'].items()])
            draw.text((self.card_config['margin'] + 20, y_offset + 20), cost_text,
                     fill=self.colors['accent'], font=body_font)
        
        # 파일 저장
        filename = f"{card_data['id']}.png"
        output_path = os.path.join(output_dir, filename)
        img.save(output_path, 'PNG', dpi=(self.card_config['dpi'], self.card_config['dpi']))
        
        print(f"생성: {output_path}")
        return output_path
    
    def generate_tokens(self):
        """토큰 데이터를 기반으로 이미지 생성"""
        print("토큰 이미지 생성...")
        
        tokens_dir = os.path.join(self.data_dir, 'tokens')
        output_tokens_dir = os.path.join(self.output_dir, 'tokens')
        os.makedirs(output_tokens_dir, exist_ok=True)
        
        for filename in sorted(os.listdir(tokens_dir)):
            if filename.endswith('.json'):
                filepath = os.path.join(tokens_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                token_type = data['type']
                token_output_dir = os.path.join(output_tokens_dir, token_type)
                os.makedirs(token_output_dir, exist_ok=True)
                
                for token in data['tokens']:
                    self.create_token_from_data(token, token_output_dir)
    
    def create_token_from_data(self, token_data, output_dir):
        """토큰 데이터로부터 이미지 생성"""
        size = 60
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # 원형 토큰 그리기
        color = token_data['color']
        fill_color = self.colors.get(f'player_{color}', self.colors['accent'])
        
        draw.ellipse([5, 5, size-5, size-5], 
                    fill=fill_color, 
                    outline=self.colors['card_border'], 
                    width=2)
        
        # 토큰 레이블 그리기
        try:
            font = ImageFont.truetype(self.fonts['small'][0], 
                                     self.fonts['small'][1])
        except:
            font = ImageFont.load_default()
            
        label = token_data['label']
        bbox = draw.textbbox((0, 0), label, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (size - text_width) // 2
        y = (size - text_height) // 2
        
        draw.text((x, y), label, 
                 fill='white', font=font)
        
        # 파일 저장
        filename = f"{token_data['id']}.png"
        output_path = os.path.join(output_dir, filename)
        img.save(output_path, 'PNG')
        
        print(f"생성: {output_path}")
        return output_path
    
    def generate_boards(self):
        """보드 데이터를 기반으로 이미지 생성"""
        print("보드 이미지 생성...")
        
        boards_dir = os.path.join(self.data_dir, 'board')
        output_boards_dir = os.path.join(self.output_dir, 'board')
        os.makedirs(output_boards_dir, exist_ok=True)
        
        for filename in sorted(os.listdir(boards_dir)):
            if filename.endswith('.json'):
                filepath = os.path.join(boards_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.create_board_from_data(data['board'], output_boards_dir)
    
    def create_board_from_data(self, board_data, output_dir):
        """보드 데이터로부터 이미지 생성"""
        img = Image.new('RGB', 
                       (board_data['width'], board_data['height']), 
                       self.colors['background'])
        draw = ImageDraw.Draw(img)
        
        # 그리드 그리기
        grid_size = board_data['grid_size']
        margin = board_data['margin']
        
        # 수평선
        for y in range(margin, board_data['height'] - margin, grid_size):
            draw.line([(margin, y), (board_data['width'] - margin, y)], 
                     fill=self.colors['card_border'], width=1)
        
        # 수직선
        for x in range(margin, board_data['width'] - margin, grid_size):
            draw.line([(x, margin), (x, board_data['height'] - margin)], 
                     fill=self.colors['card_border'], width=1)
        
        # 섹션 그리기
        for section in board_data['sections']:
            x = section['position']['x'] + margin
            y = section['position']['y'] + margin
            width = section['size']['width']
            height = section['size']['height']
            
            # 섹션 테두리
            draw.rectangle([x, y, x + width, y + height], 
                         outline=self.colors['accent'], width=2)
            
            # 섹션 제목
            try:
                font = ImageFont.truetype(self.fonts['title'][0], 
                                         self.fonts['title'][1])
            except:
                font = ImageFont.load_default()
                
            title = section['name']
            bbox = draw.textbbox((0, 0), title, font=font)
            text_width = bbox[2] - bbox[0]
            text_x = x + (width - text_width) // 2
            text_y = y + 10
            
            draw.text((text_x, text_y), title, 
                     fill=self.colors['text_primary'], font=font)
        
        # 보드 제목
        try:
            title_font = ImageFont.truetype(self.fonts['title'][0], 
                                          self.fonts['title'][1] * 2)
        except:
            title_font = ImageFont.load_default()
            
        title = board_data['title']
        bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = bbox[2] - bbox[0]
        title_x = (board_data['width'] - title_width) // 2
        title_y = 30
        
        draw.text((title_x, title_y), title, 
                 fill=self.colors['text_primary'], font=title_font)
        
        # 파일 저장
        filename = f"{board_data['id']}.png"
        output_path = os.path.join(output_dir, filename)
        img.save(output_path, 'PNG', 
                dpi=(self.board_config['dpi'], self.board_config['dpi']))
        
        print(f"생성: {output_path}")
        return output_path
    

if __name__ == "__main__":
    generator = DataImageGenerator()
    generator.generate_cards()
    generator.generate_tokens()
    generator.generate_boards()
