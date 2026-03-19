"""
60갑자 카드 데이터 강화 스크립트
기존 카드 데이터에 오행 정보를 자동으로 추가합니다.
"""

import json
import os

class GapjaDataEnhancer:
    def __init__(self, data_dir="../../data"):
        self.data_dir = os.path.join(os.path.dirname(__file__), data_dir)
        
        # 오행 정보 로드
        self.ganzi_colors = self._load_ganzi_colors()
        self.five_elements = self._load_five_elements()
        
        # 간지-오행 매핑
        self.gan_to_element = self._create_gan_to_element_mapping()
    
    def _load_ganzi_colors(self):
        """간지 색상 정보 로드"""
        filepath = os.path.join(self.data_dir, 'cards', 'ganzi_colors.json')
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _load_five_elements(self):
        """오행 정보 로드"""
        filepath = os.path.join(self.data_dir, 'cards', 'five_elements.json')
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _create_gan_to_element_mapping(self):
        """간지-오행 매핑 생성"""
        mapping = {}
        for gan, info in self.ganzi_colors['gan_colors'].items():
            mapping[gan] = info['element']
        return mapping
    
    def enhance_gapja_cards(self):
        """60갑자 카드 데이터 강화"""
        print("60갑자 카드 데이터 강화 시작...")
        
        # 노론 카드 강화
        self._enhance_faction_cards('noron_gapja.json')
        
        # 소론 카드 강화
        self._enhance_faction_cards('soron_gapja.json')
        
        print("60갑자 카드 데이터 강화 완료!")
    
    def _enhance_faction_cards(self, filename):
        """파벌 카드 강화"""
        filepath = os.path.join(self.data_dir, 'cards', filename)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 각 카드에 오행 정보 추가
        for card in data['cards']:
            gan = card['gan']
            element = self.gan_to_element.get(gan, '토')  # 기본값은 토
            
            card['element'] = element
            card['element_info'] = self.five_elements['elements'][element]
        
        # 강화된 데이터 저장
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"강화 완료: {filename}")
    
    def generate_complete_gapja_data(self):
        """완전한 60갑자 데이터 생성 (1-60번)"""
        print("완전한 60갑자 데이터 생성...")
        
        # 60갑자 조합 생성
        gapja_combinations = self._generate_all_gapja_combinations()
        
        # 노론 데이터 생성
        noron_data = {
            "type": "noron_gapja",
            "description": "노론 60갑자 카드",
            "cards": []
        }
        
        # 소론 데이터 생성
        soron_data = {
            "type": "soron_gapja", 
            "description": "소론 60갑자 카드",
            "cards": []
        }
        
        # 간지 동물 매핑
        zhi_animals = {
            '자': '쥐', '축': '소', '인': '호랑이', '묘': '토끼',
            '진': '용', '사': '뱀', '오': '말', '미': '양',
            '신': '원숭이', '유': '닭', '술': '개', '해': '돼지'
        }
        
        # 60갑자 카드 생성
        for i, (gan, zhi) in enumerate(gapja_combinations, 1):
            element = self.gan_to_element.get(gan, '토')
            animal = zhi_animals[zhi]
            
            card_data = {
                "id": f"noron_{i:03d}",
                "number": i,
                "gapja_name": f"{gan}{zhi}",
                "gan": gan,
                "ji": zhi,
                "animal": animal,
                "gan_index": self._get_gan_index(gan),
                "zi_index": self._get_zhi_index(zhi),
                "element": element,
                "element_info": self.five_elements['elements'][element],
                "special_ability": None
            }
            
            # 노론 카드 추가
            noron_card = card_data.copy()
            noron_card["id"] = f"noron_{i:03d}"
            noron_data["cards"].append(noron_card)
            
            # 소론 카드 추가
            soron_card = card_data.copy()
            soron_card["id"] = f"soron_{i:03d}"
            # 일부 카드에 특수기능 추가 (예: 11번, 22번, 33번, 44번, 55번)
            if i in [11, 22, 33, 44, 55]:
                soron_card["special_ability"] = {
                    "name": f"{element}의 힘",
                    "description": f"{element}의 특성을 활용하여 추가 효과를 얻는다."
                }
            soron_data["cards"].append(soron_card)
        
        # 파일 저장
        self._save_gapja_data('noron_gapja.json', noron_data)
        self._save_gapja_data('soron_gapja.json', soron_data)
        
        print("완전한 60갑자 데이터 생성 완료!")
    
    def _generate_all_gapja_combinations(self):
        """60갑자 조합 생성"""
        gan_list = ['갑', '을', '병', '정', '무', '기', '경', '신', '임', '계']
        zhi_list = ['자', '축', '인', '묘', '진', '사', '오', '미', '신', '유', '술', '해']
        
        combinations = []
        gan_index = 0
        zhi_index = 0
        
        for _ in range(60):
            gan = gan_list[gan_index % 10]
            zhi = zhi_list[zhi_index % 12]
            combinations.append((gan, zhi))
            
            gan_index += 1
            zhi_index += 1
        
        return combinations
    
    def _get_gan_index(self, gan):
        """간 인덱스 반환"""
        gan_list = ['갑', '을', '병', '정', '무', '기', '경', '신', '임', '계']
        return gan_list.index(gan)
    
    def _get_zhi_index(self, zhi):
        """지 인덱스 반환"""
        zhi_list = ['자', '축', '인', '묘', '진', '사', '오', '미', '신', '유', '술', '해']
        return zhi_list.index(zhi)
    
    def _save_gapja_data(self, filename, data):
        """갑자 데이터 저장"""
        filepath = os.path.join(self.data_dir, 'cards', filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"저장 완료: {filename}")

if __name__ == "__main__":
    enhancer = GapjaDataEnhancer()
    
    # 기존 데이터 강화
    enhancer.enhance_gapja_cards()
    
    # 완전한 60갑자 데이터 생성
    enhancer.generate_complete_gapja_data()
