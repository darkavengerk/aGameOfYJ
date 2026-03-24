"""ComponentHandler 등록 패턴 — 각 컴포넌트 타입의 빌드 로직을 캡슐화한다."""
from handlers.base import ComponentHandler
from handlers.card_deck import CardDeckHandler
from handlers.gapja import GapjaHandler
from handlers.board import BoardHandler
from handlers.token import TokenHandler

__all__ = [
    'ComponentHandler',
    'CardDeckHandler',
    'GapjaHandler',
    'BoardHandler',
    'TokenHandler',
]
