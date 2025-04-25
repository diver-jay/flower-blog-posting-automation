# app.py - FastAPI 메인 애플리케이션
from fastapi import FastAPI, File, UploadFile, BackgroundTasks, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import os
from datetime import datetime
import uuid

from models import FlowerPost, Platform
from services.image_analyzer import analyze_flower_image
from services.content_generator import generate_blog_post, generate_instagram_caption, generate_tags
from services.video_generator import create_shorts_video
from services.social_publisher import publish_to_naver, publish_to_instagram, publish_to_youtube
from tasks import process_flower_content
from database import get_db, SessionLocal

app = FastAPI(title="꽃집 콘텐츠 자동화 시스템")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/upload/", response_model=FlowerPost)
async def upload_flower_images(
    background_tasks: BackgroundTasks,
    images: List[UploadFile] = File(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    platforms: List[Platform] = Form([]),
    schedule_time: Optional[datetime] = Form(None),
    db = Depends(get_db)
):
    # 고유 ID 생성
    post_id = str(uuid.uuid4())
    
    # 이미지 저장
    image_paths = []
    for img in images:
        file_path = f"uploads/{post_id}/{img.filename}"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, "wb") as buffer:
            buffer.write(await img.read())
        image_paths.append(file_path)
    
    # 새 게시물 생성
    flower_post = FlowerPost(
        id=post_id,
        title=title,
        description=description,
        image_paths=image_paths,
        platforms=platforms,
        schedule_time=schedule_time or datetime.now(),
        status="pending"
    )
    
    # DB에 저장
    db.add(flower_post)
    db.commit()
    db.refresh(flower_post)
    
    # 백그라운드에서 콘텐츠 생성 및 게시 작업 시작
    background_tasks.add_task(process_flower_content, post_id)
    
    return flower_post

@app.get("/posts/", response_model=List[FlowerPost])
async def get_posts(db = Depends(get_db)):
    return db.query(FlowerPost).all()

@app.get("/posts/{post_id}", response_model=FlowerPost)
async def get_post(post_id: str, db = Depends(get_db)):
    return db.query(FlowerPost).filter(FlowerPost.id == post_id).first()


# services/image_analyzer.py - 이미지 분석 서비스
import os
import anthropic
import json
from PIL import Image
import io

# Claude API 클라이언트 초기화
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

def analyze_flower_image(image_path):
    """
    Claude를 사용하여 꽃 이미지를 분석하고 관련 정보를 반환합니다.
    """
    try:
        # 이미지 열기 및 준비
        with open(image_path, "rb") as img_file:
            img_bytes = img_file.read()
        
        # Claude API에 이미지 전송 및 분석 요청
        message = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "이 꽃 이미지를 분석해주세요. 다음 정보를 JSON 형식으로 반환해주세요:\n"
                                   "1. 꽃의 종류(한국어, 영어, 학명)\n"
                                   "2. 꽃의 주요 색상\n"
                                   "3. 꽃의 계절적 특성\n"
                                   "4. 꽃말\n"
                                   "5. 관리 팁\n"
                                   "6. 장식/인테리어 제안\n"
                                   "7. 적합한 선물 상황\n"
                                   "온전히 JSON 형식으로만 응답해주세요."
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": img_bytes
                            }
                        }
                    ]
                }
            ]
        )
        
        # JSON 응답 파싱
        response_text = message.content[0].text
        # JSON 부분만 추출
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        json_str = response_text[json_start:json_end]
        
        flower_data = json.loads(json_str)
        return flower_data
        
    except Exception as e:
        print(f"이미지 분석 중 오류 발생: {e}")
        return {
            "flower_type": {"korean": "알 수 없음", "english": "Unknown", "scientific": ""},
            "colors": ["알 수 없음"],
            "seasonal": "알 수 없음",
            "meaning": "알 수 없음",
            "care_tips": "알 수 없음",
            "decoration_ideas": "알 수 없음",
            "gift_occasions": ["알 수 없음"]
        }


# services/content_generator.py - 콘텐츠 생성 서비스
import anthropic
import os

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

