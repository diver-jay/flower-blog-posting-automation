# domain/exceptions.py - 도메인 예외

from typing import Dict, Any, Optional

class DomainException(Exception):
    """도메인 계층 기본 예외"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class ImageAnalysisError(DomainException):
    """이미지 분석 중 발생한 예외"""
    def __init__(self, message: str, default_data: Optional[Dict[str, Any]] = None):
        self.default_data = default_data
        super().__init__(message)

class ContentGenerationError(DomainException):
    """콘텐츠 생성 중 발생한 예외"""
    pass

class MediaProcessingError(DomainException):
    """미디어 처리 중 발생한 예외"""
    pass

class PublishingError(DomainException):
    """소셜 미디어 게시 중 발생한 예외"""
    pass

class RepositoryError(DomainException):
    """데이터 저장소 작업 중 발생한 예외"""
    pass

class TaskQueueError(DomainException):
    """작업 큐 작업 중 발생한 예외"""
    pass