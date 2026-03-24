"""ComponentHandler 추상 기반 클래스"""

import hashlib
import json
from abc import ABC, abstractmethod


class ComponentHandler(ABC):
    """모든 컴포넌트 핸들러의 기반 클래스.

    각 컴포넌트 타입(카드 덱, 보드, 토큰 등)은 이 클래스를 상속해
    자신의 빌드 로직을 캡슐화한다.

    build.py의 HANDLERS 목록에 인스턴스를 등록하면
    새 컴포넌트를 한 줄 추가만으로 빌드 파이프라인에 포함시킬 수 있다.
    """

    @abstractmethod
    def generate_images(self, cache: dict, force: bool = False) -> list:
        """이미지를 생성하고 출력된 PNG 경로 목록을 반환한다.

        cache: {cache_key: {'input_hash': ..., 'output_path': ...}}
               핸들러는 입력 해시가 같고 출력 파일이 존재하면 재생성을 건너뛴다.
        force: True 이면 캐시를 무시하고 전부 재생성한다.
        """
        raise NotImplementedError

    def create_tts_objects(self, deck_info: dict) -> list:
        """TTS ObjectState 딕셔너리 목록을 반환한다 (기본: 빈 목록).

        deck_info: step2 가 생성한 {deck_name: {cols, rows, count, url, path}} 맵.
        """
        return []

    def get_preview_items(self, deck_info: dict) -> list:
        """미리보기 HTML 아이템 목록을 반환한다 (기본: 빈 목록)."""
        return []

    @staticmethod
    def _input_hash(data) -> str:
        """딕셔너리/리스트 데이터를 직렬화해 MD5 해시를 반환한다."""
        return hashlib.md5(
            json.dumps(data, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest()
