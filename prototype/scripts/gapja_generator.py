"""
60갑자 카드 생성기
다형성을 활용한 60갑자 카드 자동 생성 시스템
"""

import json
import os
from card_layout_engine import CardRenderer
from config import CARD_CONFIG

class GapjaCardGenerator:
    def __init__(self, data_dir="../../data", output_dir="../images"):
        self.data_dir = os.path.join(os.path.dirname(__file__), data_dir)
        self.output_dir = os.path.join(os.path.dirname(__file__), output_dir)
        self.renderer = CardRenderer(CARD_CONFIG['width'], CARD_CONFIG['height'])
        
    def generate_all_gapja_cards(self):
        """모든 60갑자 카드 생성"""
        print("60갑자 카드 생성 시작...")
        
        # 설정 파일 로드
        layout_config = self._load_layout_config()
        colors_config = self._load_colors_config()
        
        # 노론 카드 생성
        self._generate_faction_cards('noron', layout_config, colors_config)
        
        # 소론 카드 생성
        self._generate_faction_cards('soron', layout_config, colors_config)
        
        print("60갑자 카드 생성 완료!")
    
    def _load_layout_config(self):
        """레이아웃 설정 로드"""
        config_path = os.path.join(self.data_dir, 'cards', 'gapja_cards.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data['layout']
    
    def _load_colors_config(self):
        """색상 설정 로드"""
        config_path = os.path.join(self.data_dir, 'cards', 'ganzi_colors.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _generate_faction_cards(self, faction, layout_config, colors_config):
        """파벌 카드 생성"""
        print(f"{faction} 카드 생성...")
        
        # 카드 데이터 로드
        cards_data = self._load_faction_cards(faction)
        
        # 출력 디렉토리 생성
        output_dir = os.path.join(self.output_dir, 'cards', f'{faction}_gapja')
        os.makedirs(output_dir, exist_ok=True)
        
        # 카드 생성
        for card_data in cards_data['cards']:
            self._generate_single_card(card_data, layout_config, colors_config, output_dir)
    
    def _load_faction_cards(self, faction):
        """파벌 카드 데이터 로드"""
        filename = f'{faction}_gapja.json'
        filepath = os.path.join(self.data_dir, 'cards', filename)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _generate_single_card(self, card_data, layout_config, colors_config, output_dir):
        """단일 카드 생성"""
        # 카드 렌더링
        image = self.renderer.render_card(card_data, layout_config, colors_config)
        
        # 파일 저장
        filename = f"{card_data['id']}.png"
        output_path = os.path.join(output_dir, filename)
        
        image.save(output_path, 'PNG', dpi=(CARD_CONFIG['dpi'], CARD_CONFIG['dpi']))
        
        print(f"생성: {output_path}")
        return output_path
    
    def generate_sample_cards(self):
        """샘플 카드 생성 (테스트용)"""
        print("샘플 60갑자 카드 생성...")
        
        # 설정 로드
        layout_config = self._load_layout_config()
        colors_config = self._load_colors_config()
        
        # 샘플 카드 데이터
        sample_cards = [
            {
                "id": "sample_001",
                "number": 1,
                "gapja_name": "갑자",
                "gan": "갑",
                "ji": "자",
                "animal": "쥐",
                "gan_index": 0,
                "zi_index": 0,
                "element": "목",
                "element_info": {
                    "name": "목",
                    "english": "Wood",
                    "color": "#1E90FF",
                    "direction": "동",
                    "season": "봄"
                },
                "special_ability": None
            },
            {
                "id": "sample_011",
                "number": 11,
                "gapja_name": "갑술",
                "gan": "갑",
                "ji": "술",
                "animal": "개",
                "gan_index": 0,
                "zi_index": 10,
                "element": "목",
                "element_info": {
                    "name": "목",
                    "english": "Wood",
                    "color": "#1E90FF",
                    "direction": "동",
                    "season": "봄"
                },
                "special_ability": {
                    "name": "특별한 기회",
                    "description": "이 카드를 사용할 때 추가 행동을 1번 더 할 수 있다."
                }
            }
        ]
        
        # 출력 디렉토리
        output_dir = os.path.join(self.output_dir, 'cards', 'sample_gapja')
        os.makedirs(output_dir, exist_ok=True)
        
        # 샘플 카드 생성
        for card_data in sample_cards:
            self._generate_single_card(card_data, layout_config, colors_config, output_dir)

if __name__ == "__main__":
    generator = GapjaCardGenerator()
    
    # 전체 60갑자 카드 생성
    generator.generate_all_gapja_cards()
    
    # 샘플 카드 생성 (테스트용)
    generator.generate_sample_cards()
