"""
빠른 빌드 스크립트 - 이미지만 생성
규칙서 수정 시마다 이미지를 빠르게 재생성하기 위한 스크립트
"""

import os
import sys

# 프로젝트 경로 설정
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROTOTYPE_SCRIPTS = os.path.join(PROJECT_ROOT, 'prototype', 'scripts')

sys.path.append(PROTOTYPE_SCRIPTS)

def quick_image_build():
    """이미지만 빠르게 생성"""
    print("이미지 빠른 생성 시작...")
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
        print(f"생성: {path}")
    
    # 플레이어 토큰들
    for color in ['red', 'blue', 'green', 'yellow']:
        for token_type in ['influence', 'action', 'resource']:
            path = generator.create_token(token_type, color)
            print(f"생성: {path}")
    
    # 메인 보드
    board_path = generator.create_board({})
    print(f"생성: {board_path}")
    
    print("이미지 빠른 생성 완료!")

if __name__ == "__main__":
    quick_image_build()