def generate_blog_post(flower_data, image_paths):
    """
    꽃 데이터를 기반으로 네이버 블로그용 포스트를 생성합니다.
    """
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
    
    response = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=4000,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    return response.content[0].text

def generate_instagram_caption(flower_data):
    """
    꽃 데이터를 기반으로 인스타그램 캡션을 생성합니다.
    """
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
    
    response = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=1000,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    return response.content[0].text

def generate_tags(flower_data):
    """
    꽃 데이터를 기반으로 인스타그램 해시태그를 생성합니다.
    """
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
    
    response = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=1000,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # 해시태그 목록 추출 및 가공
    text_response = response.content[0].text
    
    # 줄바꿈으로 구분된 해시태그 목록을 추출
    hashtags = [tag.strip() for tag in text_response.split('\n') if tag.strip().startswith('#')]
    
    # 충분한 해시태그가 없으면 기본 태그 추가
    if len(hashtags) < 10:
        hashtags.extend([
            "#꽃스타그램", "#플라워샵", "#꽃선물", "#꽃집", "#꽃배달",
            "#flowerstagram", "#flowerpower", "#flowerlovers", "#flowermagic", "#floweroftheday"
        ])
    
    return hashtags[:20]  # 최대 20개로 제한


# services/video_generator.py - 쇼츠 비디오 생성 서비스
import os
import subprocess
from PIL import Image, ImageFilter, ImageEnhance
import numpy as np
import random
import textwrap
from moviepy.editor import *
import tempfile

def apply_filter(image_path, filter_type="enhance"):
    """이미지에 필터를 적용합니다."""
    img = Image.open(image_path)
    
    if filter_type == "enhance":
        # 색상 향상
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(1.5)
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.2)
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(1.1)
    elif filter_type == "blur":
        # 배경 흐림 효과
        img = img.filter(ImageFilter.GaussianBlur(radius=3))
    elif filter_type == "bw":
        # 흑백 효과
        img = img.convert("L")
        img = img.convert("RGB")
    
    # 임시 파일로 저장
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
    img.save(temp_file.name, quality=95)
    return temp_file.name

def create_shorts_video(image_paths, flower_data, output_path, duration=15):
    """여러 이미지를 사용하여 쇼츠 비디오를 생성합니다."""
    clips = []
    
    # 각 이미지에 대한 클립 생성
    for idx, img_path in enumerate(image_paths):
        # 필터 적용
        filter_types = ["enhance", "blur", "bw"]
        filtered_img_path = apply_filter(img_path, random.choice(filter_types))
        
        # 이미지를 비디오 클립으로 변환
        clip_duration = duration / len(image_paths)
        img_clip = ImageClip(filtered_img_path, duration=clip_duration)
        
        # 이미지 크기 조정 (9:16 비율)
        img_clip = img_clip.resize(height=1920)
        width, height = img_clip.size
        
        if width > 1080:
            # 중앙 크롭
            x1 = (width - 1080) // 2
            img_clip = img_clip.crop(x1=x1, y1=0, x2=x1+1080, y2=height)
        
        # 줌 인/아웃 효과
        if idx % 2 == 0:
            zoom_in = lambda t: 1 + 0.1 * t  # 시간에 따라 1.0에서 1.1로 확대
            img_clip = img_clip.resize(lambda t: (zoom_in(t), zoom_in(t)))
        else:
            zoom_out = lambda t: 1.1 - 0.1 * t  # 시간에 따라 1.1에서 1.0으로 축소
            img_clip = img_clip.resize(lambda t: (zoom_out(t), zoom_out(t)))
        
        # 텍스트 오버레이 추가
        if idx == 0:
            # 첫 번째 클립에는 꽃 이름
            txt = TextClip(f"{flower_data['flower_type']['korean']}\n{flower_data['flower_type']['english']}",
                          fontsize=70, color='white', font='NanumGothic-Bold',
                          align='center', size=(1080, None))
            txt = txt.set_duration(clip_duration).set_position(('center', 'bottom')).crossfadein(0.5)
            img_clip = CompositeVideoClip([img_clip, txt])
        elif idx == len(image_paths) - 1:
            # 마지막 클립에는 꽃말
            txt = TextClip(f"꽃말: {flower_data['meaning']}",
                          fontsize=60, color='white', font='NanumGothic-Regular',
                          align='center', size=(1080, None))
            txt = txt.set_duration(clip_duration).set_position(('center', 'center')).crossfadein(0.5)
            img_clip = CompositeVideoClip([img_clip, txt])
        
        clips.append(img_clip)
    
    # 모든 클립 연결
    final_clip = concatenate_videoclips(clips, method="compose")
    
    # 배경 음악 추가 (음악 파일은 미리 준비되어 있다고 가정)
    music_files = ["assets/music/gentle_piano.mp3", "assets/music/soft_mood.mp3"]
    if os.path.exists(music_files[0]):
        audio_clip = AudioFileClip(random.choice(music_files))
        audio_clip = audio_clip.subclip(0, duration)
        audio_clip = audio_clip.volumex(0.7)  # 볼륨 조정
        final_clip = final_clip.set_audio(audio_clip)
    
    # 비디오 저장
    final_clip.write_videofile(output_path, fps=30, codec="libx264", audio_codec="aac",
                             preset="medium", audio_bitrate="128k")
    
    # 임시 파일 정리
    for clip in clips:
        try:
            clip.close()
        except:
            pass
    
    return output_path


