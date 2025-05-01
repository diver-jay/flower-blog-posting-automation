from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
from domain.entities import Platform, PublishResult

class SocialPublisherInterface(ABC):
    """소셜 미디어 게시 인터페이스"""
    
    @abstractmethod
    def publish(
        self,
        platform: Platform,
        content: Dict[str, Any],
        credentials: Dict[str, str] = None
    ) -> PublishResult:
        """
        지정된 플랫폼에 콘텐츠를 게시합니다.
        
        Args:
            platform: 게시할 플랫폼
            content: 게시할 콘텐츠
            credentials: 인증 정보 (선택 사항)
            
        Returns:
            PublishResult: 게시 결과
            
        Raises:
            PublishingError: 게시 중 오류가 발생한 경우
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
        네이버 블로그에 콘텐츠를 게시합니다.
        
        Args:
            title: 게시글 제목
            content: 게시글 내용 (HTML)
            image_paths: 이미지 파일 경로 목록
            
        Returns:
            PublishResult: 게시 결과
            
        Raises:
            PublishingError: 게시 중 오류가 발생한 경우
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
        인스타그램에 콘텐츠를 게시합니다.
        
        Args:
            caption: 게시물 캡션
            hashtags: 해시태그 목록
            image_paths: 이미지 파일 경로 목록
            
        Returns:
            PublishResult: 게시 결과
            
        Raises:
            PublishingError: 게시 중 오류가 발생한 경우
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
        유튜브에 비디오를 게시합니다.
        
        Args:
            video_path: 비디오 파일 경로
            title: 비디오 제목
            description: 비디오 설명
            tags: 태그 목록
            
        Returns:
            PublishResult: 게시 결과
            
        Raises:
            PublishingError: 게시 중 오류가 발생한 경우
        """
        pass