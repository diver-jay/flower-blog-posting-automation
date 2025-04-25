# core/services/video_generator.py - 비디오 생성 서비스

import os
import tempfile
import random
import logging
from typing import Dict, Any, List

from PIL import Image, ImageFilter, ImageEnhance
from moviepy.editor import ImageClip, AudioFileClip, TextClip, CompositeVideoClip, concatenate_videoclips

from core.interfaces.media_processor import MediaProcessorInterface
from domain.exceptions import MediaProcessingError

logger = logging.getLogger(__name__)

class MoviepyVideoGenerator(MediaProcessorInterface):
    """MoviePy를 사용하여 비디오를 생성하는 서비스"""
    
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
        try:
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
            logger.debug(f"이미지 필터 적용 완료: {filter_type}, 결과 파일: {temp_file.name}")
            return temp_file.name
        
        except Exception as e:
            logger.error(f"이미지 필터 적용 중 오류 발생: {e}")
            raise MediaProcessingError(f"이미지 필터 적용 중 오류가 발생했습니다: {str(e)}")
    
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
        try:
            # 출력 디렉토리 생성
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            clips = []
            
            # 각 이미지에 대한 클립 생성
            for idx, img_path in enumerate(image_paths):
                # 필터 적용
                filter_types = ["enhance", "blur", "bw"]
                filtered_img_path = self.apply_filter(img_path, random.choice(filter_types))
                
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
                    txt = TextClip(
                        f"{flower_data['flower_type']['korean']}\n{flower_data['flower_type']['english']}",
                        fontsize=70, color='white', font='NanumGothic-Bold',
                        align='center', size=(1080, None)
                    )
                    txt = txt.set_duration(clip_duration).set_position(('center', 'bottom')).crossfadein(0.5)
                    img_clip = CompositeVideoClip([img_clip, txt])
                elif idx == len(image_paths) - 1:
                    # 마지막 클립에는 꽃말
                    txt = TextClip(
                        f"꽃말: {flower_data['meaning']}",
                        fontsize=60, color='white', font='NanumGothic-Regular',
                        align='center', size=(1080, None)
                    )
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
            final_clip.write_videofile(
                output_path,
                fps=30,
                codec="libx264",
                audio_codec="aac",
                preset="medium",
                audio_bitrate="128k"
            )
            
            # 임시 파일 정리
            for clip in clips:
                try:
                    clip.close()
                except:
                    pass
            
            logger.info(f"쇼츠 비디오 생성 완료: {output_path}")
            return output_path
        
        except Exception as e:
            logger.error(f"쇼츠 비디오 생성 중 오류 발생: {e}")
            raise MediaProcessingError(f"쇼츠 비디오 생성 중 오류가 발생했습니다: {str(e)}")