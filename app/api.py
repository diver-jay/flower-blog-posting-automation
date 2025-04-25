# app/api.py - FastAPI 애플리케이션 및 라우터

import os
import uuid
from typing import List, Optional
from fastapi import FastAPI, File, UploadFile, Form, Depends, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from datetime import datetime

from app.config import get_settings
from app.dependencies import get_post_repository, get_task_queue
from domain.entities import FlowerPost, Platform
from infrastructure.database.repositories import PostRepository
from workers.tasks import process_flower_content

def create_app() -> FastAPI:
    """FastAPI 애플리케이션을 생성하고 설정합니다."""
    settings = get_settings()
    
    app = FastAPI(
        title=settings.APP_NAME,
        description="꽃 이미지를 분석하고 자동으로 블로그 및 소셜 미디어 콘텐츠를 생성하는 API",
        version="1.0.0",
        debug=settings.DEBUG,
    )
    
    # CORS 설정
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 업로드 디렉토리 설정
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")
    
    # 라우터 등록
    register_routes(app)
    
    return app

def register_routes(app: FastAPI):
    """라우터를 등록합니다."""
    
    @app.post("/upload/", response_model=FlowerPost)
    async def upload_flower_images(
        background_tasks: BackgroundTasks,
        images: List[UploadFile] = File(...),
        title: Optional[str] = Form(None),
        description: Optional[str] = Form(None),
        platforms: List[str] = Form([]),
        schedule_time: Optional[datetime] = Form(None),
        repository: PostRepository = Depends(get_post_repository),
        task_queue = Depends(get_task_queue),
    ):
        """꽃 이미지를 업로드하고 콘텐츠 생성 작업을 시작합니다."""
        settings = get_settings()
        
        # 파일 크기 검증
        for img in images:
            if img.size > settings.MAX_UPLOAD_SIZE:
                raise HTTPException(
                    status_code=413,
                    detail=f"이미지 크기가 너무 큽니다. 최대 허용 크기: {settings.MAX_UPLOAD_SIZE} bytes"
                )
        
        # 고유 ID 생성
        post_id = str(uuid.uuid4())
        
        # 이미지 저장
        image_paths = []
        for img in images:
            file_path = f"{settings.UPLOAD_DIR}/{post_id}/{img.filename}"
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, "wb") as buffer:
                buffer.write(await img.read())
            image_paths.append(file_path)
        
        # 플랫폼 열거형으로 변환
        platform_enums = [Platform(p) for p in platforms if p in Platform.__members__]
        
        # 새 게시물 생성
        flower_post = FlowerPost(
            id=post_id,
            title=title,
            description=description,
            image_paths=image_paths,
            platforms=platform_enums,
            schedule_time=schedule_time or datetime.now(),
            status="pending"
        )
        
        # 저장소에 저장
        saved_post = repository.save(flower_post)
        
        # 백그라운드에서 콘텐츠 생성 및 게시 작업 시작
        background_tasks.add_task(
            task_queue.enqueue_task,
            process_flower_content,
            post_id
        )
        
        return saved_post

    @app.get("/posts/", response_model=List[FlowerPost])
    async def get_posts(
        repository: PostRepository = Depends(get_post_repository),
    ):
        """모든 포스트를 조회합니다."""
        return repository.find_all()

    @app.get("/posts/{post_id}", response_model=FlowerPost)
    async def get_post(
        post_id: str,
        repository: PostRepository = Depends(get_post_repository),
    ):
        """ID로 특정 포스트를 조회합니다."""
        post = repository.find_by_id(post_id)
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        return post