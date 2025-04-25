# 꽃집 콘텐츠 자동화 시스템

꽃 이미지를 업로드하면 AI가 자동으로 분석하여 네이버 블로그 포스트, 인스타그램 게시물, 유튜브 쇼츠 비디오를 생성하고 게시하는 자동화 솔루션입니다.

## 주요 기능

- **꽃 이미지 분석**: Claude API를 통해 꽃 이미지를 분석하여 꽃의 종류, 색상, 꽃말, 계절감 등 정보 추출
- **콘텐츠 자동 생성**: 분석된 정보를 바탕으로 블로그 글, 인스타그램 캡션, 해시태그 자동 생성
- **비디오 자동 제작**: 여러 이미지를 활용한 쇼츠 형태의 짧은 영상 자동 생성
- **소셜 미디어 자동 배포**: 네이버 블로그, 인스타그램, 유튜브 쇼츠에 자동 게시
- **비동기 작업 처리**: Celery를 통한 효율적인 백그라운드 작업 관리

## 시스템 아키텍처

이 프로젝트는 SOLID 원칙과 클린 아키텍처를 따르는 계층형 구조로 설계되었습니다:

- **도메인 계층**: 핵심 비즈니스 로직과 엔티티
- **애플리케이션 계층**: 사용자 인터페이스 및 API
- **인프라스트럭처 계층**: 외부 서비스 통합 및 데이터 액세스

## 기술 스택

- **백엔드**: Python + FastAPI
- **데이터베이스**: SQLAlchemy + SQLite/PostgreSQL
- **AI 통합**: Claude API (Anthropic)
- **이미지/비디오 처리**: Pillow, MoviePy
- **작업 큐**: Celery + Redis
- **외부 API 통합**: 네이버 블로그, Instagram Graph API, YouTube Data API

## 설치 및 실행 방법

### 사전 요구사항

- Python 3.9+
- Redis 서버
- FFmpeg (비디오 처리용)

### 설치

1. 저장소 클론:
```bash
git clone https://github.com/yourusername/flower-shop-automation.git
cd flower-shop-automation
```

2. 가상환경 생성 및 활성화:
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. 의존성 패키지 설치:
```bash
pip install -r requirements.txt
```

4. 환경 변수 설정:
```bash
cp .env.example .env
# .env 파일을 편집하여 API 키 및 계정 정보 입력
```

### 실행

1. Redis 서버 실행:
```bash
redis-server
```

2. Celery 워커 실행:
```bash
celery -A workers.celery_app:celery_app worker --loglevel=info
```

3. 웹 서버 실행:
```bash
python main.py
```

## API 사용법

### 꽃 이미지 업로드 및 콘텐츠 생성

**POST /upload/**

JSON 형식:
```json
{
  "title": "아름다운 장미",
  "description": "붉은 장미 사진 모음",
  "platforms": ["naver", "instagram", "youtube"]
}
```

파일 업로드: `images[]`에 여러 개의 이미지 파일 업로드 가능

### 생성된 포스트 조회

**GET /posts/**

모든 포스트 목록을 반환합니다.

**GET /posts/{post_id}**

특정 포스트의 상세 정보를 반환합니다.

## 개발자 문서

추가적인 개발자 문서는 `docs/` 디렉토리에서 확인할 수 있습니다:

- [아키텍처 설계 문서](docs/architecture.md)
- [API 명세](docs/api.md)
- [개발 가이드라인](docs/development.md)

## 라이센스

이 프로젝트는 MIT 라이센스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.