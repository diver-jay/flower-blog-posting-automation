# infrastructure/database/repositories.py - 리포지토리 구현

import json
from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod
from sqlalchemy.orm import Session

from domain.entities import FlowerPost, Platform, FlowerData, PublishResult
from infrastructure.database.models import FlowerPostModel
from domain.exceptions import RepositoryError

class PostRepository(ABC):
    """포스트 리포지토리 인터페이스"""
    
    @abstractmethod
    def find_by_id(self, post_id: str) -> Optional[FlowerPost]:
        """ID로 포스트를 조회합니다."""
        pass
    
    @abstractmethod
    def find_all(self) -> List[FlowerPost]:
        """모든 포스트를 조회합니다."""
        pass
    
    @abstractmethod
    def save(self, post: FlowerPost) -> FlowerPost:
        """포스트를 저장합니다."""
        pass
    
    @abstractmethod
    def update(self, post: FlowerPost) -> FlowerPost:
        """포스트를 업데이트합니다."""
        pass
    
    @abstractmethod
    def delete(self, post_id: str) -> bool:
        """포스트를 삭제합니다."""
        pass

class SQLAlchemyPostRepository(PostRepository):
    """SQLAlchemy를 사용한 포스트 리포지토리 구현"""
    
    def __init__(self, db: Session):
        """
        초기화
        
        Args:
            db: 데이터베이스 세션
        """
        self.db = db
    
    def find_by_id(self, post_id: str) -> Optional[FlowerPost]:
        """
        ID로 포스트를 조회합니다.
        
        Args:
            post_id: 포스트 ID
            
        Returns:
            Optional[FlowerPost]: 조회된 포스트 또는 None
            
        Raises:
            RepositoryError: 데이터베이스 조회 중 오류가 발생한 경우
        """
        try:
            db_post = self.db.query(FlowerPostModel).filter(FlowerPostModel.id == post_id).first()
            if db_post is None:
                return None
            
            return self._map_to_entity(db_post)
        
        except Exception as e:
            raise RepositoryError(f"포스트 조회 중 오류가 발생했습니다: {str(e)}")
    
    def find_all(self) -> List[FlowerPost]:
        """
        모든 포스트를 조회합니다.
        
        Returns:
            List[FlowerPost]: 조회된 포스트 목록
            
        Raises:
            RepositoryError: 데이터베이스 조회 중 오류가 발생한 경우
        """
        try:
            db_posts = self.db.query(FlowerPostModel).order_by(FlowerPostModel.created_at.desc()).all()
            return [self._map_to_entity(db_post) for db_post in db_posts]
        
        except Exception as e:
            raise RepositoryError(f"포스트 목록 조회 중 오류가 발생했습니다: {str(e)}")
    
    def save(self, post: FlowerPost) -> FlowerPost:
        """
        포스트를 저장합니다.
        
        Args:
            post: 저장할 포스트
            
        Returns:
            FlowerPost: 저장된 포스트
            
        Raises:
            RepositoryError: 데이터베이스 저장 중 오류가 발생한 경우
        """
        try:
            db_post = self._map_to_model(post)
            self.db.add(db_post)
            self.db.commit()
            self.db.refresh(db_post)
            return self._map_to_entity(db_post)
        
        except Exception as e:
            self.db.rollback()
            raise RepositoryError(f"포스트 저장 중 오류가 발생했습니다: {str(e)}")
    
    def update(self, post: FlowerPost) -> FlowerPost:
        """
        포스트를 업데이트합니다.
        
        Args:
            post: 업데이트할 포스트
            
        Returns:
            FlowerPost: 업데이트된 포스트
            
        Raises:
            RepositoryError: 데이터베이스 업데이트 중 오류가 발생한 경우
        """
        try:
            # 기존 포스트 조회
            db_post = self.db.query(FlowerPostModel).filter(FlowerPostModel.id == post.id).first()
            if db_post is None:
                raise RepositoryError(f"업데이트할 포스트를 찾을 수 없습니다: {post.id}")
            
            # 모델 업데이트
            updated_post = self._map_to_model(post)
            for key, value in vars(updated_post).items():
                if key != "_sa_instance_state":
                    setattr(db_post, key, value)
            
            self.db.commit()
            self.db.refresh(db_post)
            return self._map_to_entity(db_post)
        
        except Exception as e:
            self.db.rollback()
            raise RepositoryError(f"포스트 업데이트 중 오류가 발생했습니다: {str(e)}")
    
    def delete(self, post_id: str) -> bool:
        """
        포스트를 삭제합니다.
        
        Args:
            post_id: 삭제할 포스트 ID
            
        Returns:
            bool: 삭제 성공 여부
            
        Raises:
            RepositoryError: 데이터베이스 삭제 중 오류가 발생한 경우
        """
        try:
            db_post = self.db.query(FlowerPostModel).filter(FlowerPostModel.id == post_id).first()
            if db_post is None:
                return False
            
            self.db.delete(db_post)
            self.db.commit()
            return True
        
        except Exception as e:
            self.db.rollback()
            raise RepositoryError(f"포스트 삭제 중 오류가 발생했습니다: {str(e)}")
    
    def _map_to_entity(self, db_post: FlowerPostModel) -> FlowerPost:
        """
        데이터베이스 모델을 도메인 엔티티로 변환합니다.
        
        Args:
            db_post: 데이터베이스 모델
            
        Returns:
            FlowerPost: 도메인 엔티티
        """
        # 플랫폼 문자열을 열거형으로 변환
        platforms = []
        for p in db_post.platforms:
            platforms.append(Platform(p))
        
        # 꽃 데이터 변환
        flower_data = None
        if db_post.flower_data:
            flower_data = FlowerData.from_dict(db_post.flower_data)
        
        # 게시 결과 변환
        publish_results = []
        if db_post.publish_results:
            for result in db_post.publish_results:
                publish_results.append(PublishResult(
                    success=result.get("success", False),
                    platform=Platform(result.get("platform", "naver")),
                    url=result.get("url"),
                    post_id=result.get("post_id"),
                    error=result.get("error")
                ))
        
        return FlowerPost(
            id=db_post.id,
            title=db_post.title,
            description=db_post.description,
            image_paths=db_post.image_paths,
            platforms=platforms,
            schedule_time=db_post.schedule_time,
            status=db_post.status,
            error_message=db_post.error_message,
            flower_data=flower_data,
            blog_content=db_post.blog_content,
            instagram_caption=db_post.instagram_caption,
            instagram_tags=db_post.instagram_tags,
            video_path=db_post.video_path,
            publish_results=publish_results,
            created_at=db_post.created_at,
            updated_at=db_post.updated_at
        )
    
    def _map_to_model(self, post: FlowerPost) -> FlowerPostModel:
        """
        도메인 엔티티를 데이터베이스 모델로 변환합니다.
        
        Args:
            post: 도메인 엔티티
            
        Returns:
            FlowerPostModel: 데이터베이스 모델
        """
        # 플랫폼 열거형을 문자열로 변환
        platforms = [p.value for p in post.platforms]
        
        # 꽃 데이터 변환
        flower_data = None
        if post.flower_data:
            if isinstance(post.flower_data, FlowerData):
                flower_data = post.flower_data.to_dict()
            else:
                flower_data = post.flower_data
        
        # 게시 결과 변환
        publish_results = None
        if post.publish_results:
            publish_results = []
            for result in post.publish_results:
                publish_results.append({
                    "success": result.success,
                    "platform": result.platform.value,
                    "url": result.url,
                    "post_id": result.post_id,
                    "error": result.error
                })
        
        return FlowerPostModel(
            id=post.id,
            title=post.title,
            description=post.description,
            image_paths=post.image_paths,
            platforms=platforms,
            schedule_time=post.schedule_time,
            status=post.status,
            error_message=post.error_message,
            flower_data=flower_data,
            blog_content=post.blog_content,
            instagram_caption=post.instagram_caption,
            instagram_tags=post.instagram_tags,
            video_path=post.video_path,
            publish_results=publish_results,
            created_at=post.created_at,
            updated_at=post.updated_at
        )