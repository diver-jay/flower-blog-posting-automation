# core/interfaces/analyzer.py
from abc import ABC, abstractmethod
from typing import Dict, Any

class ImageAnalyzerInterface(ABC):
    """이미지 분석 인터페이스"""
    
    @abstractmethod
    def analyze_flower_image(self, image_path: str) -> Dict[str, Any]:
        """
        꽃 이미지를 분석하고 관련 정보를 반환합니다.
        
        Args:
            image_path: 이미지 파일 경로
            
        Returns:
            Dict[str, Any]: 분석된 꽃 정보
        """
        pass


# core/interfaces/content_generator.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List

class ContentGeneratorInterface(ABC):
    """콘텐츠 생성 인터페이스"""
    
    @abstractmethod
    def generate_blog_post(self, flower_data: Dict[str, Any], image_paths: List[str]) -> str:
        """
        꽃 데이터를 기반으로 블로그 포스트를 생성합니다.
        
        Args:
            flower_data: 꽃 분석 데이터
            image_paths: 이미지 파일 경로 목록
            
        Returns:
            str: 생성된 블로그 포스트 HTML 콘텐츠
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
        """
        pass


# core/interfaces/media_processor.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List

class MediaProcessorInterface(ABC):
    """미디어 처리 인터페이스"""
    
    @abstractmethod
    def apply_filter(self, image_path: str, filter_type: str = "enhance") -> str:
        """
        이미지에 필터를 적용합니다.
        
        Args:
            image_path: 이미지 파일 경로
            filter_type: 적용할 필터 유형 (enhance, blur, bw 등)
            
        Returns:
            str: 필터가 적용된 이미지 파일 경로
        """
        pass
    
    @abstractmethod
    def create_shorts_video(
        self,
        image_paths: List[str],
        flower_data: Dict[str, Any],
        output_path: str,
        duration: int = 15
    ) -> str:
        """
        여러 이미지를 사용하여 쇼츠 비디오를 생성합니다.
        
        Args:
            image_paths: 이미지 파일 경로 목록
            flower_data: 꽃 분석 데이터
            output_path: 결과 비디오 파일 경로
            duration: 비디오 길이(초)
            
        Returns:
            str: 생성된 비디오 파일 경로
        """
        pass


# core/interfaces/publisher.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

from domain.entities import Platform, PublishResult

class SocialPublisherInterface(ABC):
    """소셜 미디어 게시 인터페이스"""
    
    @abstractmethod
    def publish(
        self,
        platform: Platform,
        content: Dict[str, Any],
        credentials: Dict[str, str]
    ) -> PublishResult:
        """
        지정된 플랫폼에 콘텐츠를 게시합니다.
        
        Args:
            platform: 게시할 플랫폼
            content: 게시할 콘텐츠
            credentials: 인증 정보
            
        Returns:
            PublishResult: 게시 결과
        """
        pass

class NaverPublisherInterface(ABC):
    """네이버 블로그 게시 인터페이스"""
    
    @abstractmethod
    def publish_to_naver(
        self,
        title: str,
        content: str,
        image_paths: List[str]
    ) -> PublishResult:
        """
        네이버 블로그에 게시물을 발행합니다.
        
        Args:
            title: 게시물 제목
            content: 게시물 내용
            image_paths: 이미지 파일 경로 목록
            
        Returns:
            PublishResult: 게시 결과
        """
        pass

class InstagramPublisherInterface(ABC):
    """인스타그램 게시 인터페이스"""
    
    @abstractmethod
    def publish_to_instagram(
        self,
        caption: str,
        hashtags: List[str],
        image_paths: List[str]
    ) -> PublishResult:
        """
        인스타그램에 게시물을 발행합니다.
        
        Args:
            caption: 게시물 캡션
            hashtags: 해시태그 목록
            image_paths: 이미지 파일 경로 목록
            
        Returns:
            PublishResult: 게시 결과
        """
        pass

class YoutubePublisherInterface(ABC):
    """유튜브 게시 인터페이스"""
    
    @abstractmethod
    def publish_to_youtube(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: List[str]
    ) -> PublishResult:
        """
        유튜브에 비디오를 업로드합니다.
        
        Args:
            video_path: 비디오 파일 경로
            title: 비디오 제목
            description: 비디오 설명
            tags: 태그 목록
            
        Returns:
            PublishResult: 게시 결과
        """
        pass