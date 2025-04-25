# infrastructure/ai/claude_service.py - Claude API 서비스

import os
import json
import base64
import logging
from typing import Dict, Any, List, Optional

import anthropic

from domain.exceptions import ImageAnalysisError, ContentGenerationError

logger = logging.getLogger(__name__)

class ClaudeClient:
    """Claude API 클라이언트"""
    
    def __init__(self, api_key: str):
        """
        초기화
        
        Args:
            api_key: Claude API 키
        """
        self.client = anthropic.Anthropic(api_key=api_key)
    
    def analyze_image(self, image_path: str, prompt: str) -> Dict[str, Any]:
        """
        이미지를 분석합니다.
        
        Args:
            image_path: 이미지 파일 경로
            prompt: 분석 프롬프트
            
        Returns:
            Dict[str, Any]: 분석 결과
            
        Raises:
            ImageAnalysisError: 이미지 분석 중 오류가 발생한 경우
        """
        try:
            # 이미지 파일 로드
            with open(image_path, "rb") as img_file:
                img_bytes = img_file.read()
            
            # 이미지 MIME 타입 결정
            mime_type = "image/jpeg"
            if image_path.lower().endswith(".png"):
                mime_type = "image/png"
            elif image_path.lower().endswith(".webp"):
                mime_type = "image/webp"
            
            # Claude API 호출
            message = self.client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=1000,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": mime_type,
                                    "data": base64.b64encode(img_bytes).decode("utf-8")
                                }
                            }
                        ]
                    }
                ]
            )
            
            # 응답에서 JSON 추출
            response_text = message.content[0].text
            
            # JSON 부분만 추출
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start == -1 or json_end <= json_start:
                raise ImageAnalysisError("응답에서 JSON을 찾을 수 없습니다", None)
            
            json_str = response_text[json_start:json_end]
            flower_data = json.loads(json_str)
            
            return flower_data
            
        except anthropic.APIError as e:
            logger.error(f"Claude API 호출 중 오류 발생: {e}")
            raise ImageAnalysisError(f"Claude API 오류: {str(e)}", None)
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 중 오류 발생: {e}")
            raise ImageAnalysisError(f"JSON 파싱 오류: {str(e)}", None)
            
        except Exception as e:
            logger.error(f"이미지 분석 중 예기치 않은 오류 발생: {e}")
            raise ImageAnalysisError(f"이미지 분석 오류: {str(e)}", None)
    
    def generate_text(self, prompt: str, max_tokens: int = 1000, model: str = "claude-3-opus-20240229") -> str:
        """
        텍스트를 생성합니다.
        
        Args:
            prompt: 생성 프롬프트
            max_tokens: 최대 토큰 수
            model: 사용할 모델
            
        Returns:
            str: 생성된 텍스트
            
        Raises:
            ContentGenerationError: 텍스트 생성 중 오류가 발생한 경우
        """
        try:
            # Claude API 호출
            response = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # 응답 텍스트 반환
            return response.content[0].text
            
        except anthropic.APIError as e:
            logger.error(f"Claude API 호출 중 오류 발생: {e}")
            raise ContentGenerationError(f"Claude API 오류: {str(e)}")
            
        except Exception as e:
            logger.error(f"텍스트 생성 중 예기치 않은 오류 발생: {e}")
            raise ContentGenerationError(f"텍스트 생성 오류: {str(e)}")