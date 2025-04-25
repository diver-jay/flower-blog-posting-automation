# infrastructure/external/instagram_service.py - 인스타그램 서비스

import os
import requests
import logging
from typing import List, Dict, Any, Optional

from core.interfaces.publisher import InstagramPublisherInterface
from domain.entities import PublishResult, Platform
from domain.exceptions import PublishingError

logger = logging.getLogger(__name__)

class InstagramPublisher(InstagramPublisherInterface):
    """인스타그램 게시 서비스 (Facebook Graph API 사용)"""
    
    def __init__(self, access_token: str, account_id: str):
        """
        초기화
        
        Args:
            access_token: Instagram Graph API 액세스 토큰
            account_id: Instagram 비즈니스 계정 ID
        """
        self.access_token = access_token
        self.account_id = account_id
        self.api_version = "v13.0"
        self.base_url = f"https://graph.facebook.com/{self.api_version}"
    
    def publish_to_instagram(
        self,
        caption: str,
        hashtags: List[str],
        image_paths: List[str]
    ) -> PublishResult:
        """
        인스타그램에 게시물을 발행합니다.
        
        Args:
            caption: 게시물 캡션
            hashtags: 해시태그 목록
            image_paths: 이미지 파일 경로 목록
            
        Returns:
            PublishResult: 게시 결과
            
        Raises:
            PublishingError: 게시 중 오류가 발생한 경우
        """
        try:
            # 필수 필드 검증
            if not self.access_token or not self.account_id:
                raise PublishingError("Instagram API 계정 정보가 설정되지 않았습니다.")
            
            if not caption:
                raise PublishingError("게시물 캡션은 필수입니다.")
            
            if not image_paths:
                raise PublishingError("게시물 이미지는 최소 1개 이상 필요합니다.")
            
            # 이미지 파일 존재 확인
            for img_path in image_paths:
                if not os.path.exists(img_path):
                    raise PublishingError(f"이미지 파일을 찾을 수 없습니다: {img_path}")
            
            # 해시태그 포맷팅
            full_caption = caption
            if hashtags:
                full_caption += "\n\n" + " ".join(hashtags)
            
            # 이미지를 Facebook 서버에 업로드
            image_media_ids = []
            
            for img_path in image_paths:
                # 이미지 업로드에 필요한 URL 획득
                upload_url = self._get_upload_url(img_path)
                if not upload_url:
                    raise PublishingError("이미지 업로드 URL을 가져오는데 실패했습니다.")
                
                # 이미지 업로드
                container_id = self._upload_image(img_path, upload_url)
                if container_id:
                    image_media_ids.append(container_id)
            
            if not image_media_ids:
                raise PublishingError("이미지 업로드에 실패했습니다.")
            
            # 캐러셀로 게시 (여러 이미지인 경우)
            if len(image_media_ids) > 1:
                container_id = self._create_carousel(image_media_ids, full_caption)
                if not container_id:
                    raise PublishingError("캐러셀 생성에 실패했습니다.")
            else:
                container_id = image_media_ids[0]
            
            # 게시물 발행
            post_id = self._publish_media(container_id)
            if not post_id:
                raise PublishingError("미디어 게시에 실패했습니다.")
            
            # 게시물 URL 생성
            post_url = f"https://www.instagram.com/p/{post_id}"
            
            logger.info(f"Instagram 게시 완료: {post_url}")
            return PublishResult(
                success=True,
                platform=Platform.INSTAGRAM,
                url=post_url,
                post_id=post_id
            )
        
        except Exception as e:
            logger.error(f"Instagram 발행 중 오류: {e}")
            return PublishResult(
                success=False,
                platform=Platform.INSTAGRAM,
                error=str(e)
            )
    
    def _get_upload_url(self, image_path: str) -> Optional[str]:
        """Instagram API에서 이미지 업로드 URL을 가져옵니다."""
        try:
            # 이미지 업로드 URL 요청
            url = f"{self.base_url}/{self.account_id}/media"
            params = {
                "access_token": self.access_token,
                "image_url": image_path  # 실제로는 URL이 필요하므로 이미지 서버에 먼저 업로드해야 함
            }
            
            response = requests.post(url, data=params)
            result = response.json()
            
            if "id" in result:
                return result["id"]
            else:
                logger.error(f"이미지 업로드 URL 획득 실패: {result.get('error', {}).get('message', '')}")
                return None
        
        except Exception as e:
            logger.error(f"이미지 업로드 URL 획득 중 오류: {e}")
            return None
    
    def _upload_image(self, image_path: str, upload_url: str) -> Optional[str]:
        """이미지를 Instagram API 서버에 업로드합니다."""
        try:
            # 이미지 업로드 (실제 구현에서는 multipart/form-data 사용 필요)
            with open(image_path, "rb") as img_file:
                files = {"file": img_file}
                response = requests.post(upload_url, files=files)
                result = response.json()
                
                if "id" in result:
                    return result["id"]
                else:
                    logger.error(f"이미지 업로드 실패: {result.get('error', {}).get('message', '')}")
                    return None
        
        except Exception as e:
            logger.error(f"이미지 업로드 중 오류: {e}")
            return None
    
    def _create_carousel(self, image_ids: List[str], caption: str) -> Optional[str]:
        """여러 이미지를 캐러셀로 묶습니다."""
        try:
            # 캐러셀 생성 요청
            url = f"{self.base_url}/{self.account_id}/media"
            params = {
                "access_token": self.access_token,
                "media_type": "CAROUSEL",
                "children": ",".join(image_ids),
                "caption": caption
            }
            
            response = requests.post(url, data=params)
            result = response.json()
            
            if "id" in result:
                return result["id"]
            else:
                logger.error(f"캐러셀 생성 실패: {result.get('error', {}).get('message', '')}")
                return None
        
        except Exception as e:
            logger.error(f"캐러셀 생성 중 오류: {e}")
            return None
    
    def _publish_media(self, container_id: str) -> Optional[str]:
        """미디어를 인스타그램에 게시합니다."""
        try:
            # 게시물 발행 요청
            url = f"{self.base_url}/{self.account_id}/media_publish"
            params = {
                "access_token": self.access_token,
                "creation_id": container_id
            }
            
            response = requests.post(url, data=params)
            result = response.json()
            
            if "id" in result:
                return result["id"]
            else:
                logger.error(f"미디어 게시 실패: {result.get('error', {}).get('message', '')}")
                return None
        
        except Exception as e:
            logger.error(f"미디어 게시 중 오류: {e}")
            return None