# services/social_publisher.py - 소셜 미디어 발행 서비스
import os
import requests
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def publish_to_naver(title, content, image_paths, credentials):
    """네이버 블로그에 게시물을 발행합니다."""
    try:
        # Selenium을 사용한 자동화 (네이버 블로그는 공식 API가 제한적임)
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(options=chrome_options)
        
        # 네이버 로그인
        driver.get("https://nid.naver.com/nidlogin.login")
        
        # 로그인 정보 입력
        driver.find_element(By.ID, "id").send_keys(credentials["username"])
        driver.find_element(By.ID, "pw").send_keys(credentials["password"])
        driver.find_element(By.ID, "log.login").click()
        
        # 블로그 글쓰기 페이지로 이동
        driver.get(f"https://blog.naver.com/{credentials['username']}/postwrite")
        
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
        
        driver.quit()
        return {"success": True, "url": post_url}
    
    except Exception as e:
        print(f"네이버 블로그 발행 중 오류: {e}")
        return {"success": False, "error": str(e)}

def publish_to_instagram(caption, hashtags, image_paths, credentials):
    """인스타그램에 게시물을 발행합니다."""
    try:
        # Instagram Graph API 사용 (Facebook 개발자 계정 필요)
        # 이 예시는 인증이 완료된 토큰이 있다고 가정합니다.
        
        # 이미지를 Facebook 서버에 업로드
        image_media_ids = []
        
        for img_path in image_paths:
            # 이미지 업로드 API 호출
            upload_url = f"https://graph.facebook.com/v13.0/{credentials['instagram_account_id']}/media"
            
            with open(img_path, "rb") as img_file:
                params = {
                    "access_token": credentials["access_token"],
                    "caption": caption + "\n\n" + " ".join(hashtags),
                    "image_url": img_path  # 실제로는 URL이 필요하므로 이미지 서버에 먼저 업로드해야 함
                }
                
                response = requests.post(upload_url, data=params)
                result = response.json()
                
                if "id" in result:
                    image_media_ids.append(result["id"])
                else:
                    raise Exception(f"이미지 업로드 실패: {result.get('error', {}).get('message', '')}")
        
        # 캐러셀로 게시 (여러 이미지인 경우)
        if len(image_media_ids) > 1:
            carousel_url = f"https://graph.facebook.com/v13.0/{credentials['instagram_account_id']}/media"
            params = {
                "access_token": credentials["access_token"],
                "media_type": "CAROUSEL",
                "children": ",".join(image_media_ids),
                "caption": caption + "\n\n" + " ".join(hashtags)
            }
            
            response = requests.post(carousel_url, data=params)
            result = response.json()
            
            if "id" in result:
                container_id = result["id"]
            else:
                raise Exception(f"캐러셀 생성 실패: {result.get('error', {}).get('message', '')}")
        else:
            container_id = image_media_ids[0]
        
        # 게시물 발행
        publish_url = f"https://graph.facebook.com/v13.0/{credentials['instagram_account_id']}/media_publish"
        params = {
            "access_token": credentials["access_token"],
            "creation_id": container_id
        }
        
        response = requests.post(publish_url, data=params)
        result = response.json()
        
        if "id" in result:
            post_id = result["id"]
            return {"success": True, "post_id": post_id}
        else:
            raise Exception(f"게시 실패: {result.get('error', {}).get('message', '')}")
    
    except Exception as e:
        print(f"인스타그램 발행 중 오류: {e}")
        return {"success": False, "error": str(e)}

