from typing import Dict, Any, List
from abc import ABC, abstractmethod

class ContentGeneratorInterface(ABC):
    """꽃 관련 콘텐츠를 생성하는 인터페이스"""
    
    @abstractmethod
    def generate_blog_post(self, flower_data: Dict[str, Any], image_paths: List[str]) -> str:
        """
        꽃 데이터를 기반으로 네이버 블로그용 포스트를 생성합니다.
        
        Args:
            flower_data: 꽃 분석 데이터
            image_paths: 이미지 파일 경로 목록
            
        Returns:
            str: 생성된 블로그 포스트 HTML 콘텐츠
            
        Raises:
            ContentGenerationError: 콘텐츠 생성 중 오류가 발생한 경우
        """
        pass
    
    @abstractmethod
    def generate_instagram_caption(self, flower_data: Dict[str, Any]) -> str:
        """
        꽃 데이터를 기반으로 인스타그램 캡션을 생성합니다.
        
        Args:
            flower_data: 꽃 분석 데이터
            
        Returns:
            str: 생성된 인스타그램 캡션
            
        Raises:
            ContentGenerationError: 콘텐츠 생성 중 오류가 발생한 경우
        """
        pass
    
    @abstractmethod
    def generate_tags(self, flower_data: Dict[str, Any]) -> List[str]:
        """
        꽃 데이터를 기반으로 해시태그를 생성합니다.
        
        Args:
            flower_data: 꽃 분석 데이터
            
        Returns:
            List[str]: 생성된 해시태그 목록
            
        Raises:
            ContentGenerationError: 콘텐츠 생성 중 오류가 발생한 경우
        """
        pass