# infrastructure/external/naver_service.py - 네이버 블로그 서비스

import os
import time
import logging
from typing import List, Dict, Any

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from core.interfaces.publisher import NaverPublisherInterface
from domain.entities import PublishResult, Platform
from domain.exceptions import PublishingError

logger = logging.getLogger(__name__)

class NaverBlogPublisher(NaverPublisherInterface):
    """네이버 블로그 게시 서비스"""
    
    def __init__(self, username: str, password: str):
        """
        초기화
        
        Args:
            username: 네이버 아이디
            password: 네이버 비밀번호
        """
        self.username = username
        self.password = password
    
    def publish_to_naver(
        self,
        title: str,
        content: str,
        image_paths: List[str]
    ) -> PublishResult:
        """
        네이버 블로그에 게시물을 발행합니다.
        
        Args:
            title: 게시물 제목
            content: 게시물 내용
            image_paths: 이미지 파일 경로 목록
            
        Returns:
            PublishResult: 게시 결과
            
        Raises:
            PublishingError: 게시 중 오류가 발생한 경우
        """
        try:
            # 필수 필드 검증
            if not self.username or not self.password:
                raise PublishingError("네이버 블로그 계정 정보가 설정되지 않았습니다.")
            
            if not title:
                raise PublishingError("게시물 제목은 필수입니다.")
            
            if not content:
                raise PublishingError("게시물 내용은 필수입니다.")
            
            # Selenium 설정
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            
            driver = webdriver.Chrome(options=chrome_options)
            
            try:
                # 네이버 로그인
                driver.get("https://nid.naver.com/nidlogin.login")
                
                # 로그인 정보 입력
                driver.find_element(By.ID, "id").send_keys(self.username)
                driver.find_element(By.ID, "pw").send_keys(self.password)
                driver.find_element(By.ID, "log.login").click()
                
                # 로그인 결과 확인
                time.sleep(3)
                if "로그인 실패" in driver.page_source:
                    raise PublishingError("네이버 로그인에 실패했습니다. 계정 정보를 확인해주세요.")
                
                # 블로그 글쓰기 페이지로 이동
                driver.get(f"https://blog.naver.com/{self.username}/postwrite")
                
                # iframe 전환 (네이버 블로그 에디터는 iframe 내부에 있음)
                WebDriverWait(driver, 10).until(
                    EC.frame_to_be_available_and_switch_to_it((By.ID, "mainFrame"))
                )
                
                # 제목 입력
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "subject"))
                )
                driver.find_element(By.ID, "subject").send_keys(title)
                
                # 내용 입력 (SmartEditor 사용)
                driver.switch_to.frame("SmartEditorIframe")
                editor = driver.find_element(By.CLASS_NAME, "se2_inputarea")
                driver.execute_script(f"arguments[0].innerHTML = arguments[1];", editor, content)
                driver.switch_to.default_content()
                driver.switch_to.frame("mainFrame")
                
                # 이미지 업로드
                for img_path in image_paths:
                    if not os.path.exists(img_path):
                        logger.warning(f"이미지 파일을 찾을 수 없습니다: {img_path}")
                        continue
                        
                    # 이미지 버튼 클릭
                    driver.find_element(By.CLASS_NAME, "se2_photo").click()
                    
                    # 파일 선택 대화상자
                    file_input = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
                    )
                    file_input.send_keys(os.path.abspath(img_path))
                    
                    # 이미지 삽입 버튼 클릭
                    WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CLASS_NAME, "btn_confirm"))
                    ).click()
                    
                    # 이미지 업로드 대기
                    time.sleep(3)
                
                # 발행 버튼 클릭
                driver.find_element(By.CLASS_NAME, "btn_publish").click()
                
                # 발행 완료 대기
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "post_save"))
                )
                
                # 게시된 URL 가져오기
                post_url = driver.current_url
                
                logger.info(f"네이버 블로그 게시 완료: {post_url}")
                return PublishResult(
                    success=True,
                    platform=Platform.NAVER,
                    url=post_url
                )
            
            finally:
                # 항상 드라이버 종료
                driver.quit()
        
        except Exception as e:
            logger.error(f"네이버 블로그 발행 중 오류: {e}")
            return PublishResult(
                success=False,
                platform=Platform.NAVER,
                error=str(e)
            )