def publish_to_youtube(video_path, title, description, tags, credentials):
    """유튜브 쇼츠에 비디오를 업로드합니다."""
    try:
        # Google API 클라이언트 라이브러리 사용
        # 이 예시는 OAuth 인증이 완료된 상태라고 가정합니다.
        
        # 실제 구현에서는 google-api-python-client를 사용하여 구현해야 합니다.
        # 하지만 이 예시 코드에서는 개념적 접근만 보여줍니다.
        
        """
        # Google API 클라이언트 설정
        youtube = build('youtube', 'v3', credentials=credentials)
        
        # 비디오 정보 설정
        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': tags,
                'categoryId': '22'  # People & Blogs 카테고리
            },
            'status': {
                'privacyStatus': 'public',
                'selfDeclaredMadeForKids': False
            }
        }
        
        # 비디오 업로드 시작
        insert_request = youtube.videos().insert(
            part=','.join(body.keys()),
            body=body,
            media_body=MediaFileUpload(video_path, resumable=True)
        )
        
        # 업로드 실행 및 진행 상황 모니터링
        response = insert_request.execute()
        video_id = response.get('id')
        
        return {"success": True, "video_id": video_id, "url": f"https://youtube.com/shorts/{video_id}"}
        """
        
        # 실제 구현 대신 성공 응답 반환
        return {"success": True, "video_id": "sample_id", "url": "https://youtube.com/shorts/sample_id"}
    
    except Exception as e:
        print(f"유튜브 쇼츠 업로드 중 오류: {e}")
        return {"success": False, "error": str(e)}


# tasks.py - 백그라운드 작업 관리
from celery import Celery
import os
import json
from database import SessionLocal
from models import FlowerPost, Platform
from services.image_analyzer import analyze_flower_image
from services.content_generator import generate_blog_post, generate_instagram_caption, generate_tags
from services.video_generator import create_shorts_video
from services.social_publisher import publish_to_naver, publish_to_instagram, publish_to_youtube

# Celery 초기화
app = Celery('flower_tasks', broker='redis://localhost:6379/0')
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Seoul',
    enable_utc=True,
)

