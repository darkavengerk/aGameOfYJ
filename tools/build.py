"""
영조의나라 프로젝트 빌드 스크립트
이미지 생성, 규칙서 컴파일, Tabletop Simulator JSON 생성을 자동화합니다.
"""

import os
import sys
import json
from datetime import datetime
from jinja2 import Template
import markdown
import pdfkit

# 프로젝트 경로 설정
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROTOTYPE_SCRIPTS = os.path.join(PROJECT_ROOT, 'prototype', 'scripts')
RULEBOOK_SRC = os.path.join(PROJECT_ROOT, 'rulebook', 'src')
RULEBOOK_BUILD = os.path.join(PROJECT_ROOT, 'rulebook', 'build')

sys.path.append(PROTOTYPE_SCRIPTS)

class ProjectBuilder:
    def __init__(self):
        self.components = {
            'cards': [],
            'tokens': [],
            'board': []
        }
        
    def generate_images(self):
        """프로토타입 이미지 생성"""
        print("이미지 생성 시작...")
        from image_generator import ImageGenerator
        
        generator = ImageGenerator()
        
        # 샘플 정책 카드들
        policy_cards = [
            ("탕평책", "당파 간 균형을 맞춰 정국 안정. 영향력 2 획득."),
            ("규장각 설치", "학문 기관 설치. 지식 토큰 2개 획득."),
            ("군제 개혁", "군사력 강화. 방어 토큰 1개 획득."),
            ("대동법 실시", "세금 제도 개혁. 자원 토큰 3개 획득.")
        ]
        
        for title, content in policy_cards:
            path = generator.create_card(title, content, 'policy')
            self.components['cards'].append({
                'type': '정책 카드',
                'name': title,
                'count': 1
            })
            print(f"생성: {path}")
        
        # 사건 카드들
        event_cards = [
            ("가뭄", "농업 피해. 모든 플레이어 영향력 1 감소."),
            ("이조전랑 논쟁", "조정 분열. 다음 라운드 행동 토큰 1개 감소."),
            ("민란 발생", "백성 불만. 리더 플레이어 영향력 2 감소."),
            ("청과의 무역", "경제 활성화. 모든 플레이어 자원 토큰 1개 획득.")
        ]
        
        for title, content in event_cards:
            path = generator.create_card(title, content, 'event')
            self.components['cards'].append({
                'type': '사건 카드',
                'name': title,
                'count': 1
            })
            print(f"생성: {path}")
        
        # 플레이어 토큰들
        for color in ['red', 'blue', 'green', 'yellow']:
            for token_type in ['influence', 'action', 'resource']:
                path = generator.create_token(token_type, color)
                self.components['tokens'].append({
                    'type': f'{token_type} 토큰',
                    'color': color,
                    'count': 5
                })
                print(f"생성: {path}")
        
        # 메인 보드
        board_path = generator.create_board({})
        self.components['board'].append({
            'type': '메인 보드',
            'name': '영조의나라',
            'count': 1
        })
        print(f"생성: {board_path}")
        
        print("이미지 생성 완료!")
        
    def generate_rulebook(self):
        """규칙서 PDF 생성"""
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
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #F5F5DC; }}
            </style>
        </head>
        <body>
            {html}
        </body>
        </html>
        """
        
        # PDF로 저장
        output_path = os.path.join(RULEBOOK_BUILD, 'rulebook.pdf')
        os.makedirs(RULEBOOK_BUILD, exist_ok=True)
        
        try:
            pdfkit.from_string(styled_html, output_path, options={
                'encoding': 'UTF-8',
                'page-size': 'A4',
                'margin-top': '1cm',
                'margin-right': '1cm',
                'margin-bottom': '1cm',
                'margin-left': '1cm'
            })
            print(f"규칙서 생성 완료: {output_path}")
        except Exception as e:
            print(f"PDF 생성 실패: {e}")
            # HTML 파일로 저장
            html_path = os.path.join(RULEBOOK_BUILD, 'rulebook.html')
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(styled_html)
            print(f"HTML로 저장: {html_path}")
    
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
            "Note": "영조의나라 보드게임 프로토타입",
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
                "ImageURL": "file://images/main_board.png",
                "WidthScale": 2.4,
                "HeightScale": 1.8
            },
            "Locked": True
        })
        
        # 카드 덱 추가
        card_decks = {
            "정책 카드": [],
            "사건 카드": []
        }
        
        for card in self.components['cards']:
            deck_name = card['type']
            card_data = {
                "Name": "Card",
                "CardID": 100 + len(card_decks[deck_name]),
                "CustomImage": {
                    "ImageURL": f"file://images/{deck_name}_{card['name'].replace(' ', '_')}.png",
                    "WidthScale": 0.3,
                    "HeightScale": 0.42
                }
            }
            card_decks[deck_name].append(card_data)
        
        # 덱 객체 생성
        for deck_name, cards in card_decks.items():
            tabletop_json["ObjectStates"].append({
                "Name": "Deck",
                "Transform": {
                    "posX": -2 if "정책" in deck_name else 2,
                    "posY": 1,
                    "posZ": 0,
                    "rotX": 0,
                    "rotY": 0,
                    "rotZ": 0,
                    "scaleX": 1,
                    "scaleY": 1,
                    "scaleZ": 1
                },
                "DeckIDs": [card["CardID"] for card in cards],
                "CustomDeck": {
                    str(cards[0]["CardID"]): {
                        "FaceURL": f"file://images/{deck_name}_카드.png",
                        "BackURL": "file://images/card_back.png",
                        "NumWidth": 1,
                        "NumHeight": len(cards),
                        "BackIsHidden": True
                    }
                }
            })
        
        # 토큰 백 추가
        for color in ['red', 'blue', 'green', 'yellow']:
            tabletop_json["ObjectStates"].append({
                "Name": "Bag",
                "Transform": {
                    "posX": -3 + (['red', 'blue', 'green', 'yellow'].index(color) * 2),
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
                    "ContainedObjects": [
                        {
                            "Name": "Token",
                            "CustomImage": {
                                "ImageURL": f"file://images/token_influence_{color}.png"
                            }
                        } for _ in range(5)
                    ]
                }
            })
        
        # JSON 파일 저장
        output_path = os.path.join(PROJECT_ROOT, 'prototype', 'tabletop', 'yeongjo_kingdom.json')
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
                card_groups[card_type].append(card['name'])
            
            formatted['cards'] = '\n'.join(
                f"### {card_type}\n" + '\n'.join(f"- {name}" for name in names)
                for card_type, names in card_groups.items()
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
                f"- {token_type} ({', '.join(sorted(colors))}, 각 {self.components['tokens'][0]['count']}개)"
                for token_type, colors in token_groups.items()
            )
        
        return formatted
    
    def build_all(self):
        """전체 빌드 실행"""
        print("영조의나라 프로젝트 빌드 시작...")
        print("=" * 50)
        
        try:
            self.generate_images()
            print("=" * 50)
            self.generate_rulebook()
            print("=" * 50)
            self.generate_tabletop_json()
            print("=" * 50)
            print("빌드 완료!")
        except Exception as e:
            print(f"빌드 실패: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    builder = ProjectBuilder()
    builder.build_all()
