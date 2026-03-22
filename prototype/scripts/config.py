"""
영조의나라 보드게임 프로토타입 설정
게임 컴포넌트들의 기본 설정값을 관리합니다.
"""

# 카드 기본 설정
CARD_CONFIG = {
    'width': 300,      # 픽셀
    'height': 420,     # 픽셀
    'dpi': 300,
    'margin': 20,
    'corner_radius': 10,
    'border_width': 2
}

# 보드 설정
BOARD_CONFIG = {
    'width': 2400,     # 픽셀
    'height': 1800,    # 픽셀
    'dpi': 300,
    'grid_size': 60,   # 그리드 크기
    'margin': 100
}

# 색상 설정
COLORS = {
    'background': '#F5F5DC',    # 베이지색
    'card_border': '#8B4513',   # 갈색
    'text_primary': '#2C1810',  # 진한 갈색
    'text_secondary': '#654321', # 중간 갈색
    'accent': '#D4AF37',        # 금색
    'player_red': '#DC143C',    # 붉은색
    'player_blue': '#4169E1',   # 파란색
    'player_green': '#228B22',  # 초록색
    'player_yellow': '#FFD700'  # 노란색
}

# 폰트 설정 — 한글 지원 폰트를 우선순위 순으로 탐색
def _find_korean_font():
    """시스템에서 사용 가능한 한글 지원 폰트 경로를 반환"""
    candidates = [
        'malgun.ttf',                                                      # Windows
        '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',                  # Debian/Ubuntu
        '/usr/share/fonts/truetype/fonts-japanese-gothic.ttf',            # Debian
        '/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf',              # Debian
        '/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc',             # Fedora/RHEL
        '/usr/share/fonts/google-noto-cjk/NotoSansCJKkr-Regular.otf',    # CentOS
        '/System/Library/Fonts/AppleGothic.ttf',                          # macOS
    ]
    from PIL import ImageFont
    for path in candidates:
        try:
            ImageFont.truetype(path, 12)
            return path
        except Exception:
            continue
    return None  # load_default() 사용

_KOREAN_FONT = _find_korean_font()

FONTS = {
    'title':    (_KOREAN_FONT, 24, 'bold'),
    'subtitle': (_KOREAN_FONT, 18, 'normal'),
    'body':     (_KOREAN_FONT, 14, 'normal'),
    'small':    (_KOREAN_FONT, 12, 'normal'),
}

# 게임 컴포넌트 목록
GAME_COMPONENTS = {
    'cards': {
        'policy_cards': [],      # 정책 카드
        'event_cards': [],       # 사건 카드
        'character_cards': []     # 인물 카드
    },
    'tokens': {
        'influence_tokens': [],   # 영향력 토큰
        'action_tokens': [],      # 행동 토큰
        'resource_tokens': []     # 자원 토큰
    },
    'board': {
        'main_board': '',         # 메인 보드
        'player_mats': []         # 플레이어 매트
    }
}

# 출력 경로 설정
OUTPUT_PATHS = {
    'images': 'images/',
    'tabletop': '../tabletop/'
}
