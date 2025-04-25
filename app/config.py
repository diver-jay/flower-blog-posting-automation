# app/config.py - 애플리케이션 설정

import os
from pydantic import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """애플리케이션 설정 클래스"""
    # 애플리케이션 설정
    APP_NAME: str = "꽃집 콘텐츠 자동화 시스템"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
    
    # 데이터베이스 설정
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./flower_automation.db")
    
    # API 키 및 인증 정보
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    
    # 네이버 블로그 설정
    NAVER_USERNAME: str = os.getenv("NAVER_USERNAME", "")
    NAVER_PASSWORD: str = os.getenv("NAVER_PASSWORD", "")
    
    # 인스타그램 설정
    INSTAGRAM_ACCESS_TOKEN: str = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
    INSTAGRAM_ACCOUNT_ID: str = os.getenv("INSTAGRAM_ACCOUNT_ID", "")
    
    # 유튜브 설정
    YOUTUBE_CREDENTIALS: str = os.getenv("YOUTUBE_CREDENTIALS", "")
    
    # 작업 큐 설정
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
    
    # 파일 업로드 설정
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    MAX_UPLOAD_SIZE: int = int(os.getenv("MAX_UPLOAD_SIZE", "10485760"))  # 10MB

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """설정 인스턴스를 반환합니다. (싱글톤 패턴)"""
    return Settings()