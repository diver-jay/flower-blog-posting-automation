# core/services/content_generator.py - 콘텐츠 생성 서비스

from typing import Dict, Any, List
import logging

from core.interfaces.content_generator import ContentGeneratorInterface
from infrastructure.ai.claude_service import ClaudeClient
from domain.exceptions import ContentGenerationError

logger = logging.getLogger(__name__)

class ClaudeContentGenerator(ContentGeneratorInterface):
    """Claude API를 사용하여 꽃 관련 콘텐츠를 생성하는 서비스"""
    
    def __init__(self, claude_client: ClaudeClient):
        """
        초기화
        
        Args:
            claude_client: Claude API 클라이언트
        """
        self.claude_client = claude_client
    
    def generate_blog_post(self, flower_data: Dict[str, Any], image_paths: List[str]) -> str:
        """
        꽃 데이터를 기반으로 네이버 블로그용 포스트를 생성합니다.
        
        Args:
            flower_data: 꽃 분석 데이터
            image_paths: 이미지 파일 경로 목록
            
        Returns:
            str: 생성된 블로그 포스트 HTML 콘텐츠
            
        Raises:
            ContentGenerationError: 콘텐츠 생성 중 오류가 발생한 경우
        """
        try:
            # 블로그 포스트 생성 프롬프트
            prompt = f"""
            다음 꽃 정보를 바탕으로 네이버 블로그에 게시할 내용을 작성해주세요:
            
            꽃 종류: {flower_data['flower_type']['korean']} ({flower_data['flower_type']['english']})
            학명: {flower_data['flower_type']['scientific']}
            색상: {', '.join(flower_data['colors'])}
            계절적 특성: {flower_data['seasonal']}
            꽃말: {flower_data['meaning']}
            관리 팁: {flower_data['care_tips']}
            장식/인테리어 제안: {flower_data['decoration_ideas']}
            선물 상황: {', '.join(flower_data['gift_occasions'])}
            
            블로그 포스트는 다음 구조로 작성해주세요:
            1. 매력적인 제목
            2. 꽃 소개 (특징, 역사적 배경 포함)
            3. 꽃말과 상징성
            4. 계절적 특성 및 최적의 감상 시기
            5. 관리 방법 및 팁
            6. 인테리어/장식 활용법
            7. 선물하기 좋은 상황
            8. 마무리 문구
            
            네이버 블로그에 적합한 HTML 태그를 포함해주세요. 또한 SEO에 유리한 키워드를 자연스럽게 포함시켜주세요.
            """
            
            # Claude API로 블로그 포스트 생성 요청
            blog_content = self.claude_client.generate_text(prompt, max_tokens=4000, model="claude-3-sonnet-20240229")
            
            logger.info(f"블로그 포스트 생성 완료: {len(blog_content)} 자")
            return blog_content
            
        except Exception as e:
            logger.error(f"블로그 포스트 생성 중 오류 발생: {e}")
            raise ContentGenerationError(f"블로그 포스트 생성 중 오류가 발생했습니다: {str(e)}")
    
    def generate_instagram_caption(self, flower_data: Dict[str, Any]) -> str:
        """
        꽃 데이터를 기반으로 인스타그램 캡션을 생성합니다.
        
        Args:
            flower_data: 꽃 분석 데이터
            
        Returns:
            str: 생성된 인스타그램 캡션
            
        Raises:
            ContentGenerationError: 콘텐츠 생성 중 오류가 발생한 경우
        """
        try:
            # 인스타그램 캡션 생성 프롬프트
            prompt = f"""
            다음 꽃 정보를 바탕으로 인스타그램 게시물에 사용할 짧고 매력적인 캡션을 작성해주세요:
            
            꽃 종류: {flower_data['flower_type']['korean']} ({flower_data['flower_type']['english']})
            색상: {', '.join(flower_data['colors'])}
            계절적 특성: {flower_data['seasonal']}
            꽃말: {flower_data['meaning']}
            
            캡션은 다음 요소를 포함해야 합니다:
            1. 감성적이고 눈길을 끄는 짧은 문구
            2. 꽃에 대한 간결한 설명
            3. 계절감이나 감정을 표현하는 문장
            4. 이모지 2~3개 적절히 사용
            5. 호출성 문구(CTA) - 예: "오늘 하루도 행복한 하루 되세요" 등
            
            전체 길이는 300자 내외로 작성해주세요.
            """
            
            # Claude API로 인스타그램 캡션 생성 요청
            caption = self.claude_client.generate_text(prompt, max_tokens=1000, model="claude-3-haiku-20240307")
            
            logger.info(f"인스타그램 캡션 생성 완료: {len(caption)} 자")
            return caption
            
        except Exception as e:
            logger.error(f"인스타그램 캡션 생성 중 오류 발생: {e}")
            raise ContentGenerationError(f"인스타그램 캡션 생성 중 오류가 발생했습니다: {str(e)}")
    
    def generate_tags(self, flower_data: Dict[str, Any]) -> List[str]:
        """
        꽃 데이터를 기반으로 해시태그를 생성합니다.
        
        Args:
            flower_data: 꽃 분석 데이터
            
        Returns:
            List[str]: 생성된 해시태그 목록
            
        Raises:
            ContentGenerationError: 콘텐츠 생성 중 오류가 발생한 경우
        """
        try:
            # 해시태그 생성 프롬프트
            prompt = f"""
            다음 꽃 정보를 바탕으로 인스타그램에 사용할 해시태그 목록을 생성해주세요:
            
            꽃 종류: {flower_data['flower_type']['korean']} ({flower_data['flower_type']['english']})
            색상: {', '.join(flower_data['colors'])}
            계절적 특성: {flower_data['seasonal']}
            꽃말: {flower_data['meaning']}
            선물 상황: {', '.join(flower_data['gift_occasions'])}
            
            다음 카테고리의 해시태그를 포함해주세요:
            1. 꽃 이름 관련 (한글, 영문)
            2. 색상 관련
            3. 계절/시기 관련
            4. 감성/분위기 관련
            5. 인테리어/장식 관련
            6. 선물/이벤트 관련
            7. 인기 있는 일반 꽃 해시태그
            
            총 15-20개의 해시태그를 리스트 형태로 반환해주세요. 한글과 영어 해시태그를 모두 포함해주세요.
            """
            
            # Claude API로 해시태그 생성 요청
            tags_text = self.claude_client.generate_text(prompt, max_tokens=1000, model="claude-3-haiku-20240307")
            
            # 해시태그 목록 추출 및 가공
            hashtags = [tag.strip() for tag in tags_text.split('\n') if tag.strip().startswith('#')]
            
            # 충분한 해시태그가 없으면 기본 태그 추가
            if len(hashtags) < 10:
                hashtags.extend([
                    "#꽃스타그램", "#플라워샵", "#꽃선물", "#꽃집", "#꽃배달",
                    "#flowerstagram", "#flowerpower", "#flowerlovers", "#flowermagic", "#floweroftheday"
                ])
            
            logger.info(f"해시태그 생성 완료: {len(hashtags)} 개")
            return hashtags[:20]  # 최대 20개로 제한
            
        except Exception as e:
            logger.error(f"해시태그 생성 중 오류 발생: {e}")
            raise ContentGenerationError(f"해시태그 생성 중 오류가 발생했습니다: {str(e)}")