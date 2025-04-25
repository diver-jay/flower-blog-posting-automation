# app/dependencies.py - 의존성 주입

from typing import Generator
from fastapi import Depends

from app.config import get_settings
from core.interfaces.analyzer import ImageAnalyzerInterface
from core.interfaces.content_generator import ContentGeneratorInterface
from core.interfaces.media_processor import MediaProcessorInterface
from core.interfaces.publisher import SocialPublisherInterface

from core.services.image_analyzer import ClaudeImageAnalyzer
from core.services.content_generator import ClaudeContentGenerator
from core.services.video_generator import MoviepyVideoGenerator
from core.services.social_publisher import SocialPublisherService

from infrastructure.ai.claude_service import ClaudeClient
from infrastructure.database.repositories import PostRepository, SQLAlchemyPostRepository
from infrastructure.database.models import get_db
from infrastructure.external.naver_service import NaverBlogPublisher
from infrastructure.external.instagram_service import InstagramPublisher
from infrastructure.external.youtube_service import YoutubePublisher

from workers.celery_app import CeleryTaskQueue

# AI 서비스 의존성
def get_claude_client() -> ClaudeClient:
    """Claude API 클라이언트를 반환합니다."""
    settings = get_settings()
    return ClaudeClient(api_key=settings.ANTHROPIC_API_KEY)

# 도메인 서비스 의존성
def get_image_analyzer(
    claude_client: ClaudeClient = Depends(get_claude_client)
) -> ImageAnalyzerInterface:
    """이미지 분석 서비스를 반환합니다."""
    return ClaudeImageAnalyzer(claude_client=claude_client)

def get_content_generator(
    claude_client: ClaudeClient = Depends(get_claude_client)
) -> ContentGeneratorInterface:
    """콘텐츠 생성 서비스를 반환합니다."""
    return ClaudeContentGenerator(claude_client=claude_client)

def get_video_generator() -> MediaProcessorInterface:
    """비디오 생성 서비스를 반환합니다."""
    return MoviepyVideoGenerator()

def get_social_publishers() -> SocialPublisherInterface:
    """소셜 미디어 게시 서비스를 반환합니다."""
    settings = get_settings()
    
    naver_publisher = NaverBlogPublisher(
        username=settings.NAVER_USERNAME,
        password=settings.NAVER_PASSWORD
    )
    
    instagram_publisher = InstagramPublisher(
        access_token=settings.INSTAGRAM_ACCESS_TOKEN,
        account_id=settings.INSTAGRAM_ACCOUNT_ID
    )
    
    youtube_publisher = YoutubePublisher(
        credentials_path=settings.YOUTUBE_CREDENTIALS
    )
    
    return SocialPublisherService(
        naver_publisher=naver_publisher,
        instagram_publisher=instagram_publisher,
        youtube_publisher=youtube_publisher
    )

# 리포지토리 의존성
def get_post_repository(
    db = Depends(get_db)
) -> PostRepository:
    """포스트 리포지토리를 반환합니다."""
    return SQLAlchemyPostRepository(db)

# 작업 큐 의존성
def get_task_queue() -> CeleryTaskQueue:
    """Celery 작업 큐를 반환합니다."""
    settings = get_settings()
    return CeleryTaskQueue(
        broker_url=settings.CELERY_BROKER_URL,
        result_backend=settings.CELERY_RESULT_BACKEND
    )