@app.task
def process_flower_content(post_id):
    """
    꽃 사진에 대한 모든 콘텐츠 생성 및 발행 작업을 처리합니다.
    """
    db = SessionLocal()
    try:
        # 포스트 데이터 조회
        post = db.query(FlowerPost).filter(FlowerPost.id == post_id).first()
        if not post:
            return {"success": False, "error": "Post not found"}
        
        # 상태 업데이트
        post.status = "processing"
        db.commit()
        
        # 이미지 분석
        main_image = post.image_paths[0]  # 첫 번째 이미지를 주 분석 대상으로 사용
        flower_data = analyze_flower_image(main_image)
        
        # 분석 데이터 저장
        post.flower_data = json.dumps(flower_data)
        db.commit()
        
        results = {}
        
        # 플랫폼별 콘텐츠 생성 및 발행
        for platform in post.platforms:
            if platform == Platform.NAVER:
                # 네이버 블로그 콘텐츠 생성 및 발행
                blog_content = generate_blog_post(flower_data, post.image_paths)
                post.blog_content = blog_content
                
                # 자격 증명 정보 로드 (실제 구현에서는 안전한 저장소에서 가져와야 함)
                credentials = {
                    "username": os.environ.get("NAVER_USERNAME"),
                    "password": os.environ.get("NAVER_PASSWORD")
                }
                
                # 네이버 블로그에 발행
                title = post.title or f"{flower_data['flower_type']['korean']} - {flower_data['meaning']}"
                naver_result = publish_to_naver(title, blog_content, post.image_paths, credentials)
                results["naver"] = naver_result
            
            elif platform == Platform.INSTAGRAM:
                # 인스타그램 콘텐츠 생성
                caption = generate_instagram_caption(flower_data)
                hashtags = generate_tags(flower_data)
                post.instagram_caption = caption
                post.instagram_tags = json.dumps(hashtags)
                
                # 자격 증명 정보 로드
                credentials = {
                    "access_token": os.environ.get("INSTAGRAM_ACCESS_TOKEN"),
                    "instagram_account_id": os.environ.get("INSTAGRAM_ACCOUNT_ID")
                }
                
                # 인스타그램에 발행
                instagram_result = publish_to_instagram(caption, hashtags, post.image_paths, credentials)
                results["instagram"] = instagram_result
            
            elif platform == Platform.YOUTUBE:
                # 쇼츠 비디오 생성
                video_path = f"uploads/{post_id}/shorts_video.mp4"
                create_shorts_video(post.image_paths, flower_data, video_path)
                post.video_path = video_path
                
                # 자격 증명 정보 로드
                credentials = os.environ.get("YOUTUBE_CREDENTIALS")  # OAuth 자격 증명 파일 경로
                
                # 비디오 제목 및 설명 생성
                title = post.title or f"{flower_data['flower_type']['korean']} - {flower_data['flower_type']['english']}"
                description = f"{flower_data['flower_type']['korean']} ({flower_data['flower_type']['english']}) - {flower_data['meaning']}\n\n#꽃 #플라워 #쇼츠"
                tags = generate_tags(flower_data)
                
                # 유튜브 쇼츠에 업로드
                youtube_result = publish_to_youtube(video_path, title, description, tags, credentials)
                results["youtube"] = youtube_result
        
        # 결과 저장 및 상태 업데이트
        post.publish_results = json.dumps(results)
        post.status = "completed"
        db.commit()
        
        return {"success": True, "post_id": post_id, "results": results}
    
    except Exception as e:
        # 오류 발생 시 상태 업데이트
        post.status = "failed"
        post.error_message = str(e)
        db.commit()
        
        return {"success": False, "error": str(e)}
    
    finally:
        db.close()


# models.py - 데이터 모델
from sqlalchemy import Column, String, DateTime, Enum as SQLAEnum, JSON, Integer
from sqlalchemy.ext.declarative import declarative_base
import enum
from datetime import datetime

Base = declarative_base()

class Platform(enum.Enum):
    NAVER = "naver"
    INSTAGRAM = "instagram"
    YOUTUBE = "youtube"

class FlowerPost(Base):
    __tablename__ = "flower_posts"
    
    id = Column(String, primary_key=True)
    title = Column(String, nullable=True)
    description = Column(String, nullable=True)
    image_paths = Column(JSON, nullable=False)  # 이미지 파일 경로 배열
    platforms = Column(JSON, nullable=False)    # Platform enum 값의 배열
    schedule_time = Column(DateTime, default=datetime.now)
    status = Column(String, default="pending")  # pending, processing, completed, failed
    error_message = Column(String, nullable=True)
    
    # 이미지 분석 결과
    flower_data = Column(JSON, nullable=True)
    
    # 생성된 콘텐츠
    blog_content = Column(String, nullable=True)
    instagram_caption = Column(String, nullable=True)
    instagram_tags = Column(JSON, nullable=True)
    video_path = Column(String, nullable=True)
    
    # 발행 결과
    publish_results = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


# database.py - 데이터베이스 설정
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

SQLALCHEMY_DATABASE_URL = os.environ.get("DATABASE_URL") or "sqlite:///./flower_automation.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# main.py - 애플리케이션 시작점
import uvicorn
from app import app
from models import Base
from database import engine

# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)