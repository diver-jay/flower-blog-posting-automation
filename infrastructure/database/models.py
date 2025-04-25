# infrastructure/database/models.py - 데이터베이스 모델

import os
import json
from sqlalchemy import Column, String, DateTime, JSON, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from typing import Generator

from app.config import get_settings

# 데이터베이스 설정
settings = get_settings()
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class FlowerPostModel(Base):
    """꽃 포스트 데이터베이스 모델"""
    __tablename__ = "flower_posts"
    
    id = Column(String, primary_key=True)
    title = Column(String, nullable=True)
    description = Column(String, nullable=True)
    image_paths = Column(JSON, nullable=False)
    platforms = Column(JSON, nullable=False)
    schedule_time = Column(DateTime, default=datetime.now)
    status = Column(String, default="pending")
    error_message = Column(String, nullable=True)
    
    # 이미지 분석 결과
    flower_data = Column(JSON, nullable=True)
    
    # 생성된 콘텐츠
    blog_content = Column(String, nullable=True)
    instagram_caption = Column(String, nullable=True)
    instagram_tags = Column(JSON, nullable=True)
    video_path = Column(String, nullable=True)
    
    # 발행 결과
    publish_results = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

def create_tables():
    """데이터베이스 테이블을 생성합니다."""
    Base.metadata.create_all(bind=engine)

def get_db() -> Generator[Session, None, None]:
    """데이터베이스 세션을 반환합니다."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()