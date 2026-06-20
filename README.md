# AI Repo - 날씨·선호도 기반 여행 경로 & 옷차림 추천 API

날씨 정보와 사용자 선호도를 바탕으로 **여행 경로**와 **옷차림**을 추천해주는 REST API 서버입니다.
FastAPI로 개발하며, 외부 날씨 API와 LLM(거대언어모델)을 조합해 추천 결과를 생성합니다.
(추후 RAG / 벡터 검색 기능 확장 예정)

---

## 🛠️ 기술 스택

| 구분 | 사용 기술 |
|------|-----------|
| 언어 | Python 3.x |
| 프레임워크 | FastAPI |
| 서버 | Uvicorn |
| 데이터 검증 | Pydantic |
| 외부 통신 | httpx (비동기) |
| LLM | OpenAI API |
| (예정) RAG | ChromaDB |

## 📁 디렉터리 구조

```
ai-repo/
├── app/                          # 애플리케이션 핵심 코드
│   ├── main.py                   # FastAPI 진입점 (서버 시작점)
│   ├── config.py                 # 환경설정 (.env에서 API 키 로드)
│   ├── api/v1/                   # API 엔드포인트 (버전별 관리)
│   │   ├── router.py             # v1 라우터 통합
│   │   └── endpoints/
│   │       └── recommend.py      # POST /api/v1/recommend
│   ├── schemas/                  # 요청/응답 데이터 형식 정의 (Pydantic)
│   │   └── recommend.py
│   ├── services/                 # 비즈니스 로직 (오케스트레이션)
│   │   └── recommend_service.py  # 날씨+선호도 조합해 LLM 호출·정제
│   ├── clients/                  # 외부 API 래퍼
│   │   ├── weather_client.py     # 날씨 API 호출
│   │   ├── place_client.py       # 장소/관광지 API 호출
│   │   └── llm_client.py         # LLM API 호출
│   ├── rag/                      # (확장 예정) RAG 모듈
│   │   ├── embeddings.py         # 텍스트 → 벡터 변환
│   │   ├── vector_store.py       # 벡터 DB 연동
│   │   ├── ingest.py             # 문서 적재 파이프라인
│   │   └── retriever.py          # 질의 → 관련 문서 검색
│   └── core/                     # 공통 모듈
│       ├── prompts/
│       │   └── recommend.py      # 프롬프트 템플릿 관리
│       └── exceptions.py         # 예외 처리
├── data/                         # 데이터 저장소
│   ├── documents/                # RAG 원본 문서 보관
│   └── vector_db/                # 벡터 DB 저장소 (git에 올라가지 않음)
├── tests/                        # 테스트 코드
├── .env                          # 실제 API 키 (개인별 생성, 절대 커밋 금지)
├── .env.example                  # 환경변수 템플릿 (이걸 복사해서 .env 생성)
├── .gitignore
├── requirements.txt              # 의존성 목록
└── README.md
```

### 📌 계층 구조 설명
요청은 다음 순서로 처리됩니다:
[클라이언트] → api(엔드포인트) → services(로직) → clients(외부 API 호출) → 응답
- **api**: 어떤 URL로 요청을 받을지 정의
- **schemas**: 요청/응답이 어떤 형태여야 하는지 규정
- **services**: 실제 처리 흐름(날씨 가져오기 → 프롬프트 조립 → LLM 호출 → 결과 정제)
- **clients**: 외부 서비스(날씨/장소/LLM)와 통신하는 부분

---

## 🚀 시작하기 (팀원용 세팅 가이드)

### 1. 레포지토리 클론
```bash
git clone https://github.com/junggayeong/Ai.git
cd Ai
```

### 2. 가상환경 생성 및 활성화

**Windows (PowerShell)**
```powershell
python -m venv venv
venv\Scripts\activate
```
> ⚠️ 활성화 시 "스크립트를 실행할 수 없습니다" 오류가 나면 아래 실행 후 다시 시도:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
> ```

**Mac / Linux**
```bash
python3 -m venv venv
source venv/bin/activate
```

> ✅ 활성화되면 프롬프트 앞에 `(venv)`가 표시됩니다.

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. 환경변수 설정
`.env.example`을 복사해 `.env` 파일을 만들고, 각자 발급받은 API 키를 채워주세요.

**Windows**
```powershell
copy .env.example .env
```
**Mac / Linux**
```bash
cp .env.example .env
```

그 후 `.env` 파일을 열어 키를 입력합니다:
OPENAI_API_KEY=발급받은_키_입력

WEATHER_API_KEY=발급받은_키_입력

TOUR_API_KEY=발급받은_키_입력

> ⚠️ `.env`는 **절대 깃에 커밋하지 마세요.** (`.gitignore`에 등록되어 있습니다)

### 5. 서버 실행
```bash
uvicorn app.main:app --reload
```

실행 후 아래 메시지가 나오면 성공입니다:
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)

INFO:     Application startup complete.

### 6. API 문서 확인
브라우저에서 아래 주소로 접속하면 자동 생성된 API 문서를 볼 수 있습니다:
http://localhost:8000/docs

> 서버 종료: 터미널에서 `Ctrl + C`

---


### ⚠️ 주의사항
- **`.env` 파일은 절대 커밋하지 않기** (API 키 유출 위험)
- `venv/` 폴더는 깃에 올리지 않음 (각자 로컬에서 생성)
- 새 패키지 설치 시 `pip freeze > requirements.txt`로 갱신 후 커밋

---
