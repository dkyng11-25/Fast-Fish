# 🤖 머신러닝 보완 필요 영역 상세 분석

**작성일:** 2025-01-06  
**대상:** ML 지식 보유 데이터 담당자  
**목적:** 프로젝트 내 ML 관련 개선 필요 영역 식별 및 개발 가이드

---

## 📋 목차

1. [현재 ML 구현 현황](#1-현재-ml-구현-현황)
2. [개선 필요 영역 (난이도별)](#2-개선-필요-영역)
3. [당신이 개발 가능한 ML 항목](#3-당신이-개발-가능한-ml-항목)
4. [구현 가이드 및 코드 예시](#4-구현-가이드)
5. [학습 리소스](#5-학습-리소스)

---

## 1. 현재 ML 구현 현황

### 1.1 이미 구현된 ML 컴포넌트

| 컴포넌트 | 위치 | 알고리즘 | 상태 |
|----------|------|----------|------|
| **PCA 차원 축소** | `step6_cluster_analysis.py` | sklearn.PCA | ✅ 완료 |
| **K-Means 클러스터링** | `step6_cluster_analysis.py` | sklearn.KMeans | ✅ 완료 |
| **클러스터 품질 메트릭** | `step6_cluster_analysis.py` | Silhouette, Calinski-Harabasz, Davies-Bouldin | ✅ 완료 |
| **상품 역할 분류** | `step25_product_role_classifier.py` | Rule-based (CORE/SEASONAL/FILLER/CLEARANCE) | ⚠️ 규칙 기반 |
| **최적화 엔진** | `step30_sellthrough_optimization_engine.py` | scipy.linprog, PuLP | ⚠️ 기초 구현 |

### 1.2 사용 중인 ML 라이브러리

```python
# 현재 사용 중
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
from scipy.optimize import linprog
from pulp import *

# 미사용 (향후 필요)
# from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
# from sklearn.model_selection import train_test_split, cross_val_score
# import xgboost as xgb
# import lightgbm as lgb
```

---

## 2. 개선 필요 영역

### 🟢 Level 1: 즉시 개발 가능 (당신의 현재 역량)

#### 2.1 클러스터링 품질 개선 (Silhouette ≥ 0.5)

**현재 문제:**
- 현재 Silhouette Score < 0.5 (고객 요구: ≥ 0.5)
- 피처 선택 최적화 필요

**필요 ML 지식:**
- Feature Selection (피처 중요도 분석)
- Hyperparameter Tuning (n_clusters, n_components)
- Elbow Method, Silhouette Analysis

**구현 위치:** `src/steps/cluster_analysis_step.py`

**개선 방법:**
```python
# 1. 최적 클러스터 수 탐색 (Elbow + Silhouette)
from sklearn.metrics import silhouette_score

def find_optimal_clusters(pca_df, k_range=(20, 60)):
    scores = []
    for k in range(k_range[0], k_range[1], 5):
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(pca_df)
        score = silhouette_score(pca_df, labels)
        scores.append((k, score))
    return max(scores, key=lambda x: x[1])

# 2. PCA 컴포넌트 수 최적화
def optimize_pca_components(normalized_df, variance_threshold=0.95):
    pca = PCA(n_components=None)
    pca.fit(normalized_df)
    cumsum = np.cumsum(pca.explained_variance_ratio_)
    n_components = np.argmax(cumsum >= variance_threshold) + 1
    return n_components
```

**예상 난이도:** ⭐⭐ (중간)  
**예상 시간:** 3-5일

---

#### 2.2 클러스터 안정성 분석 (Temporal Stability)

**현재 문제:**
- 시즌별 클러스터 멤버십 변화 추적 없음
- D-C Deliverable 미완료 (2/10 점수)

**필요 ML 지식:**
- Jaccard Similarity
- Cluster Membership Tracking
- Time Series Clustering Comparison

**구현 위치:** 신규 `src/steps/cluster_stability_step.py`

**개선 방법:**
```python
from sklearn.metrics import jaccard_score
import numpy as np

def calculate_cluster_stability(labels_t1, labels_t2, store_ids):
    """
    두 시점의 클러스터 멤버십 안정성 계산
    
    Returns:
        stability_score: 0-1 사이 값 (1 = 완전 안정)
    """
    # 같은 매장들만 비교
    common_stores = set(store_ids)
    
    # 클러스터별 Jaccard 유사도
    cluster_stabilities = []
    for cluster_id in np.unique(labels_t1):
        stores_t1 = set(store_ids[labels_t1 == cluster_id])
        
        # t2에서 가장 유사한 클러스터 찾기
        best_jaccard = 0
        for cluster_id_t2 in np.unique(labels_t2):
            stores_t2 = set(store_ids[labels_t2 == cluster_id_t2])
            jaccard = len(stores_t1 & stores_t2) / len(stores_t1 | stores_t2)
            best_jaccard = max(best_jaccard, jaccard)
        
        cluster_stabilities.append(best_jaccard)
    
    return np.mean(cluster_stabilities)

def flag_unstable_clusters(stability_scores, threshold=0.7):
    """안정성 임계값 미달 클러스터 플래그"""
    return [i for i, score in enumerate(stability_scores) if score < threshold]
```

**예상 난이도:** ⭐⭐ (중간)  
**예상 시간:** 2-3일

---

#### 2.3 매장 유형 분류 (Store Type Classification)

**현재 문제:**
- Fashion/Basic/Balanced 분류 없음
- 고객 요구사항 C-03 미완료

**필요 ML 지식:**
- Feature Engineering (판매 비율 계산)
- Threshold-based Classification
- (선택) K-Means for Store Segmentation

**구현 위치:** `src/steps/` 신규 또는 Step 1-3 확장

**개선 방법:**
```python
def classify_store_type(store_sales_df):
    """
    매장 유형 분류: Fashion / Basic / Balanced
    
    기준:
    - Fashion: 패션 상품 비율 > 60%
    - Basic: 기본 상품 비율 > 60%
    - Balanced: 그 외
    """
    # 패션 vs 기본 비율 계산
    fashion_ratio = store_sales_df.groupby('store_code').apply(
        lambda x: (x['style'] == 'fashion').sum() / len(x)
    )
    
    # 분류
    store_types = pd.Series(index=fashion_ratio.index, dtype=str)
    store_types[fashion_ratio > 0.6] = 'FASHION'
    store_types[fashion_ratio < 0.4] = 'BASIC'
    store_types[(fashion_ratio >= 0.4) & (fashion_ratio <= 0.6)] = 'BALANCED'
    
    return store_types
```

**예상 난이도:** ⭐ (쉬움)  
**예상 시간:** 1-2일

---

### 🟡 Level 2: 학습 후 개발 가능 (약간의 추가 학습 필요)

#### 2.4 상품 역할 분류 ML 버전

**현재 문제:**
- `step25_product_role_classifier.py`가 규칙 기반
- ML 기반 분류로 정확도 향상 가능

**필요 ML 지식:**
- Classification (Random Forest, XGBoost)
- Feature Engineering
- Cross-Validation
- Class Imbalance Handling

**개선 방법:**
```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import LabelEncoder

def train_product_role_classifier(sales_df, labeled_products):
    """
    ML 기반 상품 역할 분류기 학습
    
    Features:
    - total_sales: 총 판매액
    - sales_velocity: 판매 속도
    - store_coverage: 판매 매장 비율
    - seasonal_variance: 계절별 판매 변동
    - price_band: 가격대
    """
    # 피처 엔지니어링
    features = pd.DataFrame({
        'total_sales': sales_df.groupby('spu_code')['sales'].sum(),
        'avg_daily_sales': sales_df.groupby('spu_code')['sales'].mean(),
        'store_count': sales_df.groupby('spu_code')['store_code'].nunique(),
        'sales_std': sales_df.groupby('spu_code')['sales'].std(),
    })
    
    # 라벨 인코딩
    le = LabelEncoder()
    y = le.fit_transform(labeled_products['role'])
    
    # 모델 학습
    clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        class_weight='balanced',  # 클래스 불균형 처리
        random_state=42
    )
    
    # 교차 검증
    scores = cross_val_score(clf, features, y, cv=5, scoring='f1_weighted')
    print(f"Cross-validation F1 Score: {scores.mean():.3f} (+/- {scores.std():.3f})")
    
    clf.fit(features, y)
    return clf, le
```

**예상 난이도:** ⭐⭐⭐ (중상)  
**예상 시간:** 5-7일

---

#### 2.5 클러스터 프로파일링 자동화

**현재 문제:**
- 클러스터 설명이 기술적 (비즈니스 언어 부족)
- D-B Deliverable 개선 필요

**필요 ML 지식:**
- Cluster Interpretation
- Feature Importance per Cluster
- Statistical Profiling

**개선 방법:**
```python
def generate_cluster_profile(cluster_id, cluster_data, original_features):
    """
    클러스터별 비즈니스 프로파일 자동 생성
    """
    profile = {}
    
    # 1. 주요 특성 (평균 대비 차이)
    cluster_mean = cluster_data.mean()
    global_mean = original_features.mean()
    
    diff = (cluster_mean - global_mean) / global_mean
    
    # 상위 5개 특성
    top_features = diff.nlargest(5)
    bottom_features = diff.nsmallest(5)
    
    profile['dominant_features'] = top_features.to_dict()
    profile['weak_features'] = bottom_features.to_dict()
    
    # 2. 비즈니스 라벨 생성
    if cluster_data['temperature'].mean() > 25:
        profile['climate'] = '고온 지역'
    elif cluster_data['temperature'].mean() < 10:
        profile['climate'] = '저온 지역'
    else:
        profile['climate'] = '온대 지역'
    
    # 3. 추천 전략
    profile['strategy'] = generate_strategy_recommendation(profile)
    
    return profile
```

**예상 난이도:** ⭐⭐ (중간)  
**예상 시간:** 3-4일

---

### 🔴 Level 3: 전문 지식 필요 (협업 또는 심화 학습)

#### 2.6 수요 예측 모델 (Demand Forecasting)

**현재 문제:**
- 시계열 예측 모델 없음
- 고객 요구사항 C-13 미완료

**필요 ML 지식:**
- Time Series Analysis (ARIMA, Prophet, LSTM)
- Feature Engineering for Time Series
- Backtesting & Evaluation

**구현 복잡도:** 높음  
**권장:** ML Engineering 전문가 협업

```python
# 개념적 구조 (실제 구현은 복잡)
from prophet import Prophet
import pandas as pd

def train_demand_forecast(sales_history):
    """
    Prophet 기반 수요 예측
    """
    # Prophet 형식으로 변환
    df = sales_history.rename(columns={'date': 'ds', 'sales': 'y'})
    
    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False
    )
    
    model.fit(df)
    
    # 14일 예측
    future = model.make_future_dataframe(periods=14)
    forecast = model.predict(future)
    
    return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
```

**예상 난이도:** ⭐⭐⭐⭐⭐ (매우 높음)  
**예상 시간:** 2-4주

---

#### 2.7 MILP 최적화 엔진 고도화

**현재 문제:**
- `step30_sellthrough_optimization_engine.py` 기초 구현
- 실제 제약 조건 반영 부족

**필요 지식:**
- Operations Research
- Linear Programming / MILP
- Constraint Modeling

**현재 구현:**
```python
# step30에서 사용 중
OBJECTIVE_WEIGHTS = {
    'sell_through_rate': 0.70,
    'revenue_impact': 0.20,
    'inventory_turnover': 0.10
}

OPTIMIZATION_CONSTRAINTS = {
    'max_capacity_utilization': 0.85,
    'min_category_diversity': 3,
    'max_role_concentration': 0.60,
}
```

**권장:** Operations Research 전문가 협업

---

## 3. 당신이 개발 가능한 ML 항목

### 우선순위 1: 즉시 시작 가능

| 항목 | 관련 Step | 필요 지식 | 예상 시간 |
|------|-----------|-----------|-----------|
| **Silhouette ≥ 0.5 달성** | Step 4-6 | PCA, K-Means 튜닝 | 3-5일 |
| **매장 유형 분류** | Step 1-3 | Feature Engineering | 1-2일 |
| **클러스터 안정성 분석** | Step 6 이후 | Jaccard Similarity | 2-3일 |

### 우선순위 2: 학습 후 개발

| 항목 | 관련 Step | 필요 학습 | 예상 시간 |
|------|-----------|-----------|-----------|
| **상품 역할 ML 분류** | Step 25 | Random Forest, XGBoost | 5-7일 |
| **클러스터 프로파일 자동화** | Step 6 | Feature Importance | 3-4일 |
| **가격 탄력성 분석** | Step 26 | Regression | 4-5일 |

---

## 4. 구현 가이드

### 4.1 개발 환경 설정

```bash
# ML 라이브러리 설치
uv pip install scikit-learn xgboost lightgbm

# 시계열 분석 (선택)
uv pip install prophet statsmodels

# 최적화 (이미 설치됨)
uv pip install scipy pulp
```

### 4.2 코드 구조 권장

```
src/
├── steps/
│   ├── cluster_analysis_step.py      # 기존 (개선)
│   ├── cluster_stability_step.py     # 신규
│   └── store_type_classifier_step.py # 신규
├── components/
│   ├── ml/
│   │   ├── cluster_optimizer.py      # 클러스터 최적화
│   │   ├── product_role_classifier.py # ML 분류기
│   │   └── stability_analyzer.py     # 안정성 분석
│   └── ...
└── utils/
    └── ml_utils.py                   # ML 유틸리티
```

### 4.3 테스트 전략

```python
# tests/test_cluster_optimizer.py
import pytest
from src.components.ml.cluster_optimizer import find_optimal_clusters

def test_silhouette_improvement():
    """Silhouette score가 0.5 이상인지 검증"""
    # Given: 정규화된 매트릭스
    normalized_df = load_test_matrix()
    
    # When: 최적화 수행
    optimal_k, silhouette = find_optimal_clusters(normalized_df)
    
    # Then: 목표 달성
    assert silhouette >= 0.5, f"Silhouette {silhouette} < 0.5"
```

---

## 5. 학습 리소스

### 5.1 클러스터링 개선

- **Scikit-learn Clustering Guide**: https://scikit-learn.org/stable/modules/clustering.html
- **Silhouette Analysis**: https://scikit-learn.org/stable/auto_examples/cluster/plot_kmeans_silhouette_analysis.html
- **PCA Explained**: https://scikit-learn.org/stable/modules/decomposition.html#pca

### 5.2 분류 모델

- **Random Forest**: https://scikit-learn.org/stable/modules/ensemble.html#random-forests
- **XGBoost Tutorial**: https://xgboost.readthedocs.io/en/stable/tutorials/
- **Class Imbalance**: https://imbalanced-learn.org/stable/

### 5.3 시계열 (심화)

- **Prophet**: https://facebook.github.io/prophet/
- **Time Series with sklearn**: https://scikit-learn.org/stable/modules/cross_validation.html#time-series-split

---

## 6. 권장 실행 순서

```
Week 1: 매장 유형 분류 (1-2일) + 클러스터 안정성 분석 (2-3일)
        ↓
Week 2: Silhouette 개선 (3-5일)
        ↓
Week 3: 클러스터 프로파일 자동화 (3-4일)
        ↓
Week 4+: 상품 역할 ML 분류 (5-7일)
```

---

**문서 버전:** 1.0  
**다음 검토일:** 2025-01-13
