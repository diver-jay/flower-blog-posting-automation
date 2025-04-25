# core/services/social_publisher.py - 소셜 미디어 게시 서비스

import logging
from typing import Dict, Any, List, Optional

from core.interfaces.publisher import (
    SocialPublisherInterface,
    NaverPublisherInterface,
    InstagramPublisherInterface,
    YoutubePublisherInterface
)
from domain.entities import Platform, PublishResult
from domain.exceptions import PublishingError

logger = logging.getLogger(__name__)

class SocialPublisherService(SocialPublisherInterface):
    """소셜 미디어 게시 서비스"""
    
    def __init__(
        self,
        naver_publisher: NaverPublisherInterface,
        instagram_publisher: InstagramPublisherInterface,
        youtube_publisher: YoutubePublisherInterface
    ):
        """
        초기화
        
        Args:
            naver_publisher: 네이버 블로그 게시 인터페이스
            instagram_publisher: 인스타그램 게시 인터페이스
            youtube_publisher: 유튜브 게시 인터페이스
        """
        self.publishers = {
            Platform.NAVER: naver_publisher,
            Platform.INSTAGRAM: instagram_publisher,
            Platform.YOUTUBE: youtube_publisher
        }
    
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
        try:
            publisher = self.publishers.get(platform)
            if not publisher:
                raise PublishingError(f"지원되지 않는 플랫폼입니다: {platform.value}")
            
            # 플랫폼별 게시 로직
            if platform == Platform.NAVER:
                # 네이버 블로그 게시
                result = publisher.publish_to_naver(
                    title=content.get("title", ""),
                    content=content.get("blog_content", ""),
                    image_paths=content.get("image_paths", [])
                )
            
            elif platform == Platform.INSTAGRAM:
                # 인스타그램 게시
                result = publisher.publish_to_instagram(
                    caption=content.get("instagram_caption", ""),
                    hashtags=content.get("instagram_tags", []),
                    image_paths=content.get("image_paths", [])
                )
            
            elif platform == Platform.YOUTUBE:
                # 유튜브 게시
                result = publisher.publish_to_youtube(
                    video_path=content.get("video_path", ""),
                    title=content.get("title", ""),
                    description=content.get("description", ""),
                    tags=content.get("tags", [])
                )
            
            logger.info(f"{platform.value} 플랫폼 게시 완료: {result.success}")
            return result
        
        except Exception as e:
            logger.error(f"{platform.value} 플랫폼 게시 중 오류 발생: {e}")
            return PublishResult(
                success=False,
                platform=platform,
                error=str(e)
            )