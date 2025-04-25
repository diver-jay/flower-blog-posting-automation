# workers/celery_app.py - Celery 작업 큐

import os
import logging
from celery import Celery
from typing import Any, Callable, Dict

from domain.exceptions import TaskQueueError

logger = logging.getLogger(__name__)

class CeleryTaskQueue:
    """Celery를 사용한 작업 큐"""
    
    def __init__(self, broker_url: str, result_backend: str):
        """
        초기화
        
        Args:
            broker_url: Celery 브로커 URL (예: Redis 연결 문자열)
            result_backend: Celery 결과 백엔드 URL
        """
        self.app = Celery(
            'flower_tasks',
            broker=broker_url,
            backend=result_backend
        )
        
        # Celery 설정
        self.app.conf.update(
            task_serializer='json',
            accept_content=['json'],
            result_serializer='json',
            timezone='Asia/Seoul',
            enable_utc=True,
        )
    
    def enqueue_task(self, task_func: Callable, *args: Any, **kwargs: Any) -> str:
        """
        작업을 큐에 추가합니다.
        
        Args:
            task_func: 작업 함수
            *args: 작업 함수 인수
            **kwargs: 작업 함수 키워드 인수
            
        Returns:
            str: 작업 ID
            
        Raises:
            TaskQueueError: 작업 큐잉 중 오류가 발생한 경우
        """
        try:
            # Celery 작업 실행
            task_name = f"{task_func.__module__}.{task_func.__name__}"
            task = self.app.task(task_func)
            result = task.apply_async(args=args, kwargs=kwargs)
            
            logger.info(f"작업 큐에 추가됨: {task_name}, 작업 ID: {result.id}")
            return result.id
        
        except Exception as e:
            logger.error(f"작업 큐잉 중 오류 발생: {e}")
            raise TaskQueueError(f"작업 큐잉 실패: {str(e)}")
    
    def get_task_result(self, task_id: str) -> Dict[str, Any]:
        """
        작업 결과를 조회합니다.
        
        Args:
            task_id: 작업 ID
            
        Returns:
            Dict[str, Any]: 작업 결과
            
        Raises:
            TaskQueueError: 작업 결과 조회 중 오류가 발생한 경우
        """
        try:
            # Celery 작업 결과 조회
            async_result = self.app.AsyncResult(task_id)
            
            # 상태 확인
            if async_result.ready():
                if async_result.successful():
                    return {
                        "status": "completed",
                        "result": async_result.get()
                    }
                else:
                    return {
                        "status": "failed",
                        "error": str(async_result.result)
                    }
            else:
                return {
                    "status": "pending",
                    "info": async_result.info
                }
        
        except Exception as e:
            logger.error(f"작업 결과 조회 중 오류 발생: {e}")
            raise TaskQueueError(f"작업 결과 조회 실패: {str(e)}")

# Celery 인스턴스 초기화를 위한 함수 (워커 프로세스에서 사용)
def create_celery_app():
    """Celery 애플리케이션을 생성합니다."""
    broker_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
    result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
    
    app = Celery(
        'flower_tasks',
        broker=broker_url,
        backend=result_backend
    )
    
    # Celery 설정
    app.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='Asia/Seoul',
        enable_utc=True,
    )
    
    return app

# Celery 워커에서 사용할 애플리케이션 인스턴스
celery_app = create_celery_app()