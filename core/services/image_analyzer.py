# core/services/image_analyzer.py - 이미지 분석 서비스

from typing import Dict, Any
import logging

from core.interfaces.analyzer import ImageAnalyzerInterface
from infrastructure.ai.claude_service import ClaudeClient
from domain.exceptions import ImageAnalysisError

logger = logging.getLogger(__name__)

class ClaudeImageAnalyzer(ImageAnalyzerInterface):
    """Claude API를 사용하여 꽃 이미지를 분석하는 서비스"""
    
    def __init__(self, claude_client: ClaudeClient):
        """
        초기화
        
        Args:
            claude_client: Claude API 클라이언트
        """
        self.claude_client = claude_client
    
    def analyze_flower_image(self, image_path: str) -> Dict[str, Any]:
        """
        Claude를 사용하여 꽃 이미지를 분석하고 관련 정보를 반환합니다.
        
        Args:
            image_path: 이미지 파일 경로
            
        Returns:
            Dict[str, Any]: 분석된 꽃 정보
            
        Raises:
            ImageAnalysisError: 이미지 분석 중 오류가 발생한 경우
        """
        try:
            # 꽃 이미지 분석 프롬프트
            prompt = """이 꽃 이미지를 분석해주세요. 다음 정보를 JSON 형식으로 반환해주세요:
1. 꽃의 종류(한국어, 영어, 학명)
2. 꽃의 주요 색상
3. 꽃의 계절적 특성
4. 꽃말
5. 관리 팁
6. 장식/인테리어 제안
7. 적합한 선물 상황
온전히 JSON 형식으로만 응답해주세요."""
            
            # Claude API로 이미지 분석 요청
            flower_data = self.claude_client.analyze_image(image_path, prompt)
            
            logger.info(f"꽃 이미지 분석 완료: {flower_data.get('flower_type', {}).get('korean', '알 수 없음')}")
            return flower_data
            
        except Exception as e:
            logger.error(f"이미지 분석 중 오류 발생: {e}")
            # 기본 값 반환
            default_data = {
                "flower_type": {"korean": "알 수 없음", "english": "Unknown", "scientific": ""},
                "colors": ["알 수 없음"],
                "seasonal": "알 수 없음",
                "meaning": "알 수 없음",
                "care_tips": "알 수 없음",
                "decoration_ideas": "알 수 없음",
                "gift_occasions": ["알 수 없음"]
            }
            
            raise ImageAnalysisError(f"이미지 분석 중 오류가 발생했습니다: {str(e)}", default_data)