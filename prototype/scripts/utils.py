"""
공통 유틸리티
"""

from PIL import Image, ImageDraw, ImageFont


# 텍스트 너비 측정용 공유 draw 객체 (임시 1×1 이미지)
_measure_draw = ImageDraw.Draw(Image.new('RGB', (1, 1)))


def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list:
    """text를 max_width 픽셀 안에 들어오도록 줄 단위로 분리해 반환.

    공백 기준으로 단어를 분리하며, 단어 하나가 max_width를 초과하면
    그 단어만 한 줄로 처리한다.
    """
    lines: list = []
    current: list = []

    for word in text.split(' '):
        test_line = ' '.join(current + [word])
        bbox = _measure_draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current.append(word)
        else:
            if current:
                lines.append(' '.join(current))
            current = [word]

    if current:
        lines.append(' '.join(current))

    return lines
