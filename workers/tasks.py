# workers/tasks.py - 백그라운드 작업

import os
import json
import logging
from typing import Dict, Any

from workers.celery_app import celery_app
from app.config import get_settings
from app.dependencies import (
    get_image_analyzer,
    get_content_generator,
    get_video_generator,
    get_social_publishers
)
from domain.entities import FlowerPost, Platform, PostStatus, PublishResult
from domain.exceptions import DomainException
from infrastructure.database.models import get_db, SessionLocal
from infrastructure.database.repositories import SQLAlchemyPostRepository
from infrastructure.ai.claude_service import ClaudeClient

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, max_retries=3)
def process_flower_content(self, post_id: str) -> Dict[str, Any]:
    """
    꽃 사진에 대한 모든 콘텐츠 생성 및 발행 작업을 처리합니다.
    
    Args:
        post_id: 포스트 ID
        
    Returns:
        Dict[str, Any]: 작업 처리 결과
    """
    # 설정 및 의존성 초기화
    settings = get_settings()
    db = SessionLocal()
    repository = SQLAlchemyPostRepository(db)
    
    # 서비스 초기화
    claude_client = ClaudeClient(api_key=settings.ANTHROPIC_API_KEY)
    image_analyzer = get_image_analyzer(claude_client)
    content_generator = get_content_generator(claude_client)
    video_generator = get_video_generator()
    social_publishers = get_social_publishers()
    
    try:
        # 포스트 데이터 조회
        post = repository.find_by_id(post_id)
        if not post:
            return {"success": False, "error": "Post not found"}
        
        # 상태 업데이트
        post.update_status(PostStatus.PROCESSING)
        repository.update(post)
        
        # 이미지 분석
        main_image = post.image_paths[0]  # 첫 번째 이미지를 주 분석 대상으로 사용
        flower_data = image_analyzer.analyze_flower_image(main_image)
        
        # 분석 데이터 저장
        post.flower_data = flower_data
        repository.update(post)
        
        results = {}
        
        # 플랫폼별 콘텐츠 생성 및 발행
        for platform in post.platforms:
            if platform == Platform.NAVER:
                # 네이버 블로그 콘텐츠 생성 및 발행
                logger.info(f"네이버 블로그 콘텐츠 생성 시작: {post_id}")
                blog_content = content_generator.generate_blog_post(flower_data, post.image_paths)
                post.blog_content = blog_content
                repository.update(post)
                
                # 네이버 블로그에 발행
                logger.info(f"네이버 블로그 발행 시작: {post_id}")
                title = post.title or f"{flower_data['flower_type']['korean']} - {flower_data['meaning']}"
                naver_result = social_publishers.publish(
                    platform=Platform.NAVER,
                    content={
                        "title": title,
                        "blog_content": blog_content,
                        "image_paths": post.image_paths
                    }
                )
                post.add_publish_result(naver_result)
                repository.update(post)
                results["naver"] = naver_result
            
            elif platform == Platform.INSTAGRAM:
                # 인스타그램 콘텐츠 생성
                logger.info(f"인스타그램 콘텐츠 생성 시작: {post_id}")
                caption = content_generator.generate_instagram_caption(flower_data)
                hashtags = content_generator.generate_tags(flower_data)
                post.instagram_caption = caption
                post.instagram_tags = hashtags
                repository.update(post)
                
                # 인스타그램에 발행
                logger.info(f"인스타그램 발행 시작: {post_id}")
                instagram_result = social_publishers.publish(
                    platform=Platform.INSTAGRAM,
                    content={
                        "instagram_caption": caption,
                        "instagram_tags": hashtags,
                        "image_paths": post.image_paths
                    }
                )
                post.add_publish_result(instagram_result)
                repository.update(post)
                results["instagram"] = instagram_result
            
            elif platform == Platform.YOUTUBE:
                # 쇼츠 비디오 생성
                logger.info(f"유튜브 쇼츠 비디오 생성 시작: {post_id}")
                video_path = f"uploads/{post_id}/shorts_video.mp4"
                video_generator.create_shorts_video(post.image_paths, flower_data, video_path)
                post.video_path = video_path
                repository.update(post)
                
                # 비디오 제목 및 설명 생성
                title = post.title or f"{flower_data['flower_type']['korean']} - {flower_data['flower_type']['english']}"
                description = f"{flower_data['flower_type']['korean']} ({flower_data['flower_type']['english']}) - {flower_data['meaning']}\n\n#꽃 #플라워 #쇼츠"
                tags = content_generator.generate_tags(flower_data)
                
                # 유튜브 쇼츠에 업로드
                logger.info(f"유튜브 쇼츠 업로드 시작: {post_id}")
                youtube_result = social_publishers.publish(
                    platform=Platform.YOUTUBE,
                    content={
                        "video_path": video_path,
                        "title": title,
                        "description": description,
                        "tags": tags
                    }
                )
                post.add_publish_result(youtube_result)
                repository.update(post)
                results["youtube"] = youtube_result
        
        # 결과 저장 및 상태 업데이트
        post.update_status(PostStatus.COMPLETED)
        repository.update(post)
        
        logger.info(f"콘텐츠 생성 및 발행 완료: {post_id}")
        return {"success": True, "post_id": post_id, "results": results}
    
    except DomainException as e:
        logger.error(f"도메인 예외 발생: {e.message}")
        post.update_status(PostStatus.FAILED, str(e))
        repository.update(post)
        return {"success": False, "error": str(e)}
    
    except Exception as e:
        logger.error(f"예기치 않은 오류 발생: {e}")
        post.update_status(PostStatus.FAILED, str(e))
        repository.update(post)
        return {"success": False, "error": str(e)}
    
    finally:
        db.close()