#!/usr/bin/env python3
# main.py - 애플리케이션 시작점

import os
import uvicorn
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

from app.api import create_app
from infrastructure.database.models import create_tables

def main():
    """애플리케이션 시작점"""
    # 데이터베이스 테이블 생성
    create_tables()
    
    # FastAPI 애플리케이션 생성
    app = create_app()
    
    # 서버 실행
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    # uvicorn.run(app, host=host, port=port, reload=True)
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    main()