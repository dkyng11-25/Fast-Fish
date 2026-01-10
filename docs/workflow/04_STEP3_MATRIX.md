# 📊 Step 3: 매트릭스 생성 (Matrix Creation)

## 1. 개요 (Overview)

### 1.1 목적
매장-제품 관계를 나타내는 피처 매트릭스를 생성합니다. 클러스터링 분석의 입력 데이터로 사용됩니다.

### 1.2 파일 위치
- **소스 코드**: `src/step3_create_matrix.py`
- **출력 위치**: `output/step3/`

---

## 2. 매트릭스 유형 (Matrix Types)

### 2.1 지원 매트릭스

| 유형 | 설명 | 행 | 열 | 용도 |
|------|------|----|----|------|
| **SPU 매트릭스** | 개별 제품 레벨 | 매장 | SPU | 세분화 분석 |
| **카테고리 매트릭스** | 카테고리 레벨 | 매장 | 카테고리 | 거시적 분석 |
| **집계 매트릭스** | 카테고리 집계 SPU | 매장 | 집계 카테고리 | 균형 분석 |

### 2.2 매트릭스 구조

```
                    SPU_001  SPU_002  SPU_003  ...  SPU_N
Store_001           0.15     0.08     0.12     ...  0.05
Store_002           0.22     0.05     0.18     ...  0.03
Store_003           0.10     0.15     0.08     ...  0.07
...                 ...      ...      ...      ...  ...
Store_M             0.18     0.10     0.14     ...  0.04
```

---

## 3. 처리 로직 (Processing Logic)

### 3.1 처리 흐름도

```
┌─────────────────────────┐
│  Step 2 출력 데이터       │
│  (좌표 포함 매장 데이터)   │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────────────────┐
│  1. 데이터 병합 (Data Merge)          │
│  • 매장 데이터 + 판매 데이터           │
│  • 제품 마스터 조인                   │
│  • 키: store_id, product_id          │
└───────────┬─────────────────────────┘
            │
            ▼
┌─────────────────────────────────────┐
│  2. 집계 (Aggregation)               │
│  • 매장별 제품 판매량 집계            │
│  • 비율 계산 (정규화)                 │
│  • 결측치 0으로 채움                  │
└───────────┬─────────────────────────┘
            │
            ▼
┌─────────────────────────────────────┐
│  3. 피벗 (Pivot)                     │
│  • 행: 매장 (store_id)               │
│  • 열: 제품 (spu_id/category)        │
│  • 값: 판매 비율                      │
└───────────┬─────────────────────────┘
            │
            ▼
┌─────────────────────────────────────┐
│  4. 정규화 (Normalization)           │
│  • 행 합계 = 1.0 (비율 정규화)        │
│  • 또는 StandardScaler 적용          │
│  • 희소 행렬 처리                     │
└───────────┬─────────────────────────┘
            │
            ▼
┌─────────────────────────┐
│  피처 매트릭스 출력       │
└─────────────────────────┘
```

### 3.2 핵심 코드 로직

```python
def create_product_mix_matrix(
    sales_df: pd.DataFrame,
    level: str = "spu"  # "spu" or "category"
) -> pd.DataFrame:
    """
    제품 믹스 매트릭스를 생성합니다.
    
    Args:
        sales_df: 판매 데이터 DataFrame
        level: 집계 레벨 ("spu" 또는 "category")
        
    Returns:
        피벗된 매트릭스 DataFrame
    """
    # 집계 컬럼 결정
    group_col = "spu_id" if level == "spu" else "category"
    
    # 매장별 제품 판매량 집계
    agg_df = sales_df.groupby(
        ["store_id", group_col]
    )["quantity"].sum().reset_index()
    
    # 피벗 테이블 생성
    matrix = agg_df.pivot_table(
        index="store_id",
        columns=group_col,
        values="quantity",
        fill_value=0
    )
    
    # 비율 정규화 (행 합계 = 1)
    matrix = matrix.div(matrix.sum(axis=1), axis=0)
    
    return matrix
```

