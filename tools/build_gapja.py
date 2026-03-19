"""
60갑자 카드 빌드 스크립트
60갑자 카드 시스템을 통합하여 전체 빌드를 수행합니다.
"""

import os
import sys
import json
from datetime import datetime
from jinja2 import Template
import markdown

# 프로젝트 경로 설정
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROTOTYPE_SCRIPTS = os.path.join(PROJECT_ROOT, 'prototype', 'scripts')
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
RULEBOOK_SRC = os.path.join(PROJECT_ROOT, 'rulebook', 'src')
RULEBOOK_BUILD = os.path.join(PROJECT_ROOT, 'rulebook', 'build')

sys.path.append(PROTOTYPE_SCRIPTS)

class GapjaProjectBuilder:
    def __init__(self):
        self.data_dir = DATA_DIR
        self.components = {
            'cards': [],
            'tokens': [],
            'board': []
        }
        
    def load_all_data(self):
        """모든 데이터 로드"""
        print("데이터 로드 시작...")
        
        # 기존 카드 데이터 로드
        self._load_existing_cards()
        
        # 60갑자 카드 데이터 로드
        self._load_gapja_cards()
        
        # 토큰 데이터 로드
        self._load_tokens()
        
        # 보드 데이터 로드
        self._load_boards()
        
        print("데이터 로드 완료!")
        
    def _load_existing_cards(self):
        """기존 카드 데이터 로드"""
        cards_dir = os.path.join(self.data_dir, 'cards')
        for filename in os.listdir(cards_dir):
            if filename.endswith('.json') and not filename.startswith('gapja') and not filename.startswith('ganzi') and not filename.startswith('zodiac') and not filename.endswith('_gapja.json'):
                filepath = os.path.join(cards_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # cards 키가 있는지 확인
                if 'cards' in data:
                    card_type = data['type']
                    for card in data['cards']:
                        self.components['cards'].append({
                            'type': card_type,
                            'name': card['title'],
                            'id': card['id'],
                            'count': 1
                        })
    
    def _load_gapja_cards(self):
        """60갑자 카드 데이터 로드"""
        gapja_files = ['noron_gapja.json', 'soron_gapja.json']
        
        for filename in gapja_files:
            filepath = os.path.join(self.data_dir, 'cards', filename)
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                faction = data['type']
                for card in data['cards']:
                    self.components['cards'].append({
                        'type': f'{faction} 카드',
                        'name': f"{card['number']}. {card['gapja_name']} ({card['animal']})",
                        'id': card['id'],
                        'count': 1
                    })
    
    def _load_tokens(self):
        """토큰 데이터 로드"""
        tokens_dir = os.path.join(self.data_dir, 'tokens')
        for filename in os.listdir(tokens_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(tokens_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                token_type = data['type']
                for token in data['tokens']:
                    self.components['tokens'].append({
                        'type': f"{token['type']} 토큰",
                        'color': token['color'],
                        'count': token['count'],
                        'id': token['id']
                    })
    
    def _load_boards(self):
        """보드 데이터 로드"""
        boards_dir = os.path.join(self.data_dir, 'board')
        for filename in os.listdir(boards_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(boards_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                board = data['board']
                self.components['board'].append({
                    'type': '메인 보드',
                    'name': board['title'],
                    'id': board['id'],
                    'count': 1
                })
    
    def generate_all_images(self):
        """모든 이미지 생성"""
        print("이미지 생성 시작...")
        
        # 기존 이미지 생성
        from data_generator import DataImageGenerator
        existing_generator = DataImageGenerator()
        existing_generator.generate_all()
        
        # 60갑자 카드 생성
        from gapja_generator import GapjaCardGenerator
        gapja_generator = GapjaCardGenerator()
        gapja_generator.generate_all_gapja_cards()
        
        print("모든 이미지 생성 완료!")
        
    def generate_rulebook(self):
        """규칙서 생성"""
        print("규칙서 생성 시작...")
        
        # 템플릿 로드
        template_path = os.path.join(RULEBOOK_SRC, 'template.md')
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # 컴포넌트 목록 포맷팅
        components_text = self._format_components()
        
        # 템플릿 렌더링
        template = Template(template_content)
        rendered = template.render(
            date=datetime.now().strftime('%Y년 %m월 %d일'),
            components=components_text
        )
        
        # 마크다운을 HTML로 변환
        html = markdown.markdown(rendered, extensions=['tables'])
        
        # HTML에 CSS 스타일 추가
        styled_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>영조의나라 규칙서</title>
            <style>
                body {{ font-family: 'Malgun Gothic', sans-serif; line-height: 1.6; margin: 40px; }}
                h1 {{ color: #2C1810; border-bottom: 2px solid #D4AF37; }}
                h2 {{ color: #654321; }}
                h3 {{ color: #8B4513; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #F5F5DC; }}
                .card-count {{ font-size: 0.9em; color: #666; }}
            </style>
        </head>
        <body>
            {html}
        </body>
        </html>
        """
        
        # HTML로 저장
        output_path = os.path.join(RULEBOOK_BUILD, 'rulebook.html')
        os.makedirs(RULEBOOK_BUILD, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(styled_html)
        
        print(f"규칙서 생성 완료: {output_path}")
    
    def generate_tabletop_json(self):
        """Tabletop Simulator JSON 생성"""
        print("Tabletop Simulator JSON 생성 시작...")
        
        # 기본 JSON 구조
        tabletop_json = {
            "SaveName": "영조의나라",
            "Date": datetime.now().isoformat(),
            "VersionNumber": "1.0",
            "GameMode": "영조의나라",
            "Table": "",
            "Sky": "Sky_Box",
            "Note": "영조의나라 보드게임 프로토타입 (60갑자 카드 포함)",
            "Rules": "",
            "ObjectStates": []
        }
        
        # 보드 객체 추가
        tabletop_json["ObjectStates"].append({
            "Name": "Custom_Model",
            "Transform": {
                "posX": 0,
                "posY": 1,
                "posZ": 0,
                "rotX": 0,
                "rotY": 0,
                "rotZ": 0,
                "scaleX": 1,
                "scaleY": 1,
                "scaleZ": 1
            },
            "CustomImage": {
                "ImageURL": "file://images/board/main_board.png",
                "WidthScale": 2.4,
                "HeightScale": 1.8
            },
            "Locked": True
        })
        
        # 카드 덱 추가
        card_decks = {}
        for card in self.components['cards']:
            card_type = card['type']
            if card_type not in card_decks:
                card_decks[card_type] = []
            card_decks[card_type].append(card)
        
        deck_index = 0
        for deck_name, cards in card_decks.items():
            deck_index += 1
            
            # 덱 객체 생성
            tabletop_json["ObjectStates"].append({
                "Name": "Deck",
                "Transform": {
                    "posX": -4 + (deck_index - 1) * 2,
                    "posY": 1,
                    "posZ": 0,
                    "rotX": 0,
                    "rotY": 0,
                    "rotZ": 0,
                    "scaleX": 1,
                    "scaleY": 1,
                    "scaleZ": 1
                },
                "DeckIDs": list(range(100 + deck_index * 100, 100 + deck_index * 100 + len(cards))),
                "ContainedObjects": [
                    {
                        "Name": "Card",
                        "CardID": 100 + deck_index * 100 + i,
                        "CustomImage": {
                            "ImageURL": f"file://images/cards/{deck_name}/{card['id']}.png",
                            "WidthScale": 0.3,
                            "HeightScale": 0.42
                        }
                    } for i, card in enumerate(cards)
                ]
            })
        
        # 토큰 백 추가
        token_bags = {}
        for token in self.components['tokens']:
            color = token['color']
            if color not in token_bags:
                token_bags[color] = []
            token_bags[color].append(token)
        
        bag_index = 0
        for color, tokens in token_bags.items():
            bag_index += 1
            
            contained_objects = []
            for token in tokens:
                for _ in range(token['count']):
                    contained_objects.append({
                        "Name": "Token",
                        "CustomImage": {
                            "ImageURL": f"file://images/tokens/player_tokens/{token['id']}.png"
                        }
                    })
            
            tabletop_json["ObjectStates"].append({
                "Name": "Bag",
                "Transform": {
                    "posX": -3 + bag_index * 2,
                    "posY": 1,
                    "posZ": 2,
                    "rotX": 0,
                    "rotY": 0,
                    "rotZ": 0,
                    "scaleX": 1,
                    "scaleY": 1,
                    "scaleZ": 1
                },
                "Color": color,
                "Bag": {
                    "ContainedObjects": contained_objects
                }
            })
        
        # JSON 파일 저장
        output_path = os.path.join(PROJECT_ROOT, 'prototype', 'tabletop', 'yeongjo_kingdom_gapja.json')
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(tabletop_json, f, ensure_ascii=False, indent=2)
        
        print(f"Tabletop Simulator JSON 생성 완료: {output_path}")
    
    def _format_components(self):
        """컴포넌트 목록 포맷팅"""
        formatted = {
            'board': '',
            'cards': '',
            'tokens': ''
        }
        
        # 보드
        if self.components['board']:
            formatted['board'] = '\n'.join(
                f"- {item['name']} ({item['count']}개)" 
                for item in self.components['board']
            )
        
        # 카드
        if self.components['cards']:
            card_groups = {}
            for card in self.components['cards']:
                card_type = card['type']
                if card_type not in card_groups:
                    card_groups[card_type] = []
                card_groups[card_type].append(card)
            
            formatted['cards'] = '\n'.join(
                f"### {card_type} <span class='card-count'>({len(cards)}장)</span>\n" + 
                '\n'.join(f"- {card['name']}" for card in cards)
                for card_type, cards in card_groups.items()
            )
        
        # 토큰
        if self.components['tokens']:
            token_groups = {}
            for token in self.components['tokens']:
                token_type = token['type']
                if token_type not in token_groups:
                    token_groups[token_type] = set()
                token_groups[token_type].add(token['color'])
            
            formatted['tokens'] = '\n'.join(
                f"- {token_type} ({', '.join(sorted(colors))}, 각 5개)"
                for token_type, colors in token_groups.items()
            )
        
        return formatted
    
    def build_all(self):
        """전체 빌드 실행"""
        print("60갑자 포함 영조의나라 프로젝트 빌드 시작...")
        print("=" * 60)
        
        try:
            self.load_all_data()
            print("=" * 60)
            self.generate_all_images()
            print("=" * 60)
            self.generate_rulebook()
            print("=" * 60)
            self.generate_tabletop_json()
            print("=" * 60)
            print("60갑자 포함 빌드 완료!")
            
            # 통계 출력
            self._print_statistics()
            
        except Exception as e:
            print(f"빌드 실패: {e}")
            import traceback
            traceback.print_exc()
    
    def _print_statistics(self):
        """빌드 통계 출력"""
        print("\n" + "=" * 60)
        print("빌드 통계")
        print("=" * 60)
        
        card_count = len(self.components['cards'])
        token_count = len(self.components['tokens'])
        board_count = len(self.components['board'])
        
        print(f"총 카드 수: {card_count}장")
        print(f"총 토큰 수: {token_count}개")
        print(f"총 보드 수: {board_count}개")
        
        # 카드 종류별 통계
        card_types = {}
        for card in self.components['cards']:
            card_type = card['type']
            card_types[card_type] = card_types.get(card_type, 0) + 1
        
        print("\n카드 종류별:")
        for card_type, count in card_types.items():
            print(f"  - {card_type}: {count}장")

if __name__ == "__main__":
    builder = GapjaProjectBuilder()
    builder.build_all()
