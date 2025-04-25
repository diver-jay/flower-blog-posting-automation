# infrastructure/ai/image_processing.py - 이미지 처리 유틸리티

import os
import tempfile
import logging
from typing import Tuple, Optional
from PIL import Image, ImageOps, ImageEnhance, ImageDraw, ImageFont, ImageFilter

logger = logging.getLogger(__name__)

def resize_image(
    image_path: str,
    target_size: Tuple[int, int],
    keep_aspect_ratio: bool = True,
    output_path: Optional[str] = None
) -> str:
    """
    이미지 크기를 조정합니다.
    
    Args:
        image_path: 이미지 파일 경로
        target_size: 목표 크기 (너비, 높이)
        keep_aspect_ratio: 종횡비 유지 여부
        output_path: 출력 파일 경로 (None인 경우 임시 파일 생성)
        
    Returns:
        str: 크기가 조정된 이미지 파일 경로
    """
    try:
        img = Image.open(image_path)
        
        if keep_aspect_ratio:
            img.thumbnail(target_size, Image.LANCZOS)
        else:
            img = img.resize(target_size, Image.LANCZOS)
        
        if output_path is None:
            # 임시 파일 생성
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
            output_path = temp_file.name
        else:
            # 출력 디렉토리 생성
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 이미지 저장
        img.save(output_path, quality=95)
        logger.debug(f"이미지 크기 조정 완료: {output_path}")
        
        return output_path
    
    except Exception as e:
        logger.error(f"이미지 크기 조정 중 오류 발생: {e}")
        raise e

def add_watermark(
    image_path: str,
    text: str,
    position: Tuple[int, int] = None,
    font_size: int = 30,
    font_color: Tuple[int, int, int, int] = (255, 255, 255, 128),
    output_path: Optional[str] = None
) -> str:
    """
    이미지에 워터마크를 추가합니다.
    
    Args:
        image_path: 이미지 파일 경로
        text: 워터마크 텍스트
        position: 워터마크 위치 (None인 경우 우하단)
        font_size: 폰트 크기
        font_color: 폰트 색상 (RGBA)
        output_path: 출력 파일 경로 (None인 경우 임시 파일 생성)
        
    Returns:
        str: 워터마크가 추가된 이미지 파일 경로
    """
    try:
        img = Image.open(image_path).convert("RGBA")
        
        # 워터마크 레이어 생성
        watermark = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(watermark)
        
        # 폰트 로드 (기본 폰트 사용)
        try:
            font = ImageFont.truetype("NanumGothic.ttf", font_size)
        except IOError:
            font = ImageFont.load_default()
        
        # 텍스트 크기 계산
        text_width, text_height = draw.textsize(text, font=font)
        
        # 워터마크 위치 계산 (기본값: 우하단)
        if position is None:
            position = (img.width - text_width - 20, img.height - text_height - 20)
        
        # 워터마크 그리기
        draw.text(position, text, font=font, fill=font_color)
        
        # 이미지에 워터마크 합성
        result = Image.alpha_composite(img, watermark)
        result = result.convert("RGB")
        
        if output_path is None:
            # 임시 파일 생성
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
            output_path = temp_file.name
        else:
            # 출력 디렉토리 생성
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 이미지 저장
        result.save(output_path, quality=95)
        logger.debug(f"워터마크 추가 완료: {output_path}")
        
        return output_path
    
    except Exception as e:
        logger.error(f"워터마크 추가 중 오류 발생: {e}")
        raise e

def enhance_image(
    image_path: str,
    brightness: float = 1.0,
    contrast: float = 1.0,
    color: float = 1.2,
    sharpness: float = 1.0,
    output_path: Optional[str] = None
) -> str:
    """
    이미지 품질을 향상시킵니다.
    
    Args:
        image_path: 이미지 파일 경로
        brightness: 밝기 조정 (1.0 = 변화 없음)
        contrast: 대비 조정 (1.0 = 변화 없음)
        color: 색상 조정 (1.0 = 변화 없음)
        sharpness: 선명도 조정 (1.0 = 변화 없음)
        output_path: 출력 파일 경로 (None인 경우 임시 파일 생성)
        
    Returns:
        str: 향상된 이미지 파일 경로
    """
    try:
        img = Image.open(image_path)
        
        # 이미지 향상
        if brightness != 1.0:
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(brightness)
        
        if contrast != 1.0:
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(contrast)
        
        if color != 1.0:
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(color)
        
        if sharpness != 1.0:
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(sharpness)
        
        if output_path is None:
            # 임시 파일 생성
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
            output_path = temp_file.name
        else:
            # 출력 디렉토리 생성
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 이미지 저장
        img.save(output_path, quality=95)
        logger.debug(f"이미지 향상 완료: {output_path}")
        
        return output_path
    
    except Exception as e:
        logger.error(f"이미지 향상 중 오류 발생: {e}")
        raise e