---

## 4. 입력 (Input)

### 4.1 필요 데이터

| 데이터 | 소스 | 필수 컬럼 |
|--------|------|-----------|
| 매장 데이터 | Step 2 | store_id, latitude, longitude |
| 판매 데이터 | Step 1 | store_id, product_id, quantity |
| 제품 마스터 | Step 1 | product_id, spu_id, category |

---

## 5. 출력 (Output)

### 5.1 출력 파일

| 파일명 | 형식 | 설명 |
|--------|------|------|
| `spu_matrix.csv` | CSV | SPU 레벨 매트릭스 |
| `category_matrix.csv` | CSV | 카테고리 레벨 매트릭스 |
| `matrix_metadata.json` | JSON | 매트릭스 메타데이터 |

### 5.2 메타데이터 구조

```json
{
    "matrix_type": "spu",
    "num_stores": 1000,
    "num_features": 500,
    "sparsity": 0.65,
    "normalization": "row_sum",
    "created_at": "2025-01-05T14:30:00",
    "processing_time_seconds": 120.5
}
```

---

## 6. 설정 (Configuration)

### 6.1 설정 파라미터

```python
# step3_create_matrix.py 설정
MATRIX_CONFIG = {
    "matrix_type": "spu",  # "spu", "category", "category_agg"
    "normalization": "row_sum",  # "row_sum", "standard", "minmax"
    "min_products_per_store": 5,  # 최소 제품 수 필터
    "top_n_spus": 100,  # 상위 N개 SPU만 사용 (선택적)
    "fill_value": 0,  # 결측치 채움 값
}
```

---

## 7. 성능 최적화 (Performance)

### 7.1 대용량 데이터 처리

```python
# 메모리 효율적 처리
def create_matrix_chunked(
    sales_df: pd.DataFrame,
    chunk_size: int = 10000
) -> pd.DataFrame:
    """
    청크 단위로 매트릭스를 생성합니다.
    대용량 데이터에 적합합니다.
    """
    store_ids = sales_df["store_id"].unique()
    chunks = np.array_split(store_ids, len(store_ids) // chunk_size + 1)
    
    matrices = []
    for chunk in tqdm(chunks, desc="Processing chunks"):
        chunk_df = sales_df[sales_df["store_id"].isin(chunk)]
        chunk_matrix = create_product_mix_matrix(chunk_df)
        matrices.append(chunk_matrix)
    
    return pd.concat(matrices)
```

### 7.2 희소 행렬 최적화

```python
from scipy.sparse import csr_matrix

def to_sparse_matrix(matrix: pd.DataFrame) -> csr_matrix:
    """
    희소 행렬로 변환하여 메모리 절약
    """
    return csr_matrix(matrix.values)
```

---

## 8. 실행 방법 (Execution)

### 8.1 명령어

```bash
# 기본 실행 (SPU 매트릭스)
python src/step3_create_matrix.py

# 카테고리 매트릭스 생성
python src/step3_create_matrix.py --type category

# 상위 100개 SPU만 사용
python src/step3_create_matrix.py --top-n 100
```

### 8.2 예상 출력

```
[INFO] Starting Step 3: Matrix Creation
[INFO] Loading data from Step 1 and Step 2 outputs
[INFO] Merging sales and product data...
[INFO] Creating SPU-level matrix...
[INFO]   - Stores: 1000
[INFO]   - SPUs: 500
[INFO]   - Sparsity: 65%
[INFO] Normalizing matrix (row_sum)...
[INFO] Saving matrix to output/step3/
[INFO] Step 3 completed in 120.5 seconds
```

---

## 9. 다음 단계

- **다음**: [05_STEP4_5_CLUSTERING.md](./05_STEP4_5_CLUSTERING.md) - 클러스터링 분석
- **이전**: [03_STEP2_COORDINATES.md](./03_STEP2_COORDINATES.md) - 좌표 추출
