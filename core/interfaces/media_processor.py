from typing import Dict, Any, List
from abc import ABC, abstractmethod

class MediaProcessorInterface(ABC):
    """미디어 처리 인터페이스"""
    
    @abstractmethod
    def apply_filter(self, image_path: str, filter_type: str = "enhance") -> str:
        """
        이미지에 필터를 적용합니다.
        
        Args:
            image_path: 이미지 파일 경로
            filter_type: 적용할 필터 유형 (enhance, blur, bw 등)
            
        Returns:
            str: 필터가 적용된 이미지 파일 경로
            
        Raises:
            MediaProcessingError: 이미지 처리 중 오류가 발생한 경우
        """
        pass
    
    @abstractmethod
    def create_shorts_video(
        self,
        image_paths: List[str],
        flower_data: Dict[str, Any],
        output_path: str,
        duration: int = 15
    ) -> str:
        """
        여러 이미지를 사용하여 쇼츠 비디오를 생성합니다.
        
        Args:
            image_paths: 이미지 파일 경로 목록
            flower_data: 꽃 분석 데이터
            output_path: 결과 비디오 파일 경로
            duration: 비디오 길이(초)
            
        Returns:
            str: 생성된 비디오 파일 경로
            
        Raises:
            MediaProcessingError: 비디오 생성 중 오류가 발생한 경우
        """
        pass