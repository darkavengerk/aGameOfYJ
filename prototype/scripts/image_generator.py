"""
영조의나라 보드게임 이미지 생성기
카드, 보드, 토큰 등 게임 컴포넌트 이미지를 자동으로 생성합니다.
"""

from PIL import Image, ImageDraw, ImageFont
import os
from config import CARD_CONFIG, BOARD_CONFIG, COLORS, FONTS, OUTPUT_PATHS

class ImageGenerator:
    def __init__(self):
        self.card_config = CARD_CONFIG
        self.board_config = BOARD_CONFIG
        self.colors = COLORS
        self.fonts = FONTS
        
    def create_card(self, title, content, card_type='policy', output_filename=None):
        """카드 이미지 생성"""
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
        
        # 제목 그리기
        try:
            title_font = ImageFont.truetype(self.fonts['title'][0], 
                                          self.fonts['title'][1])
        except:
            title_font = ImageFont.load_default()
            
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
            
        # 텍스트 자동 줄바꿈
        lines = self._wrap_text(content, body_font, 
                               self.card_config['width'] - 2 * self.card_config['margin'] - 40)
        
        y_offset = title_y + 50
        for line in lines:
            draw.text((self.card_config['margin'] + 20, y_offset), line,
                     fill=self.colors['text_secondary'], font=body_font)
            y_offset += 25
        
        # 파일 저장
        if output_filename is None:
            output_filename = f"{card_type}_{title.replace(' ', '_')}.png"
            
        output_path = os.path.join(os.path.dirname(__file__), OUTPUT_PATHS['images'], output_filename)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img.save(output_path, 'PNG', dpi=(self.card_config['dpi'], self.card_config['dpi']))
        
        return output_path
    
    def create_token(self, token_type, player_color=None, output_filename=None):
        """토큰 이미지 생성"""
        size = 60  # 토큰 크기
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))  # 투명 배경
        draw = ImageDraw.Draw(img)
        
        # 원형 토큰 그리기
        if player_color:
            fill_color = self.colors.get(f'player_{player_color}', self.colors['accent'])
        else:
            fill_color = self.colors['accent']
            
        draw.ellipse([5, 5, size-5, size-5], 
                    fill=fill_color, 
                    outline=self.colors['card_border'], 
                    width=2)
        
        # 토큰 타입 텍스트
        try:
            font = ImageFont.truetype(self.fonts['small'][0], 
                                     self.fonts['small'][1])
        except:
            font = ImageFont.load_default()
            
        # 토큰 타입 약자
        token_abbr = {
            'influence': '영',
            'action': '행',
            'resource': '자'
        }.get(token_type, '?')
        
        bbox = draw.textbbox((0, 0), token_abbr, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (size - text_width) // 2
        y = (size - text_height) // 2
        
        draw.text((x, y), token_abbr, 
                 fill='white', font=font)
        
        # 파일 저장
        if output_filename is None:
            output_filename = f"token_{token_type}_{player_color or 'neutral'}.png"
            
        output_path = os.path.join(os.path.dirname(__file__), OUTPUT_PATHS['images'], output_filename)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img.save(output_path, 'PNG')
        
        return output_path
    
    def create_board(self, board_data, output_filename='main_board.png'):
        """메인 보드 이미지 생성"""
        img = Image.new('RGB', 
                       (self.board_config['width'], self.board_config['height']), 
                       self.colors['background'])
        draw = ImageDraw.Draw(img)
        
        # 그리드 그리기
        grid_size = self.board_config['grid_size']
        margin = self.board_config['margin']
        
        # 수평선
        for y in range(margin, self.board_config['height'] - margin, grid_size):
            draw.line([(margin, y), (self.board_config['width'] - margin, y)], 
                     fill=self.colors['card_border'], width=1)
        
        # 수직선
        for x in range(margin, self.board_config['width'] - margin, grid_size):
            draw.line([(x, margin), (x, self.board_config['height'] - margin)], 
                     fill=self.colors['card_border'], width=1)
        
        # 보드 제목
        try:
            title_font = ImageFont.truetype(self.fonts['title'][0], 
                                          self.fonts['title'][1] * 2)
        except:
            title_font = ImageFont.load_default()
            
        title = "영조의나라"
        bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = bbox[2] - bbox[0]
        title_x = (self.board_config['width'] - title_width) // 2
        title_y = 30
        
        draw.text((title_x, title_y), title, 
                 fill=self.colors['text_primary'], font=title_font)
        
        # 파일 저장
        output_path = os.path.join(os.path.dirname(__file__), OUTPUT_PATHS['images'], output_filename)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img.save(output_path, 'PNG', 
                dpi=(self.board_config['dpi'], self.board_config['dpi']))
        
        return output_path
    
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

# 사용 예시
if __name__ == "__main__":
    generator = ImageGenerator()
    
    # 샘플 카드 생성
    generator.create_card(
        title="탕평책",
        content="당파 간의 균형을 맞추어 정국을 안정시킵니다. 영향력 2를 얻습니다.",
        card_type="policy"
    )
    
    # 샘플 토큰 생성
    for color in ['red', 'blue', 'green', 'yellow']:
        generator.create_token('influence', color)
    
    # 메인 보드 생성
    generator.create_board({})
    
    print("샘플 이미지 생성 완료!")
