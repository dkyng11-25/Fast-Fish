# 🐟 FAST FISH 파이프라인 워크플로우 가이드

## 문서 인덱스 (Document Index)

이 문서는 FAST FISH 프로젝트의 전체 파이프라인 워크플로우를 설명합니다.
문서가 여러 파일로 분할되어 있으며, 아래 인덱스를 참조하세요.

---

## 📚 문서 구조

| 번호 | 파일명 | 설명 |
|------|--------|------|
| 01 | [01_PIPELINE_OVERVIEW.md](./01_PIPELINE_OVERVIEW.md) | 파이프라인 개요 및 전체 흐름도 |
| 02 | [02_STEP1_DATA_LOADING.md](./02_STEP1_DATA_LOADING.md) | Step 1: 데이터 로딩 상세 |
| 03 | [03_STEP2_COORDINATES.md](./03_STEP2_COORDINATES.md) | Step 2: 좌표 추출 상세 |
| 04 | [04_STEP3_MATRIX.md](./04_STEP3_MATRIX.md) | Step 3: 매트릭스 생성 상세 |
| 05 | [05_STEP4_5_CLUSTERING.md](./05_STEP4_5_CLUSTERING.md) | Step 4-5: 클러스터링 분석 상세 |
| 06 | [06_STEP6_7_RULES.md](./06_STEP6_7_RULES.md) | Step 6-7: 규칙 생성 및 시각화 상세 |
| 07 | [07_CLIENT_REQUIREMENTS.md](./07_CLIENT_REQUIREMENTS.md) | 고객 요구사항 추적 및 갭 분석 |
| 08 | [08_NEXT_STEPS.md](./08_NEXT_STEPS.md) | 다음 단계 권장사항 |

---

## 🔄 빠른 파이프라인 개요

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        FAST FISH 데이터 파이프라인                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  [Step 1]          [Step 2]           [Step 3]          [Step 4-5]         │
│  데이터 로딩   →   좌표 추출    →    매트릭스 생성  →   클러스터링          │
│  (Data Load)      (Coordinates)      (Matrix)          (Clustering)        │
│                                                                             │
│                                           ↓                                 │
│                                                                             │
│  [Step 6]          [Step 7]           [Output]                              │
│  규칙 생성    →   시각화 생성   →    최종 결과물                            │
│  (Rules)          (Visualization)    (Final Output)                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 프로젝트 구조

```
ProducMixClustering/
├── src/                          # 소스 코드
│   ├── step1_load_data.py        # 데이터 로딩
│   ├── step2_extract_coordinates.py  # 좌표 추출
│   ├── step3_create_matrix.py    # 매트릭스 생성
│   ├── step4_optimal_clusters.py # 최적 클러스터 수 결정
│   ├── step5_cluster_analysis.py # 클러스터 분석
│   ├── step6_cluster_analysis.py # 클러스터 분석 (확장)
│   ├── step7_generate_rules.py   # 규칙 생성
│   └── step8_visualize_rules.py  # 시각화
├── data/                         # 입력 데이터
├── output/                       # 출력 결과
├── docs/                         # 문서
│   └── workflow/                 # 워크플로우 문서
└── notes/                        # 회의록 및 메모
```

---

## 🚀 시작하기

1. **환경 설정**: Python 3.8+ 및 필요 패키지 설치
2. **데이터 준비**: `data/` 폴더에 입력 데이터 배치
3. **파이프라인 실행**: 각 Step을 순차적으로 실행

```bash
# 전체 파이프라인 실행 예시
python src/step1_load_data.py
python src/step2_extract_coordinates.py
python src/step3_create_matrix.py
python src/step4_optimal_clusters.py
python src/step5_cluster_analysis.py
python src/step6_cluster_analysis.py
python src/step7_generate_rules.py
python src/step8_visualize_rules.py
```

---

## 📅 문서 정보

- **생성일**: 2025-01-05
- **버전**: 1.0
- **작성자**: Data Pipeline Team
