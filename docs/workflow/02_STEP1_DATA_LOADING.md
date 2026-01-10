# 📥 Step 1: 데이터 로딩 (Data Loading)

## 1. 개요 (Overview)

### 1.1 목적
원시 데이터 파일을 로드하고 파이프라인에서 사용할 수 있도록 정제합니다.

### 1.2 파일 위치
- **소스 코드**: `src/step1_load_data.py`
- **출력 위치**: `output/step1/`

---

## 2. 입력 (Input)

### 2.1 입력 데이터 형식

| 파일 유형 | 형식 | 필수 컬럼 |
|-----------|------|-----------|
| 매장 데이터 | CSV | store_id, store_name, location |
| 판매 데이터 | CSV | store_id, product_id, quantity, amount |
| 제품 마스터 | CSV | product_id, spu_id, category |

### 2.2 데이터 위치
```
data/
├── raw/
│   ├── stores.csv
│   ├── sales.csv
│   └── products.csv
```

---

## 3. 처리 로직 (Processing Logic)

### 3.1 처리 흐름도

```
┌─────────────────┐
│  원시 CSV 파일   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  1. 파일 읽기 (File Reading)          │
│  • pandas/fireducks로 CSV 로드       │
│  • 인코딩 자동 감지                   │
│  • 대용량 파일 청크 처리              │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  2. 데이터 검증 (Data Validation)     │
│  • 필수 컬럼 존재 확인                │
│  • 데이터 타입 검증                   │
│  • 중복 레코드 확인                   │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  3. 데이터 정제 (Data Cleaning)       │
│  • 결측치 처리                       │
│  • 타입 변환                         │
│  • 이상치 제거                       │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  4. 데이터 저장 (Data Persistence)    │
│  • 정제된 데이터 저장                 │
│  • 메타데이터 기록                   │
│  • 로그 출력                         │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────┐
│  정제된 데이터   │
└─────────────────┘
```

### 3.2 주요 함수

```python
def load_data(file_path: str) -> pd.DataFrame:
    """
    CSV 파일을 로드합니다.
    
    Args:
        file_path: CSV 파일 경로
        
    Returns:
        로드된 DataFrame
    """
    pass

def validate_data(df: pd.DataFrame, required_columns: List[str]) -> bool:
    """
    데이터 유효성을 검증합니다.
    
    Args:
        df: 검증할 DataFrame
        required_columns: 필수 컬럼 목록
        
    Returns:
        유효성 검증 결과
    """
    pass

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    데이터를 정제합니다.
    
    Args:
        df: 정제할 DataFrame
        
    Returns:
        정제된 DataFrame
    """
    pass
```

---

## 4. 출력 (Output)

### 4.1 출력 파일

| 파일명 | 형식 | 설명 |
|--------|------|------|
| `cleaned_stores.csv` | CSV | 정제된 매장 데이터 |
| `cleaned_sales.csv` | CSV | 정제된 판매 데이터 |
| `cleaned_products.csv` | CSV | 정제된 제품 데이터 |
| `load_metadata.json` | JSON | 로딩 메타데이터 |

### 4.2 메타데이터 구조

```json
{
    "load_timestamp": "2025-01-05T14:00:00",
    "files_processed": 3,
    "total_records": {
        "stores": 1000,
        "sales": 500000,
        "products": 5000
    },
    "validation_status": "passed",
    "processing_time_seconds": 45.2
}
```

---

## 5. 에러 처리 (Error Handling)

### 5.1 예상 에러

| 에러 유형 | 원인 | 처리 방법 |
|-----------|------|-----------|
| FileNotFoundError | 파일 경로 오류 | 에러 메시지 출력 후 종료 |
| EncodingError | 인코딩 불일치 | UTF-8, CP949 순차 시도 |
| ValidationError | 필수 컬럼 누락 | 누락 컬럼 명시 후 종료 |
| MemoryError | 대용량 파일 | 청크 처리로 전환 |

### 5.2 에러 로그 예시

```
[ERROR] 2025-01-05 14:00:00 - FileNotFoundError: data/raw/stores.csv not found
[ERROR] 2025-01-05 14:00:00 - ValidationError: Missing required columns: ['store_id', 'location']
```

---

## 6. 설정 (Configuration)

### 6.1 설정 파라미터

```python
# step1_load_data.py 설정
CONFIG = {
    "input_dir": "data/raw/",
    "output_dir": "output/step1/",
    "encoding": "utf-8",
    "chunk_size": 100000,  # 대용량 파일 청크 크기
    "required_columns": {
        "stores": ["store_id", "store_name", "location"],
        "sales": ["store_id", "product_id", "quantity"],
        "products": ["product_id", "spu_id", "category"]
    }
}
```

---

## 7. 실행 방법 (Execution)

### 7.1 명령어

```bash
# 기본 실행
python src/step1_load_data.py

# 특정 파일만 로드
python src/step1_load_data.py --file stores.csv

# 디버그 모드
python src/step1_load_data.py --debug
```

### 7.2 예상 출력

```
[INFO] Starting Step 1: Data Loading
[INFO] Loading stores.csv... 1000 records loaded
[INFO] Loading sales.csv... 500000 records loaded
[INFO] Loading products.csv... 5000 records loaded
[INFO] Validation passed for all files
[INFO] Cleaning data...
[INFO] Saving cleaned data to output/step1/
[INFO] Step 1 completed in 45.2 seconds
```

---

## 8. 다음 단계

- **다음**: [03_STEP2_COORDINATES.md](./03_STEP2_COORDINATES.md) - 좌표 추출
- **이전**: [01_PIPELINE_OVERVIEW.md](./01_PIPELINE_OVERVIEW.md) - 파이프라인 개요
