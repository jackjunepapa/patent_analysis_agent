# Patent Analysis Agent

나의 발명(특허)과 선행 특허를 비교·분석하여 **차별화 방안**과 **회피·권리 강화 전략**을 수립하도록 돕는 AI 에이전트 웹 서비스입니다.

---

## AI 에이전트 정의

Patent Analysis Agent는 **일반 LLM 요약**에 머무르지 않고, 특허 명세서 안의 **기술적 연관 관계**를 구조적으로 파악하는 것을 전제로 합니다. **독립 청구항의 권리 범위**와 **상세한 설명·실시예**를 통합해 기술적 핵심(Core Idea)을 도출하고, **청구항 용어 ↔ 본문 단락·도면 부호**의 대응을 자동으로 연결해 **근거 중심 분석**의 토대를 마련합니다. 이 위에서 **구성요소별(Element-by-Element) 선행 대비**, **신규성·진보성 리스크**의 정량·정성 리포팅, **차별화 논리·청구 수정(Amendment) 방향**까지 제안하는 **실무 지향 에이전트**입니다.

**법률적 전문성의 방향:** 미국 **MPEP**와 한국 **KIPO** 심사 관행·지침을 **프롬프트 엔지니어링**에 반영하여, 심사·분쟁 맥락에 가깝게 질문하고 답하도록 설계합니다. (최종 출원·침해·무효 등 **법률 판단**은 등록 변리사·변호사 자문이 필요하며, 본 도구는 **보조 분석**에 해당합니다. 아래 [면책](#면책) 참고.)

---

## 개발 목표

단순 요약을 넘어, 명세서 전체를 **통합적으로 이해**하고 **선행과의 1:1 매핑**·**심사 기준에 근거한 리스크 진단**·**실행 가능한 전략**까지 연결하는 것이 핵심입니다.

### 1. 본 발명의 구조적 이해 및 가독성 최적화

| 방향 | 내용 |
|------|------|
| **통합적 발명 요약** | 독립 청구항의 권리 범위와 상세한 설명의 실시예를 결합하여 **기술적 핵심(Core Idea)**을 도출합니다. |
| **청구항–본문 유기적 매핑** | 청구항의 각 용어가 상세한 설명의 **어느 단락**, **어느 도면 부호**와 대응하는지 자동 연결하여, **근거 중심 분석**의 기반을 마련합니다. |

### 2. 선행 기술과의 심층 비교 (Element-by-Element Analysis)

특허 침해·등록 가능성 검토에서 쓰이는 **구성요소 대비** 방식을 AI 파이프라인으로 자동화하는 것을 목표로 합니다.

| 방향 | 내용 |
|------|------|
| **대비표(Mapping Table) 자동 생성** | 본 발명 청구항의 구성요소를 **분해(Decomposition)**하고, 각 요소가 선행 특허의 어느 부분에 개시되어 있는지 **1:1**로 매칭합니다. |
| **신규성·진보성 리스크 진단** | “비슷하다” 수준의 결론이 아니라, **KIPO(한국)** 및 **USPTO(미국)** 심사 지침에 근거하여 **동일 구성 존재 여부(신규성)**와 **결합의 용이성(진보성)** 관점에서 위험도를 **수치화·리포팅**합니다. |

### 3. 차별화 전략 및 권리 고도화 가이드 제공

분석 결과를 **실질적인 액션 플랜**으로 연결합니다.

| 방향 | 내용 |
|------|------|
| **특징적 유기적 결합 도출** | 개별 구성요소가 선행에 있더라도, 본 발명만의 **구성 간 결합 방식**·**특유의 효과**를 포착해 **진보성 주장 논리**를 생성합니다. |
| **전략적 청구항 재구성(Amendment Advice)** | 선행을 회피하면서도 가능한 한 넓은 권리 범위를 지향하는 **신규 청구항 초안** 및 **수사(Rhetoric)** 제안을 제공합니다. |

### 기대 효과 및 실무 활용

| 목표 영역 | 주요 가치 |
|-----------|-----------|
| **출원 전 단계** | 선행 조사로 거절 사유를 사전에 인지하고, **등록 가능성이 높은 청구** 방향으로 수정·보완하는 데 활용합니다. |
| **분쟁 대응 단계** | 타사 특허와의 차별을 논리적으로 구성해 **무효 심판·침해 소송** 등 방어 논리 수립에 활용합니다. |
| **R&D 전략 단계** | 경쟁사의 공백 기술 영역을 파악하고 **강한 특허망(Patent Mesh)** 구축 가이드로 활용합니다. |

---

## 주요 기능 명세

### 1. Hybrid Claim Chunking (특허 청구항 하이브리드 파싱)

특허 청구항은 일반 문서와 달리 **계층적 구조**를 가집니다. 단순 글자수 분할이 아닌 **논리 단위**로 분할하여 분석 효율을 높입니다.

| 영역 | 설명 |
|------|------|
| **독립항·종속항 추출** | 청구항 간 인용 관계를 분석하고 **트리 구조**로 정리합니다. |
| **구성요소 분리 (Element-wise Splitting)** | 각 청구항 내 개별 **구성요소(Element)**와 요소 간 **결합 관계**를 구조화·벡터화합니다. |

### 2. Intelligent RAG (Chroma DB)

| 영역 | 설명 |
|------|------|
| **Hybrid Search** | **키워드(BM25)** 검색과 **의미(Semantic)** 검색을 결합하여 유사 선행 특허를 정밀하게 필터링합니다. |
| **Contextual Retrieval** | 사용자 발명서에서 **기술적 특징(Technical Feature)**을 추출해 핵심 쿼리로 변환하여 검색 효율을 극대화합니다. |

### 3. 신규성 및 진보성 심층 분석

- **구성요소 대비 (Mapping)**: 나의 발명과 선행 기술의 구성요소를 **1:1**로 매칭합니다.
- **차별점 도출**: 선행에 없는 신규 구성요소, 또는 구성 간 **유기적 결합**의 차이를 식별합니다.
- **회피 설계 전략**: 차별점 분석을 바탕으로 침해 가능성을 낮추고 권리 범위를 강화하는 방향의 가이드를 제공합니다.

### 4. Comparison Table 자동 생성

- 사용자 발명과 **복수의 선행 특허**를 한눈에 비교할 수 있는 **마크다운** 기반 테이블을 생성합니다.
- 예시 항목: **구성요소**, 선행특허 A(일치 여부), 선행특허 B(일치 여부), **차별화 포인트**.

---

## 기술 스택 (계획)

| 구분 | 기술 |
|------|------|
| 프론트엔드 | Next.js, 스트리밍 UI |
| LLM·오케스트레이션 | LangChain |
| 벡터 DB | Chroma DB |
| 데이터 | 특허 PDF·텍스트 파서, 임베딩 파이프라인 |
| 참고 기준 | 미국 MPEP, 한국 KIPO 심사 가이드라인 반영 프롬프트 |

---

## 개발 로드맵

### Phase 1: 기반 인프라 및 특허 전용 파싱 엔진 구축 (1~2개월)

데이터 품질을 가장 먼저 좌우하는 **파싱(Parsing) 엔진**에 집중합니다. 아래는 **목표**와 저장소에 반영된 **구현**을 함께 정리한 것입니다.

- **특허 전문 OCR & Layout Parser**  
  - **목표**: 특허 **2단 편집**·**도면 부호**를 고려한 레이아웃 인지(예: [Unstructured.io](https://unstructured.io/), LayoutLM 계열).  
  - **구현**: `backend/patent_pdf_load.py` — PDF 업로드 시 **Unstructured** `partition_pdf`(strategy=`fast`)를 시도하고, 패키지 미설치·오류 시 **PyPDF**로 폴백합니다. (`patent_parse.load_text_from_uploaded`에서 사용.) **선택 설치**: `requirements-dev.txt` 주석 참고 — `pip install "unstructured[pdf]"`. OCR·LayoutLM·2단 전용 튜닝은 이후 확장 과제입니다.

- **Claim Tree & Element Parser**  
  - **목표**: 「제n항」·「Claim n」 인식, 독립·종속 **부모–자식 트리**, **`;` / wherein** 기반 구성요소 분해 및 **LLM 하이브리드**(정규식 시드 + LLM 정규화).  
  - **구현**: `backend/claim_tree.py` — `build_claim_tree`, `split_claim_elements_regex`(정규식·기존 `regex_split_claim_limitations` 연동). LLM 정규화는 Phase 2 `phase2_claim_structuring.py`와 연계합니다. 한국어 **`제n항.`** 처럼 항 번호 직후 마침표가 오는 경우에도 본문이 잘리도록 `patent_parse._kr_body_after_claim_label` 보강.

- **Vector DB (Chroma DB) 메타데이터**  
  - **목표**: 청크별 **독립항 여부**, **발명의 명칭**, **출원번호** 등을 필수 메타로 두어 **Contextual Retrieval** 기반 확보.  
  - **구현**: `patent_parse.extract_application_number`, `ParsedPatent.application_number`, `documents_from_parsed`에 **`application_number`**, **`claim_number`**, **`independent_claim`** 반영. `ingest_pipeline`의 `invention_claim1_meta`가 Phase 2로 **발명의 명칭·출원번호**를 넘기고, `build_phase2_preview_json` 산출 청크 메타에도 동일 필드를 넣습니다. 키 정의는 `chroma_schema.METADATA_KEYS`.

- **테스트**: `backend/tests/test_phase1_claim_tree.py`, `test_phase1_application_number.py`, `test_phase1_pdf_loader.py`, `test_phase1_documents_metadata.py` — `pytest tests`로 실행합니다.

### Phase 2: Intelligent RAG 및 구성요소 매핑 로직 (2~3개월) ✅

검색 품질을 높이고, **사용자 발명**과 **선행 문헌**을 근거 있는 단위로 잇는 단계입니다. 아래는 **목표**와 저장소에 반영된 **구현**을 함께 정리한 것입니다.

- **Hybrid Search Pipeline**  
  - **목표**: **BM25**로 도면 부호(예: 100, 200)·특정 기술 용어(예: 캐패시터)를 정밀히 짚고, **시맨틱 검색**으로 「잔상 제거를 위한 전압 보상」과 같이 **발명의 목적·효과(Effect)** 를 의미 단위로 찾습니다.  
  - **구현**: `retrieval.py` — Chroma **시맨틱 + BM25** 앙상블, 중복 제거 후 컨텍스트 조립. 인덱스 단계에서 `patent_parse.augment_chunk_for_bm25`로 **발명의 명칭·부호/도면 설명(REF_TERMS)** 등을 BM25 페이지에 붙여 도면 부호·용어 신호를 강화합니다.

- **청구 한계 단위 청킹 (Hybrid Chunking)**  
  - **목표**: 독립항을 **구성요소·한계(limitation)** 단위로 나누어 검색·매핑의 입력으로 씁니다.  
  - **구현**: `phase2_claim_structuring.py` — 관할(KR/US) 인지 구조화, 한계 단위 청크; `ingest_phase2_merge.py`로 베이스 인덱스와 병합. 선택 시 LLM 정규화(`use_llm_refine`).

- **Contextual Retrieval & 압축**  
  - **목표**: 청구·명세에서 뽑은 질의로 선행을 좁히고, 긴 히트는 요약해 분석에 넣습니다.  
  - **구현**: 독립 청구에서 **기술적 특징 쿼리**를 LLM으로 추출한 뒤 검색(`prompts_phase2.py`, `phase2_analysis.py`). 검색 결과 **Context Compression**(`prompts_phase2.py`).

- **Element-to-Description Mapping**  
  - **목표**: 청구 용어(예: 「보상용 캐패시터」)가 상세한 설명의 **어느 단락**(예: **[0045]** 문단)·근거와 연결되도록 추적해, 사용자에게 **인용(Citation)** 형태로 제시합니다.  
  - **구현**: 단락 번호·문단 ID를 메타로 고정 파싱하는 단계는 **로드맵**입니다. 현재는 검색·분석 단계에서 **청크·파일·한계 ID** 등 출처 메타를 넘겨 **근거 단서**로 활용합니다(전면 단락 매핑 UI는 확장 예정).

- **Comparison Engine (Step 2 목표)**  
  - **목표**: 업로드한 본 발명의 **각 구성요소를 쿼리로 변환**하고, 선행 특허의 대응 구간과 **1:1 매칭**하는 **프롬프트 체인**을 설계합니다.  
  - **구현**: 심층 비교·리포트는 `phase2_analysis.py` + `prompts_phase2.py`(MPEP·KIPO **참고 관점**, 비법적 판단 명시). Phase 3 `comparison_table.py`에서 **한계별·선행 파일별** 유사도 표(Markdown)로 1차 대응을 제공합니다. 완전한 Element↔선행 조각 **자동 1:1 표**는 고도화 과제입니다.

- **HTTP API**: FastAPI `backend/api.py` — 인덱스 빌드·동기/스트림 분석 등. Next.js와 버튼 연동(`web/`).

### Phase 3: 심층 분석 에이전트 및 비교 자동화 ✅

KIPO/MPEP **참고 톤**의 신규성·진보성 논의와 결과 표시를 한 단계로 묶습니다.

- **Comparison Table (Element-by-Element)**: `comparison_table.py` — 본 발명 한계(limitation)별로 선행 파일 **A, B, …** 열과 매칭 상태·**토큰 교집합 발췌**(근거 단서)를 Markdown 표로 출력합니다.
- **Reasoning Agent**: `prompts_phase3.REASONING_AGENT_PROMPT` — 심사 가이드라인을 참고한 **신규성·진보성 리스크**·차별 논점 Markdown 리포트 (`phase2_analysis.run_deep_analysis_llm` / SSE 1단계 스트림).
- **Strategy Generator**: `prompts_phase3.STRATEGY_GENERATOR_PROMPT` — 분석 초안과 검색 컨텍스트를 바탕으로 **청구 수정(Amendment) 초안·회피 설계** 불릿 (`run_deep_analysis_llm` 후반·SSE 2단계 스트림).
- **Streaming UI**: `POST /api/v1/analyze/stream` — `event: phase`로 단계 라벨 전송 후 `delta`에 `phase: reasoning | strategy`를 실어 **구간별 실시간** 표시. 웹(`PatentWorkspace.tsx`)은 Reasoning / Strategy 패널 이중 렌더.
- **DOCX / Next.js**: `phase3_export.py`, `NEXT_PUBLIC_API_BASE_URL` 등 기존과 동일. PDF 레이아웃·고급 파싱은 Phase 1 및 **Phase 4+** 로드맵과 연계.

**[Test 3] 백엔드 pytest**

- **Hallucination Check (휴리스틱)**: `phase3_verification.hallucination_quote_cross_check` — 분석문 내 큰따옴표 구절이 주어진 원문 합집합에 있는지 검사. `tests/test_phase3_verification_unit.py`.
- **Consistency**: 동일 입력에 대한 비교표 문자열 해시 안정성 — `comparison_table_consistency_hash`, 동일 테스트 파일.
- **대용량 청구 스트레스**: 종속항 **52개** 포함 KR 더미 명세 파싱 후 비교표 생성 완료 — `tests/test_phase3_stress_large_claims.py`. (실제 타임아웃은 리버스 프록시·클라이언트 설정에 따름.)

- PDF는 미포함(필요 시 Phase 4+에서 추가).

#### Phase 3 전체 테스트 (웹·API 비전문가용)

구현을 **손으로 끝까지 확인**할 때의 절차입니다. (**개발 단계 순서:** Phase 3 기능 검증 → 아래 수동 테스트 → 그다음 **Phase 4** 베타·Streamlit.)

이 서비스는 **프로그램 두 개**를 동시에 켜야 합니다. (① 백엔드 서버, ② 웹 화면)

##### 준비

- PC에 **Python**과 **Node.js**가 설치되어 있어야 합니다. (이미 개발 중이셨다면 설치되어 있습니다.)
- `patent analysis agent` 폴더 안에 **`.env`** 파일이 있고, 그 안에 **`OPENAI_API_KEY=`** 로 시작하는 키가 있어야 인덱스 빌드·분석이 됩니다.

##### ① 백엔드 켜기 (한 번만, 검은 창 유지)

1. 파일 탐색기에서  
   `바탕화면\KK\Vibe_coding\patent analysis agent\backend` 폴더로 이동합니다.
2. **`run_backend.bat`** 을 더블클릭합니다.  
   (또는 그 폴더에서 PowerShell을 연 뒤  
   `python -m uvicorn api:app --reload --host 127.0.0.1 --port 8000` 을 실행해도 됩니다.)
3. 창에 **`Application startup complete`** 또는 **`Uvicorn running`** 비슷한 글이 나오면 성공입니다. **이 창을 닫지 마세요.**

**브라우저에서 확인:** 주소창에 `http://127.0.0.1:8000/docs` 를 입력합니다.  
Swagger라는 **API 시험 화면**이 나오면 ①번 성공입니다.

##### ② 웹 화면 켜기 (새 창·새 터미널)

1. **새** PowerShell 또는 명령 프롬프트 창을 엽니다. (①번 창은 그대로 둡니다.)
2. 아래를 **한 줄씩** 입력하고 Enter 합니다.  
   (본인 PC 경로가 다르면 `C:\Users\jackp\...` 부분만 실제 경로로 바꿉니다.)

```powershell
cd "C:\Users\jackp\Desktop\KK\Vibe_coding\patent analysis agent\web"
npm install
npm run dev
```

**경로 주의:** 지금 터미널이 `...\patent analysis agent\backend` 안이면, 웹 폴더로 가려면 **`cd ..\web`** 만 입력합니다. (`cd patent analysis agent\web` 은 **오류**가 납니다.)

3. 터미널에 **`http://localhost:3000`** 주소가 나오면, 브라우저에 그 주소를 입력합니다.

##### ③ 웹에서 Phase 3 기능 끝까지 써보기

1. **한국어 / English** 중 원하는 쪽을 누릅니다.
2. **본 발명 파일**에서 특허 PDF 또는 TXT 등을 고릅니다.
3. **선행 문헌**에서 비교할 파일을 고릅니다.
4. **Build Search Index**를 누릅니다. 잠시 기다리면 아래에 **세션** 정보가 나옵니다.
5. **분석 실행**을 누릅니다. 왼쪽에 **비교 표**, 오른쪽에 **스트리밍 분석**이 나와야 정상입니다.
6. **DOCX로보내기**를 누르면 PC에 Word 파일이 받아집니다.

##### ④ Swagger(API 시험 화면)만 쓰고 싶을 때

- 메인 화면의 **「Swagger UI에서 API 테스트」** 링크를 누르거나, 주소창에 **`http://localhost:3000/api-test`** 를 입력합니다.
- **「새 탭에서 Swagger 열기」** 를 누르면 **①번에서 켠 서버**의 시험 화면(`http://127.0.0.1:8000/docs`)이 열립니다.

##### 자주 나는 문제

| 현상 | 점검 |
|------|------|
| Swagger가 안 열림 | ①번 백엔드 창이 켜져 있는지, 주소가 **`127.0.0.1:8000`** 인지 확인 |
| 웹에서 연결 오류 | ①번과 ②번을 **둘 다** 켰는지 확인 |
| `npm`이 `package.json`을 못 찾음 | 터미널이 **`...\web`** 폴더인지 확인 (`backend`가 아님) |

##### (선택) 자동 검사

`patent analysis agent` 폴더에서 **`run_tests.bat`** 또는 **`run_tests.ps1`** 을 실행하면 개발자용 테스트가 한 번에 돌아갑니다.

### Phase 4: 베타 완성 · Streamlit 배포 · 소규모 사용자 테스트

Phase 3까지의 파이프라인을 **베타 수준으로 완결**하고, **Streamlit**으로 배포한 뒤 **일부 사용자 테스트**를 거친 뒤 다음 라운드를 설계하는 단계입니다. 목표는 “기능을 무한히 늘리기”보다 **안전하게 동작하고, 피드백을 모을 수 있는 최소 기능(MVF)** 을 고정하는 것입니다.

**제품 범위:** 베타에서는 업로드 → 인덱스 빌드 → 분석(동기 또는 단순한 진행 표시) → 결과 확인 → DOCX(선택) 등 **이미 검증된 흐름**을 우선합니다. README 상 기존 Phase 4 후보였던 **추가 채팅·자유 질의** 등은 베타 직후가 아니라 **Phase 4+**에서 우선순위를 두고 넣기 쉽도록 구분합니다.

**Streamlit·아키텍처:** 가능하면 **기존 FastAPI 백엔드를 유지**하고 Streamlit은 **REST/SSE 클라이언트**로 두어, 이후 Next.js 웹과 **기능 동기화**와 유지보수 비용을 줄입니다. Streamlit에서 장시간 SSE를 그대로 붙이기 어려울 수 있으므로, 베타에서는 **진행 상태 + 최종 결과 갱신**, 또는 백엔드와 맞춘 **단순한 스트리밍 대안(예: 청크 폴링)** 등 현실적인 패턴을 우선합니다.

- **구현:** `streamlit_beta/app.py` — `/api/v1/index/build`(multipart), 동기 `/api/v1/analyze`, `/api/v1/export/docx/combined`. 실행은 **`run_streamlit.ps1`** 또는 **`run_streamlit.bat`** (먼저 백엔드 `:8000` 실행). 선택 환경 변수: **`PATENT_AGENT_API_BASE`**(기본 `http://127.0.0.1:8000`), **`STREAMLIT_FEEDBACK_URL`**(사이드바 피드백 버튼).

**실패 처리·운영:** 타임아웃, 빈 결과, API 키 한도, 과대 파일 등은 사용자에게 **이유가 드러나는 메시지**로 노출합니다. 배포 시 **Secrets·HTTPS·Rate limit** 등을 정리하고, 인메모리 세션 특성상 **재시작 시 세션 소실** 여부를 안내하거나 베타 한정으로 짧은 TTL의 **세션 영속화**를 검토합니다. 선택적으로 **익명 사용 로그**(세션 길이, 단계별 성공/실패, 파일 크기 구간 등)와 **피드백 링크·간단 설문**을 두어 테스트 의견을 수집합니다. 원문 명세·개인정보 저장 정책은 배포 전에 문서화합니다.

**검증:** 실제 등록 특허·거절 결정서 등을 활용한 **정확도·회귀 테스트**, 성능 튜닝, **보안·유출 방지** 관점의 데이터 처리(메모리 상 보관 시간, 로그 마스킹)를 병행합니다.

### Phase 4+: 사용자 피드백 반영 후 추가 개발

베타·소규모 테스트에서 나온 요구를 바탕으로 **우선순위를 재정렬**해 진행합니다. 전형적인 후보는 다음과 같습니다.

- **Follow-up 질의·채팅:** 분석 결과를 컨텍스트로 한 추가 질문, 특정 선행·청구만 깊게 보기.
- **근거·추적성(Grounding) 강화:** 출력에 단락·청크·파일 단위 인용을 일관되게 붙이고, UI에서 근거 확인이 가능하도록 확장.
- **DOCX·보고서 보강:** 본 발명 요약 포함, 템플릿·목차·면책 문구 등 내보내기 완성도.
- **정량 리스크 요약:** 신규성·진보성 위험을 한눈에 보는 지표·카드(규칙 기반 + 선택적 LLM 스코어).
- **세션·작업 영속화:** Redis/SQLite·Job 큐 등으로 재시작·장시간 분석에 대비.
- **파싱·PDF 품질:** 특정 PDF에서만 깨지는 사례가 많으면 OCR·레이아웃·2단 명세 파싱 우선순위 상승.

**한 줄 요약:** **Phase 4** = Streamlit 베타 배포 + MVF·오류·관측·배포 정리. **Phase 4+** = 피드백 기반으로 대화형 분석·근거·내보내기·지표·영속화·파싱을 순차 확장.

---

## 사용 방법

웹 UI(Next.js) 사용 순서입니다. 백엔드(uvicorn)가 실행 중이어야 합니다.

1. 답변 언어(한국어 / English) 선택
2. 본 발명 파일 업로드
3. 선행 문헌 파일 업로드 (KR/US 혼합 가능)
4. **Build Search Index** 클릭 → `session_id` 확보
5. **분석 실행** 클릭 → 비교 표 표시 후 SSE로 심층 분석 스트리밍
6. 필요 시 **DOCX로 내보내기** — 추가 채팅·자유 질의는 **Phase 4+** 확장 후보

---

## 디렉터리 구조 (Phase 1–2)

| 경로 | 설명 |
|------|------|
| `web/` | Next.js(App Router) UI — 언어 선택, 파일 업로드 영역, 인덱스·분석 버튼(플레이스홀더), 채팅 영역 |
| `backend/api.py` | FastAPI 엔드포인트 (인덱스 빌드·분석) |
| `backend/phase2_claim_structuring.py` | 청구항 구조 분석·하이브리드 청크(한계 단위) |
| `backend/ingest_phase2_merge.py` | Phase 2 청크 병합 및 Chroma 메타데이터 정규화 |
| `backend/retrieval.py` | 벡터 + BM25 앙상블 검색 |
| `backend/phase2_analysis.py` | 검색 → 압축 → 심층 분석 오케스트레이션 |
| `backend/prompts_phase2.py` | 기술 특징 추출·압축·MPEP/KIPO 톤 분석 프롬프트 |
| `backend/session_store.py` | 인메모리 세션 (개발용) |
| `backend/comparison_table.py` | 비교 표 Markdown 생성 |
| `backend/phase3_export.py` | DOCX 내보내기 |
| `backend/phase3_deep_analysis.py` | 토큰 유사도 등 비교 헬퍼 |
| `backend/tests/` | pytest — API·단위·(선택) OpenAI 통합 |
| `backend/requirements-dev.txt` | pytest 등 개발 의존성 |
| `backend/pytest.ini` | pytest 설정 |
| `run_tests.ps1`, `run_tests.bat` | 백엔드 pytest + 웹 `npm run test` 일괄 실행 |
| `backend/` | 기타: `config`, `patent_parse`, `ingest_pipeline`, `vector_store_chroma`, `chroma_schema`, 스모크 스크립트 |
| `.env.example` | 환경 변수 템플릿 (루트 `.env`에 복사 후 사용) |
| `.chroma_patent_analysis/` | Chroma 미설정 시 로컬 persist (gitignore) |

---

## 시작하기

### 요구 사항

- **Node.js** 20 이상 권장 (Next.js 16)
- **Python** 3.11–3.13 권장 (3.14는 일부 LangChain 의존성에서 경고가 날 수 있음)

#### Python 3.14와 `Pydantic v1` 경고 (LangChain)

uvicorn 실행 시 아래와 비슷한 **경고**가 나올 수 있습니다.

`Core Pydantic V1 functionality isn't compatible with Python 3.14 or greater`

- **의미:** LangChain 일부 코드가 아직 **Pydantic v1 호환 레이어**를 쓰는데, Python 3.14부터는 공식적으로 그 조합이 권장되지 않는다는 **안내용 경고**입니다. 대부분 **동작은 계속**됩니다.
- **권장 해결:** 이 프로젝트 전용으로 **Python 3.12 또는 3.13** 을 설치한 뒤, 가상환경(venv)을 만들어 그 안에서 `pip install`·`uvicorn`을 실행하세요. (가장 안정적입니다.)
- **설치 예 (Windows):** [python.org](https://www.python.org/downloads/) 에서 **3.12.x** Windows installer → 설치 시 **“Add python.exe to PATH”** 체크 → 새 터미널에서 `py -3.12 -m venv .venv` → `.\.venv\Scripts\activate` → `pip install -r backend/requirements.txt` 등.
- **임시로 경고만 줄이기:** 근본 해결은 아니며, `PYTHONWARNINGS=ignore` 로 숨길 수는 있으나 **버전 맞추는 편이 낫습니다.**

### 1) 환경 변수

루트에 `.env`를 두고 `.env.example`을 참고해 채웁니다. Phase 1·2에는 최소 **`OPENAI_API_KEY`**가 필요합니다(임베딩 + LLM). 선택적으로 **`OPENAI_MODEL`**(기본 `gpt-4o-mini`). Chroma Cloud를 쓰지 않으면 로컬 폴더 `.chroma_patent_analysis`에 자동 저장됩니다.

### 2) Python 백엔드

```bash
cd "patent analysis agent"
python -m pip install -r backend/requirements.txt
python backend/test_phase1_embedding.py
```

`OPENAI_API_KEY`가 없으면 테스트는 스킵 메시지 후 종료합니다. 키가 있으면 샘플 KR 텍스트 → 인제스트 → Chroma 적재 → 유사도 검색까지 수행합니다.

Phase 2 엔진 스모크(인덱스 + 하이브리드 검색 + LLM 분석):

```bash
python backend/test_phase2_smoke.py
```

### 3) Phase 2 API (FastAPI)

`backend` 폴더에서 uvicorn을 실행합니다.

**복사가 안 될 때:** 한 번에 세 줄을 붙여 넣으면, 일부 터미널·앱에서는 줄바꿈이 빠지거나 첫 줄만 실행되어 오류가 납니다. 아래 **방법 A**(스크립트) 또는 **방법 B**(세미콜론 한 줄)를 권장합니다.

**방법 A — 스크립트 (가장 단순)**

- 파일 탐색기에서 `patent analysis agent/backend/run_backend.bat` 더블클릭  
  또는 PowerShell에서:

```powershell
cd "...\Vibe_coding\patent analysis agent\backend"
.\run_backend.ps1
```

(`...\Vibe_coding`은 본인 PC의 저장소 경로로 바꿉니다. `run_backend.ps1`이 실행 거부되면 최초 1회 `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` 후 재시도.)

**방법 B — 저장소 루트에서 한 줄 (PowerShell 5.x 호환)**

```powershell
cd "patent analysis agent/backend"; python -m pip install -r requirements.txt; python -m uvicorn api:app --reload --host 127.0.0.1 --port 8000
```

**방법 C — 줄마다 따로 붙여 넣은 뒤 Enter**

1. `cd "patent analysis agent/backend"` Enter  
2. `python -m pip install -r requirements.txt` Enter  
3. `python -m uvicorn api:app --reload --host 127.0.0.1 --port 8000` Enter  

(항상 **`patent analysis agent`까지 포함한 경로**에서 `backend`로 들어가야 합니다. `Vibe_coding`만 연 상태에서 `cd backend` 하면 다른 폴더를 가리킵니다.)

- 문서 UI(Swagger): **http://127.0.0.1:8000/docs** — 브라우저에서 바로 열어 엔드포인트를 시험합니다. (`/` 로 접속하면 `/docs`로 리다이렉트됩니다.)
- Next.js 앱 실행 중일 때: **http://localhost:3000/api-test** 에서 안내·링크·Swagger 미리보기(iframe)를 제공합니다.
- `POST /api/v1/index/build`: multipart — 필드 `invention`(파일 여러 개), `prior`(파일 여러 개), 선택 `use_llm_refine`(bool). 응답에 `session_id` 포함.  
- `POST /api/v1/analyze`: JSON `{ "session_id": "...", "language": "ko" }` 또는 `"en"` — `analysis_markdown`, `comparison_table_markdown` 등 JSON.
- `POST /api/v1/analyze/stream`: 동일 JSON — SSE(`text/event-stream`), 먼저 `event: meta`에 비교표.
- `POST /api/v1/export/docx/combined`: `{ "analysis_markdown", "comparison_table_markdown", "language" }` — DOCX 다운로드.

### 4) Next.js 웹

`web/.env.local.example`을 참고해 `web/.env.local`에 API 주소를 넣을 수 있습니다(미설정 시 UI는 `http://127.0.0.1:8000` 사용).

```bash
cd "patent analysis agent/web"
npm install
npm run dev
```

백엔드(uvicorn)와 **동시에** 띄운 뒤, 웹에서 파일 업로드 → **Build Search Index** → **분석 실행** 순으로 사용합니다.

**경로 주의:** Next.js 앱은 저장소 최상위(`Vibe_coding`)의 `web`이 아니라 **`patent analysis agent/web`** 입니다. 상위 폴더에서 `cd web`만 하면 경로를 찾지 못합니다.

PowerShell 예시 — 저장소 루트(`...\Vibe_coding`)에서 바로 실행:

```powershell
cd "patent analysis agent/web"; npm install; npm run dev
```

이미 **`patent analysis agent`** 폴더 안이라면:

```powershell
cd web; npm run dev
```

PowerShell 5.x에서는 `&&` 대신 `;`를 사용합니다. PowerShell 7+ 또는 CMD에서는 `cd "patent analysis agent/web" && npm run dev` 형태도 가능합니다.

브라우저 UI는 Phase 3 기준으로 FastAPI와 연결되어 있습니다.

---

## 테스트

### 한 번에 실행

저장소 **`patent analysis agent`** 폴더에서:

```powershell
.\run_tests.ps1
```

또는 CMD:

```bat
run_tests.bat
```

(Python·npm이 PATH에 있어야 합니다.)

### Phase 3 개발 현황만 검증 (`-m phase3`)

비교표·Reasoning/Strategy 프롬프트·환각 검사·대용량 청구 스트레스·DOCX·(선택) OpenAI SSE를 한 번에 돌립니다.

저장소 **`patent analysis agent`** 폴더에서:

```powershell
.\run_phase3_tests.ps1
```

또는 CMD:

```bat
run_phase3_tests.bat
```

직접 pytest만 쓸 때:

```powershell
cd "patent analysis agent/backend"
python -m pip install -r requirements.txt -r requirements-dev.txt
python -m pytest tests -m phase3 -v --tb=short
```

- **키 없이 수행:** `phase3` 중 `test_integration_openai`는 **스킵**되고 나머지(비교표, `phase3_verification`, 스트레스, 프롬프트 스모크, DOCX)는 통과해야 합니다.
- **전체 Phase 3 라운드트립까지:** `patent analysis agent` 루트에 `.env`의 `OPENAI_API_KEY`를 두고 같은 명령을 실행하면 통합 테스트도 포함됩니다.

### 백엔드 (pytest — 전체)

```powershell
cd "patent analysis agent/backend"
python -m pip install -r requirements.txt -r requirements-dev.txt
python -m pytest tests -v --tb=short
```

- **키 없이 통과하는 항목:** 헬스체크, 리다이렉트, 비교표 단위 테스트, DOCX 내보내기, 인덱스/분석 오류 처리 등.
- **`OPENAI_API_KEY`가 필요한 항목:** `tests/test_integration_openai.py` — 인덱스 빌드 → 동기 분석 → SSE 라운드트립. 키가 없으면 **자동 스킵**됩니다. 루트 `.env`에 키가 있으면 `conftest`에서 로드합니다.

기존 스모크 스크립트도 그대로 사용할 수 있습니다.

```bash
python backend/test_phase1_embedding.py
python backend/test_phase2_smoke.py
```

### 프론트엔드

**경로 주의:** 이미 **`...\patent analysis agent\backend`** 안에 있다면 `patent analysis agent\web`으로 `cd` 하면 안 됩니다(`backend` 아래에 그런 폴더가 없음). 한 단계 올라가야 합니다.

- 저장소 루트 `...\patent analysis agent` 에서:

```powershell
cd web; npm run test
```

- 지금 위치가 `...\patent analysis agent\backend` 라면:

```powershell
cd ..\web; npm run test
```

- 저장소 최상위 `...\Vibe_coding` 에서라면:

```powershell
cd "patent analysis agent/web"; npm run test
```

현재는 **`eslint`(Lint)** 를 테스트 스크립트로 실행합니다. 빌드 검증은 `npm run build`.

---

## 면책

본 도구는 **법률 자문이 아닙니다**. 특허 출원·침해·회피 설계 등 최종 판단은 반드시 등록 변리사·변호사 등 전문가와 상담하시기 바랍니다.

---

## 라이선스

프로젝트 루트 정책에 따릅니다. (미정 시 추후 명시)
