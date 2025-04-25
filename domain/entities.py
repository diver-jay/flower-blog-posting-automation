# domain/entities.py - 도메인 엔티티

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
import json

class Platform(str, Enum):
    """소셜 미디어 플랫폼 열거형"""
    NAVER = "naver"
    INSTAGRAM = "instagram"
    YOUTUBE = "youtube"

class PostStatus(str, Enum):
    """포스트 상태 열거형"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class FlowerData:
    """꽃 분석 데이터"""
    flower_type: Dict[str, str]  # {"korean": "장미", "english": "Rose", "scientific": "Rosa"}
    colors: List[str]
    seasonal: str
    meaning: str
    care_tips: str
    decoration_ideas: str
    gift_occasions: List[str]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FlowerData':
        """딕셔너리에서 FlowerData 객체를 생성합니다."""
        return cls(
            flower_type=data.get("flower_type", {"korean": "", "english": "", "scientific": ""}),
            colors=data.get("colors", []),
            seasonal=data.get("seasonal", ""),
            meaning=data.get("meaning", ""),
            care_tips=data.get("care_tips", ""),
            decoration_ideas=data.get("decoration_ideas", ""),
            gift_occasions=data.get("gift_occasions", [])
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """FlowerData 객체를 딕셔너리로 변환합니다."""
        return {
            "flower_type": self.flower_type,
            "colors": self.colors,
            "seasonal": self.seasonal,
            "meaning": self.meaning,
            "care_tips": self.care_tips,
            "decoration_ideas": self.decoration_ideas,
            "gift_occasions": self.gift_occasions
        }

@dataclass
class PublishResult:
    """소셜 미디어 게시 결과"""
    success: bool
    platform: Platform
    url: Optional[str] = None
    post_id: Optional[str] = None
    error: Optional[str] = None

@dataclass
class FlowerPost:
    """꽃 포스트 엔티티"""
    id: str
    image_paths: List[str]
    platforms: List[Platform]
    title: Optional[str] = None
    description: Optional[str] = None
    schedule_time: datetime = field(default_factory=datetime.now)
    status: str = PostStatus.PENDING.value
    error_message: Optional[str] = None
    
    # 이미지 분석 결과
    flower_data: Optional[Union[FlowerData, Dict[str, Any]]] = None
    
    # 생성된 콘텐츠
    blog_content: Optional[str] = None
    instagram_caption: Optional[str] = None
    instagram_tags: Optional[List[str]] = None
    video_path: Optional[str] = None
    
    # 발행 결과
    publish_results: List[PublishResult] = field(default_factory=list)
    
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """초기화 후 처리"""
        # flower_data가 딕셔너리인 경우 FlowerData 객체로 변환
        if isinstance(self.flower_data, dict):
            self.flower_data = FlowerData.from_dict(self.flower_data)
    
    def update_status(self, status: PostStatus, error_message: Optional[str] = None):
        """포스트 상태를 업데이트합니다."""
        self.status = status.value
        if error_message:
            self.error_message = error_message
        self.updated_at = datetime.now()
    
    def add_publish_result(self, result: PublishResult):
        """게시 결과를 추가합니다."""
        self.publish_results.append(result)
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """FlowerPost 객체를 딕셔너리로 변환합니다."""
        flower_data_dict = None
        if self.flower_data:
            if isinstance(self.flower_data, FlowerData):
                flower_data_dict = self.flower_data.to_dict()
            else:
                flower_data_dict = self.flower_data
        
        publish_results_dict = []
        for result in self.publish_results:
            publish_results_dict.append({
                "success": result.success,
                "platform": result.platform.value,
                "url": result.url,
                "post_id": result.post_id,
                "error": result.error
            })
        
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "image_paths": self.image_paths,
            "platforms": [p.value for p in self.platforms],
            "schedule_time": self.schedule_time.isoformat(),
            "status": self.status,
            "error_message": self.error_message,
            "flower_data": flower_data_dict,
            "blog_content": self.blog_content,
            "instagram_caption": self.instagram_caption,
            "instagram_tags": self.instagram_tags,
            "video_path": self.video_path,
            "publish_results": publish_results_dict,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FlowerPost':
        """딕셔너리에서 FlowerPost 객체를 생성합니다."""
        # 플랫폼 문자열을 열거형으로 변환
        platforms = []
        for p in data.get("platforms", []):
            if isinstance(p, str):
                platforms.append(Platform(p))
            else:
                platforms.append(p)
        
        # 날짜 문자열을 datetime으로 변환
        schedule_time = data.get("schedule_time")
        if isinstance(schedule_time, str):
            schedule_time = datetime.fromisoformat(schedule_time)
        
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        
        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        
        # 게시 결과 딕셔너리를 PublishResult 객체로 변환
        publish_results = []
        for result in data.get("publish_results", []):
            if isinstance(result, dict):
                publish_results.append(PublishResult(
                    success=result.get("success", False),
                    platform=Platform(result.get("platform", "naver")),
                    url=result.get("url"),
                    post_id=result.get("post_id"),
                    error=result.get("error")
                ))
            else:
                publish_results.append(result)
        
        # 꽃 데이터 딕셔너리를 FlowerData 객체로 변환
        flower_data = data.get("flower_data")
        if isinstance(flower_data, dict):
            flower_data = FlowerData.from_dict(flower_data)
        
        return cls(
            id=data.get("id"),
            title=data.get("title"),
            description=data.get("description"),
            image_paths=data.get("image_paths", []),
            platforms=platforms,
            schedule_time=schedule_time or datetime.now(),
            status=data.get("status", PostStatus.PENDING.value),
            error_message=data.get("error_message"),
            flower_data=flower_data,
            blog_content=data.get("blog_content"),
            instagram_caption=data.get("instagram_caption"),
            instagram_tags=data.get("instagram_tags"),
            video_path=data.get("video_path"),
            publish_results=publish_results,
            created_at=created_at or datetime.now(),
            updated_at=updated_at or datetime.now()
        )