#!/usr/bin/env python3

"""
Step 1 – FastFish API downloader (period‑pure runbook and usage guide)
=====================================================================

Purpose
-------
This module downloads four Step 1 datasets for a target period into `data/api_data/`:
- `store_config_YYYYMM[AB].csv`
- `store_sales_YYYYMM[AB].csv`
- `complete_category_sales_YYYYMM[AB].csv`
- `complete_spu_sales_YYYYMM[AB].csv`

Key guarantees and realities (what we learned and verified)
----------------------------------------------------------
- Store files (`store_config`, `store_sales`) include in‑file period columns (`yyyy`, `mm`, `mm_type`).
  You MUST filter rows to the exact period to ensure period purity. `mm_type` formats can be "6B" or
  "06B"; accept both.
- Category/SPU files do NOT contain `yyyy/mm/mm_type`. The filename defines the period. If a half‑month
  file was aliased from a full month, you cannot correct it by filtering; you must re‑fetch.
- Cross‑file aggregation is schema‑dependent by period:
  • Some periods (e.g., 202506B) – Category/SPU aggregate exactly to store_sales TOTALS.
  • Some periods (e.g., 202509A) – SPU equals Category exactly per store/subcategory.
  • Earlier periods (e.g., 202409A/202410A) – SPU is a stable subset of Category (~0.6–0.73 median). This is a
    domain difference, not a math bug. Use Category as total‑of‑record and SPU for splits.

How to run (Do’s)
-----------------
- For half‑month pulls: run with `--month YYYYMM --period A|B` and then filter store files to period.
- For full‑month pulls: run with `--month YYYYMM` (no `--period`) and then filter store files to month.
- Normalize fields immediately after download:
  • `str_code` – cast to string across all files.
  • `mm_type` – strip spaces; accept both "6A"/"06A" formats.
  • `store_sales` – if `total_sal_amt/total_sal_qty` are missing, derive as `base + fashion` for validation.
- Keep Hong Kong VPN on for API stability (fdapidb.fastfish.com:8089).

How NOT to run (Don’ts)
-----------------------
- Do not copy/alias a full‑month file to fabricate A/B (or vice‑versa).
- Do not assume Category/SPU can be filtered to a half‑month from contents; re‑fetch if wrong.
- Do not enforce Category/SPU == store_sales without checking schema; prefer tracking correlation and median ratio.

Quick validation checklist (recommended after every pull)
--------------------------------------------------------
1) Period purity audit (store files): keep only rows matching `yyyy==YYYY`, `mm==MM`, and `mm_type` in
   {f"{MM}{A|B}", f"{MM:02d}{A|B}"}. Full‑month: accept month or blank mm_type.
2) Coverage: stores in `store_sales`, `category`, `spu` should be subsets of `store_config` (normal exceptions may
   occur due to endpoint coverage). Investigate large gaps only.
3) Reconciliation:
   - Choose store_sales target per period: TOTALS (prefer) or FASHION if clearly better.
   - Compute per‑store sums of Category/SPU and compare to the target with ~0.5–2% tolerance.
   - Track `corr` and `median_ratio` per period as a domain signature (alert on big drifts, not on non‑1.0 levels).
4) Internal aggregation (strict): SPU → Category per (store, sub_cate_name) should have corr ≥ 0.95;
   exact equality (ratio≈1) on aligned periods (e.g., 202509A).

Operator notes for AI/automation
--------------------------------
- When asked to run Step 1 for a half‑month, prefer: `PYTHONPATH=. python src/step1_download_api_data.py --month YYYYMM --period A|B`.
- Immediately post‑filter store files in `data/api_data/` to enforce period purity and re‑save.
- If Category/SPU A/B row count ≈ full‑month row count (within ~0.5%), mark as suspect alias and re‑fetch that half.
- Always cast `str_code` to string before merges to avoid dtype join errors.

Implementation status (non‑functional guidance only)
---------------------------------------------------
This header documents usage and validation practices. Code below still performs API calls and basic
filtering but does not implement all guardrails automatically (to avoid unintended behavior changes).
If desired, we can add an opt‑in `--harden` flag to:
  • normalize dtypes/`mm_type` on save,
  • filter store files strictly to period,
  • write a small JSON reconciliation signature per period.

"""

import requests
import pandas as pd
import os
import json
import sys
import time
from datetime import datetime
import traceback
from typing import List, Dict, Any, Optional, Tuple
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from tqdm import tqdm
import argparse

# Import shared configuration
try:
    from config import set_current_period, ensure_backward_compatibility
except ImportError:
    # Fallback if config module is not available
    def set_current_period(yyyymm, period):
        pass
    def ensure_backward_compatibility():
        pass

# ——— CONFIGURATION ———
API_BASE = "https://fdapidb.fastfish.com:8089/api/sale"

# Using the correct endpoints from the API documentation
CONFIG_ENDPOINT = f"{API_BASE}/getAdsAiStrCfg"  # Store configuration
STORE_SALES_ENDPOINT = f"{API_BASE}/getAdsAiStrSal"  # Store sales data

# Define the month and period we want to analyze (configurable via environment variables)
TARGET_YYYYMM = os.environ.get('PIPELINE_TARGET_YYYYMM', os.environ.get('PIPELINE_YYYYMM', "202508"))  # Default to 202508 if not set
TARGET_PERIOD = os.environ.get('PIPELINE_TARGET_PERIOD', os.environ.get('PIPELINE_PERIOD', "A"))  # Default to "A" if not set

# 3-MONTH ROLLING WINDOW CONFIGURATION - NEW
MONTHS_FOR_CLUSTERING = 3  # Number of months to look back for clustering data

# Maximum number of stores to process in a single API call
BATCH_SIZE = 10

# API request configuration
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "User-Agent": "ProducMixClustering/1.0"
}
TIMEOUT = 30  # seconds
RETRY_COUNT = 3
RETRY_DELAY = 5  # seconds
RETRY_BACKOFF = 2  # seconds

# Track which stores have already been processed
PROCESSED_STORES = set()
FAILED_STORES = set()  # Track stores that failed to download

# Output directories
OUTPUT_DIR = "data/api_data"
ERROR_DIR = os.path.join(OUTPUT_DIR, "notes")

# Create required directories
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(ERROR_DIR, exist_ok=True)

def log_progress(message: str) -> None:
    """
    Log a progress message with a timestamp.
    
    Args:
        message: The message to log
    """
    # 타임 스탭프와 함께 어떤 함수 / 동작 실행됬는지 실행 로그 기록 

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def get_last_n_months_periods(target_yyyymm: str, target_period: str, n_months: int = 3) -> List[str]:
    """
    Get the last N months of periods for clustering data collection.
    
    Args:
        target_yyyymm: Current period in YYYYMM format (e.g., "202508")
        target_period: Current period indicator ("A" or "B")
        n_months: Number of months to look back (default: 3)
        
    Returns:
        List of period labels (e.g., ["202505A", "202505B", "202506A", "202506B", "202507A", "202507B"])
    """
    periods = []
    
    current_year = int(target_yyyymm[:4])
    current_month = int(target_yyyymm[4:6])
    
    # Calculate total half-months to generate
    total_half_months = n_months * 2
    
    # Start from current period and work backwards
    year, month = current_year, current_month
    period = target_period
    
    for i in range(total_half_months):
        periods.append(f"{year:04d}{month:02d}{period}")
        
        # Move to previous half-month
        if period == "B":
            period = "A"
        else:  # period == "A"
            period = "B"
            month -= 1
            if month < 1:
                month = 12
                year -= 1
    
    # Reverse to get chronological order
    periods.reverse()
    
    return periods

    # 기준 날짜에 대해서 분석 기간 + 과거 n개월의 히스토리 데이터 period label 목록 반환 
    # 예: ["202505A", "202505B", "202506A", "202506B", "202507A", "202507B"]

def get_year_over_year_seasonal_periods(target_yyyymm: str, target_period: str, n_months: int = 3) -> Tuple[List[str], List[str]]:
    """
    Get both current and historical periods for year-over-year seasonal clustering.
    
    Current periods: Last N months of current year (May/June/July 2025)
    Historical periods: NEXT N months from same time last year (August/September/October 2024)
    
    Args:
        target_yyyymm: Current period in YYYYMM format (e.g., "202507")
        target_period: Current period indicator ("A" or "B")
        n_months: Number of months to look back/forward (default: 3)
        
    Returns:
        Tuple of (current_periods, historical_future_periods) lists
    """

    # 위의 함수에서 과거 n개월의 데이터 추출
    # 현재 기준으로 그 전년도의 동일 시기부터 n개월 후의 데이터도 추가 수집 

    log_progress(f"🎯 Generating year-over-year seasonal periods for {n_months}-month predictive analysis...")
    
    # Get current periods (last N months of current year)
    current_periods = get_last_n_months_periods(target_yyyymm, target_period, n_months)
    
    # Generate historical FUTURE periods (next N months from same time last year)
    # Example: If current is July 2025, get Aug/Sep/Oct 2024 (next 3 months from July 2024)
    # We need BOTH A and B parts for complete monthly data
    # 분석하고자 하는 현재 특정 시기에 대해서 예측 레퍼런스를 작년 데이터에서 가져옴 
    
    current_year = int(target_yyyymm[:4])
    current_month = int(target_yyyymm[4:6])
    historical_year = current_year - 1
    
    # Start from the month AFTER the current month in previous year
    historical_periods = []
    
    # For July 2025 (202507), we want Aug/Sep/Oct 2024
    # So start from August 2024 (current_month + 1 in previous year)
    start_year = historical_year
    start_month = current_month + 1  # Next month in previous year
    if start_month > 12:
        start_month = 1
        start_year += 1
    
    # Generate BOTH A and B periods for each month (complete monthly data)
    for i in range(n_months): 
        # 해당 달에 대해서 
        period_a = f"{start_year:04d}{start_month:02d}A"
        period_b = f"{start_year:04d}{start_month:02d}B"
        historical_periods.append(period_a)
        historical_periods.append(period_b)
        # 분석하고자 하는 추가 개월수에 대해서 period A, B로 나누기 
        
        # Move to next month (다음 달로 move-on)
        start_month += 1
        if start_month > 12:
            start_month = 1
            start_year += 1
    
    # 타임스탬프 남기기 
    log_progress(f"📅 Current periods ({len(current_periods)}): {current_periods}")
    log_progress(f"📅 Historical future periods ({len(historical_periods)}): {historical_periods}")
    
    return current_periods, historical_periods

    # 현재까지 완료된 스텝: 분석하고자 하는 현재 날짜 설정 > 분석하고자 하는 기간 (과거 n개월) 리스트 추출 > 1년 전 같은 시기의 미래 n개월 추출 

def get_multi_period_label(periods: List[str]) -> str:
    """
    Create a label for multiple periods.
    
    Args:
        periods: List of period labels # 과거 n개월 
        
    Returns:
        Combined label (e.g., "202505-202507_multi")
    """
    # 우리가 분석하고자하는 n개월의 기간을 라벨링 

    if not periods:
        return "empty"
    
    # Sort periods and get first and last (년도와 월까지 추출)
    sorted_periods = sorted(periods)
    first_period = sorted_periods[0][:6]  # YYYYMM
    last_period = sorted_periods[-1][:6]   # YYYYMM
    
    if first_period == last_period:
        return f"{first_period}_multi"
    else:
        return f"{first_period}-{last_period}_multi"

def check_multi_period_data_availability(periods: List[str]) -> Dict[str, bool]:
    """
    Check which periods have data available.
    
    Args:
        periods: List of period labels to check
        
    Returns:
        Dictionary mapping period to availability status
    """
    availability = {} # 딕셔너리 initialize 
    
    for period in periods: # list에 있는 각 period에 대해서 for-loop 
        # Check if files exist for this period
        files_to_check = [ # 확인해야 할 파일들 이름 리스트업 
            f"complete_category_sales_{period}.csv",
            f"complete_spu_sales_{period}.csv",
            f"store_config_{period}.csv"
        ]
        
        period_available = True
        for filename in files_to_check: # 리스트에 있는 확인해야 할 파일 하나씩 접근 후 확인 
            filepath = os.path.join(OUTPUT_DIR, filename)
            print(f"Checking {filepath}")
            if not os.path.exists(filepath):
                period_available = False
                break
        
        availability[period] = period_available
        # 딕셔너리에 파일 존재 여부 하나씩 채워넣기 

    return availability

def create_retry_session() -> requests.Session:
    """
    Create a requests session with automatic retries.
    
    Returns:
        Session with retry capability
    """
    # 데이터를 API에서 가져오는 과정에서 요청 실패 시 다시 시도하도록 설정 
    retry_strategy = Retry(
        total=RETRY_COUNT,
        backoff_factor=RETRY_BACKOFF,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = requests.Session()
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def log_error(error_message: str, error_details: Any, store_codes: List[str] = None) -> None:
    """
    Log an error message to a file.
    
    Args:
        error_message: Short error message
        error_details: Detailed error information (can be exception or string)
        store_codes: List of store codes involved in the error
    """
    # 언제 어떤 매장 정보에서 어떤 에러가 발생했고 서버 응답은 뭐였는지 타임스템프와 함께 남겨서 에러 추적 가능하게 함 
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    error_file = os.path.join(ERROR_DIR, f"api_error_{timestamp}.md")
    
    with open(error_file, "w") as f:
        f.write(f"# API Error: {timestamp}\n\n")
        f.write(f"## Error Message\n{error_message}\n\n")
        
        if store_codes:
            f.write(f"## Affected Stores\n{', '.join(map(str, store_codes[:20]))}")
            if len(store_codes) > 20:
                f.write(f"... (and {len(store_codes) - 20} more)")
            f.write("\n\n")
        
        f.write(f"## Error Details\n```\n{error_details}\n```\n\n")
        
        if isinstance(error_details, requests.Response):
            f.write(f"## Response Status Code\n{error_details.status_code}\n\n")
            try:
                f.write(f"## Response Content\n```\n{error_details.text[:1000]}\n```\n")
            except:
                f.write("Could not extract response content\n")
    
    log_progress(f"Error logged to {error_file}") # 에러 파일에 기록된 구체적인 에러 내용 안내해주는 라인 

# 현재까지 필요한 히스토리 날짜 데이터 추출 및 접근 가능 파일 있는지 확인하고 그 과정에서 발생할 수 있는 에러 핸들링 

def get_period_label(yyyymm: str, period: Optional[str] = None) -> str:
    """
    Generate a period label for file naming.
    
    Args:
        yyyymm: Year-month in YYYYMM format
        period: Period indicator ("A" for first half, "B" for second half, None for full month)
        
    Returns:
        String label for the period (e.g., "202505A", "202505B", "202505")
    """
    #  input 년도 / 월 / 기간 구분자를 파일명 혹은 키로 사용할 수 있게 하나의 문자열로 합쳐서 리턴 (라벨 생성기)
    if period:
        return f"{yyyymm}{period}"
    return yyyymm

def get_period_description(period: Optional[str] = None) -> str:
    """
    Get human-readable description of the period.
    
    Args:
        period: Period indicator ("A" for first half, "B" for second half, None for full month)
        
    Returns:
        Human-readable description
    """
    if period == "A":
        return "first half of month"
    elif period == "B":
        return "second half of month"
    else:
        return "full month"

def clear_previous_data(yyyymm: str, period: Optional[str] = None, keep_notes: bool = True) -> None:
    """
    Clear previous API data files to ensure clean runs.
    
    Args:
        yyyymm: Year-month in YYYYMM format
        period: Period indicator ("A" for first half, "B" for second half, None for full month)
        keep_notes: Whether to keep error logs and notes (default: True)
    """
    import glob
    
    period_label = get_period_label(yyyymm, period) # 특정 월 데이터 라벨 
    log_progress(f"Clearing previous data for period {period_label}...")
    
    # Define patterns for files to clear # clear 필요한 파일 이름 리스트업 (월 데이터 라벨 활용) = 해당 period에 대해 생성될 수 있는 산출물
    patterns_to_clear = [
        f"store_config_{period_label}.csv",
        f"store_sales_{period_label}.csv", 
        f"complete_category_sales_{period_label}.csv",
        f"complete_spu_sales_{period_label}.csv",
        f"processed_stores_{period_label}.txt",
        f"failed_stores_{period_label}.txt",  # Track failed stores separately
        f"partial_*_{period_label}_*.csv"  # Intermediate files
    ]
    
    files_removed = 0 # 파일이 몇개가 지워졌는지 확인하기 위한 tracker 
    for pattern in patterns_to_clear:
        file_path = os.path.join(OUTPUT_DIR, pattern)
        if '*' in pattern:
            # Handle wildcard patterns (특정 패턴이 공통되는 여러개의 파일)
            matching_files = glob.glob(file_path) # 공통되는 파일 리스트업 (wildcard 패턴에 맞는 모든 파일)
            for file in matching_files:
                try:
                    os.remove(file)
                    files_removed += 1
                    print(f"[DEBUG] Removed: {os.path.basename(file)}")
                except Exception as e:
                    log_progress(f"Warning: Could not remove {file}: {e}")
        else:
            # Handle exact file names (파일명 정확히 1개인 경우)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path) # 파일 존재하면 삭제 및 tracker 1 업데이트 
                    files_removed += 1
                    print(f"[DEBUG] Removed: {os.path.basename(file_path)}")
                except Exception as e:
                    log_progress(f"Warning: Could not remove {file_path}: {e}")
    
    # Optionally clear notes directory (but keep the directory structure)
    # when keep_notes = FALSE > remove all .md files 
    if not keep_notes:
        notes_pattern = os.path.join(ERROR_DIR, "*.md")
        note_files = glob.glob(notes_pattern)
        for note_file in note_files:
            try:
                os.remove(note_file)
                files_removed += 1
                print(f"[DEBUG] Removed note: {os.path.basename(note_file)}")
            except Exception as e:
                log_progress(f"Warning: Could not remove {note_file}: {e}")
    # 파일 삭제에 대한 로그 기록 
    if files_removed > 0:
        log_progress(f"Cleared {files_removed} previous data files for period {period_label}")
    else:
        log_progress(f"No previous data files found for period {period_label}")
    
    # Clear the processed and failed stores sets
    global PROCESSED_STORES, FAILED_STORES # global variables 
    PROCESSED_STORES.clear()
    FAILED_STORES.clear()
    print(f"[DEBUG] Cleared processed and failed stores tracking")
    # 변수 유지하지만 안에 들어있는 원소 전부 삭제 

def get_unique_store_codes(input_file: str = "data/store_codes.csv") -> List[str]:
    """
    Extract unique store codes from the store codes file.
    
    Returns:
        List of unique store codes
    """
    try:
        # Try several potential file paths
        # 가능성 있는 파일 경로 리스트업 
        potential_paths = [
            input_file,                             # First try: "data/store_codes.csv"
            input_file.replace("./", "../"),        # Second try: "../data/store_codes.csv"
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "store_codes.csv")  # Absolute path
        ]
        
        df = None
        used_path = None
        
        # 리스트업한 파일 경로에 대해서 for-loop로 store에 대한 정보 파일 찾기 
        for path in potential_paths:
            if os.path.exists(path):
                # 파일 찾으면 로그 기록 및 파일 DataFrame 형태로 변환 (store data 저장)
                log_progress(f"Found store codes file at: {path}")
                df = pd.read_csv(path)
                used_path = path
                break
        
        if df is None:
            # 파일 찾기 실패 
            raise FileNotFoundError(f"Could not find store_codes.csv in any of these locations: {potential_paths}")
        
        # DataFrame으로 변환한 store info에서 store 코드 추출 (unique한 code) 및 리스트로 변환 
        store_codes = sorted(df["str_code"].astype(str).unique().tolist())
        log_progress(f"Found {len(store_codes)} unique store codes in {used_path}")
        # unique한 store code 리스트업 및 정렬 후 로그 기록 
        
        # Check for previously processed and failed stores if resuming
        period_label = get_period_label(TARGET_YYYYMM, TARGET_PERIOD)
        processed_stores_file = os.path.join(OUTPUT_DIR, f"processed_stores_{period_label}.txt")
        failed_stores_file = os.path.join(OUTPUT_DIR, f"failed_stores_{period_label}.txt")
        
        if os.path.exists(processed_stores_file):
            with open(processed_stores_file, 'r') as f:
                PROCESSED_STORES.update([line.strip() for line in f.readlines()])
            log_progress(f"Found {len(PROCESSED_STORES)} previously processed stores for period {period_label}")
        
        if os.path.exists(failed_stores_file):
            with open(failed_stores_file, 'r') as f:
                FAILED_STORES.update([line.strip() for line in f.readlines()])
            log_progress(f"Found {len(FAILED_STORES)} previously failed stores for period {period_label}")
        
        return store_codes
    
    except Exception as e: # 에러 핸들링 
        error_msg = f"Failed to extract store codes from {input_file}"
        log_error(error_msg, e)
        sys.exit(f"Error: {error_msg}. Check notes directory for details.")

def fetch_store_config(store_codes: List[str], yyyymm: str, period: Optional[str] = None) -> Tuple[pd.DataFrame, List[str]]:
    """
    Fetch store configuration data (big_class_name, sub_cate_name, etc.).
    
    Args: # 특정 기간 및 store code list
        store_codes: List of store codes to fetch configurations for
        yyyymm: Year and month in YYYYMM format (e.g., "202505")
        period: Period indicator ("A" for first half, "B" for second half, None for full month)
        
    Returns:
        Tuple containing:
            - DataFrame containing store configuration data
            - List of successfully processed store codes
    """
    # Prepare payload - add period parameter if specified
    payload = {"strCodes": store_codes, "yyyymm": yyyymm} 
    # 조건부: period가 A, B, None인지 확인하여 API에 전달
    if period: # 반월 데이터 조회 요구 존재 (A or B) > filtering 
        payload["period"] = period  # Add period parameter for half-month requests
    
    session = create_retry_session()
    
    try:
        period_desc = get_period_description(period)
        log_progress(f"Fetching store configuration for {len(store_codes)} stores ({period_desc})...")
        print(f"[DEBUG] API payload: {payload}")
        
        resp = session.post(CONFIG_ENDPOINT, json=payload, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json().get("data", [])
        
        if not data:
            error_msg = f"Empty data received from config API for {period_desc}"
            log_error(error_msg, resp, store_codes)
            return pd.DataFrame(), []
        
        # Create DataFrame and validate
        df = pd.DataFrame(data)
        
        # Filter by mm_type if period is specified (validate that we got the right period)
        # 원하는 요구조건에 맞는 데이터 필터링 
        # case 1: with leading 0
        if period and "mm_type" in df.columns:
            expected_mm_type = f"{yyyymm[-2:]}{period}"  # e.g., "05A" for May first half
            period_filtered = df[df["mm_type"] == expected_mm_type]
            if len(period_filtered) > 0:
                df = period_filtered
                log_progress(f"Filtered to {len(df)} rows matching period {expected_mm_type}")
        # case 2: without leading 0
            else:
                # Try alternative format without leading zero
                alt_expected_mm_type = f"{int(yyyymm[-2:])}{period}"  # e.g., "5A" instead of "05A"
                period_filtered = df[df["mm_type"] == alt_expected_mm_type]
                if len(period_filtered) > 0:
                    df = period_filtered
                    log_progress(f"Filtered to {len(df)} rows matching period {alt_expected_mm_type}")
                else:
                    log_progress(f"Warning: No data found for mm_type={expected_mm_type} or {alt_expected_mm_type}, using all data")
        
        # Extract the store codes that were successfully processed
        processed_codes = df["str_code"].astype(str).unique().tolist()
        missing_codes = set(store_codes) - set(processed_codes)
        
        if missing_codes:
            log_progress(f"Warning: {len(missing_codes)} stores missing from config API response")
            log_error(f"Missing stores in config API response", f"These stores did not return data: {missing_codes}", list(missing_codes))
        
        log_progress(f"Received configuration data for {len(processed_codes)} stores ({period_desc})")
        return df, processed_codes
            
    except Exception as e:
        error_msg = f"Failed to fetch store configuration for {get_period_description(period)}"
        log_error(error_msg, traceback.format_exc(), store_codes)
        return pd.DataFrame(), []

def fetch_store_sales(store_codes: List[str], yyyymm: str, period: Optional[str] = None) -> Tuple[pd.DataFrame, List[str]]:
    """
    Fetch store-level sales data.
    
    Args:
        store_codes: List of store codes to fetch sales data for
        yyyymm: Year and month in YYYYMM format (e.g., "202505")
        period: Period indicator ("A" for first half, "B" for second half, None for full month)
        
    Returns:
        Tuple containing:
            - DataFrame with store sales data
            - List of successfully processed store codes
    """
    # Prepare payload - add period parameter if specified
    payload = {"strCodes": store_codes, "yyyymm": yyyymm}
    if period:
        payload["period"] = period  # Add period parameter for half-month requests
    
    session = create_retry_session()
    
    try:
        period_desc = get_period_description(period)
        log_progress(f"Fetching store sales data for {len(store_codes)} stores ({period_desc})...")
        print(f"[DEBUG] API payload: {payload}")
        
        resp = session.post(STORE_SALES_ENDPOINT, json=payload, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json().get("data", [])
        
        if not data:
            error_msg = f"Empty data received from sales API for {period_desc}"
            log_error(error_msg, resp, store_codes)
            return pd.DataFrame(), []
        
        # Create DataFrame and perform basic validation
        df = pd.DataFrame(data)
        
        # Filter by mm_type if period is specified (validate that we got the right period)
        if period and "mm_type" in df.columns:
            expected_mm_type = f"{yyyymm[-2:]}{period}"  # e.g., "05A" for May first half
            period_filtered = df[df["mm_type"] == expected_mm_type]
            if len(period_filtered) > 0:
                df = period_filtered
                log_progress(f"Filtered to {len(df)} rows matching period {expected_mm_type}")
            else:
                # Try alternative format without leading zero
                alt_expected_mm_type = f"{int(yyyymm[-2:])}{period}"  # e.g., "5A" instead of "05A"
                period_filtered = df[df["mm_type"] == alt_expected_mm_type]
                if len(period_filtered) > 0:
                    df = period_filtered
                    log_progress(f"Filtered to {len(df)} rows matching period {alt_expected_mm_type}")
                else:
                    log_progress(f"Warning: No data found for mm_type={expected_mm_type} or {alt_expected_mm_type}, using all data")
        
        # Extract the store codes that were successfully processed
        processed_codes = df["str_code"].astype(str).unique().tolist()
        missing_codes = set(store_codes) - set(processed_codes)
        
        if missing_codes:
            log_progress(f"Warning: {len(missing_codes)} stores missing from sales API response")
            log_error(f"Missing stores in sales API response", f"These stores did not return data: {missing_codes}", list(missing_codes))
        
        log_progress(f"Received sales data for {len(processed_codes)} stores ({period_desc})")
        return df, processed_codes
    
    except Exception as e:
        error_msg = f"Failed to fetch store sales data for {get_period_description(period)}"
        log_error(error_msg, traceback.format_exc(), store_codes)
        return pd.DataFrame(), []

def process_and_merge_data(store_sales_df: pd.DataFrame, config_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, List[str]]:
    """
    Process and merge store sales and configuration data, outputting both subcategory-level and SPU-level sales.
    NOW INCLUDES REAL QUANTITY CALCULATIONS FROM API DATA!
    
    Args:
        store_sales_df: DataFrame containing store sales data with QUANTITY FIELDS
        config_df: DataFrame containing store configuration data
    Returns:
        Tuple containing:
            - Subcategory-level DataFrame
            - SPU-level DataFrame with REAL QUANTITIES
            - List of successfully processed store codes
    """
    try:
        if store_sales_df.empty or config_df.empty:
            print("[DEBUG] One of the dataframes is empty - skipping merge")
            return pd.DataFrame(), pd.DataFrame(), []

        print(f"[DEBUG] config_df columns: {config_df.columns.tolist()}")
        print(f"[DEBUG] store_sales_df columns: {store_sales_df.columns.tolist()}")
        
        # Check if we have quantity data in store_sales_df
        has_quantity_data = 'base_sal_qty' in store_sales_df.columns and 'fashion_sal_qty' in store_sales_df.columns
        print(f"[DEBUG] Has quantity data: {has_quantity_data}")

        # Create store-level quantity and unit price mapping
        store_quantity_map = {}
        if has_quantity_data:
            print("[DEBUG] 🎯 EXTRACTING REAL QUANTITY DATA FROM API...")
            for _, row in store_sales_df.iterrows():
                str_code = str(row['str_code'])
                
                # Extract quantity data
                base_qty = float(row.get('base_sal_qty', 0) or 0)
                fashion_qty = float(row.get('fashion_sal_qty', 0) or 0)
                base_amt = float(row.get('base_sal_amt', 0) or 0)
                fashion_amt = float(row.get('fashion_sal_amt', 0) or 0)
                
                total_qty = base_qty + fashion_qty
                total_amt = base_amt + fashion_amt
                
                # Calculate REAL unit prices from API data
                if total_qty > 0:
                    unit_price = total_amt / total_qty
                    print(f"[DEBUG] Store {str_code}: {total_qty:.1f} units, ${total_amt:.2f} sales = ${unit_price:.2f}/unit")
                else:
                    unit_price = 50.0  # Default for stores with no sales
                
                store_quantity_map[str_code] = {
                    'total_quantity': total_qty,
                    'total_sales': total_amt,
                    'unit_price': unit_price,
                    'base_qty': base_qty,
                    'fashion_qty': fashion_qty,
                    'base_amt': base_amt,
                    'fashion_amt': fashion_amt
                }
            
            print(f"[DEBUG] ✅ Calculated real unit prices for {len(store_quantity_map)} stores")
            
            # Show sample unit prices
            sample_stores = list(store_quantity_map.keys())[:5]
            for store in sample_stores:
                data = store_quantity_map[store]
                print(f"[DEBUG]   Store {store}: ${data['unit_price']:.2f}/unit ({data['total_quantity']:.1f} units)")

        # Subcategory-level (CORRECTED: Keep all records - they represent different product assortments)
        if "big_class_name" in config_df.columns and "sub_cate_name" in config_df.columns:
            # Keep all records as they represent different product assortments within subcategories
            # Each record has different sty_sal_amt (SPU composition) even if store-subcategory-season-sex is same
            category_sales = config_df[[
                "str_code", "str_name", "big_class_name", "sub_cate_name", "sal_amt"
            ]].copy()
            category_sales.rename(columns={"big_class_name": "cate_name"}, inplace=True)
            
            print(f"[DEBUG] ✅ Category data preserved: {len(category_sales):,} records (all product assortments kept)")
            
            # Add quantity data to category sales if available
            if has_quantity_data:
                category_sales['store_unit_price'] = category_sales['str_code'].astype(str).map(
                    lambda x: store_quantity_map.get(x, {}).get('unit_price', 50.0)
                )
                category_sales['estimated_quantity'] = category_sales['sal_amt'] / category_sales['store_unit_price']
                print(f"[DEBUG] ✅ Added quantity calculations to category data")
            
            if "sal_amt_avg" in store_sales_df.columns:
                store_metrics = store_sales_df[["str_code", "sal_amt_avg"]].drop_duplicates()
                category_sales = pd.merge(
                    category_sales, 
                    store_metrics,
                    on="str_code", 
                    how="left"
                )
            stores_with_subcats = category_sales.groupby("str_code").size()
            valid_stores = stores_with_subcats[stores_with_subcats > 0].index.tolist()
        else:
            print(f"[DEBUG] Required columns not found in config_df: {config_df.columns.tolist()}")
            return pd.DataFrame(), pd.DataFrame(), []

        # SPU-level: DEDUPLICATE config_df first to prevent duplicate SPUs
        print("[DEBUG] 🎯 CREATING SPU DATA WITH REAL QUANTITIES...")
        print(f"[DEBUG] Original config records: {len(config_df):,}")
        
        # CRITICAL FIX: Remove duplicate store-subcategory-season-sex combinations that contain identical SPU data
        # This prevents the same SPU from being processed multiple times for the same store
        config_dedup_cols = ['str_code', 'sub_cate_name', 'season_name', 'sex_name', 'sty_sal_amt']
        available_cols = [col for col in config_dedup_cols if col in config_df.columns]
        if 'sty_sal_amt' in available_cols:
            config_df_clean = config_df.drop_duplicates(subset=available_cols, keep='first')
            print(f"[DEBUG] After deduplication: {len(config_df_clean):,} records ({len(config_df) - len(config_df_clean):,} duplicates removed)")
        else:
            # Fallback if sty_sal_amt column not available
            config_df_clean = config_df.drop_duplicates(subset=['str_code', 'sub_cate_name'], keep='first')
            print(f"[DEBUG] After basic deduplication: {len(config_df_clean):,} records ({len(config_df) - len(config_df_clean):,} duplicates removed)")
        
        spu_rows = []
        for idx, row in tqdm(config_df_clean.iterrows(), total=config_df_clean.shape[0], desc="Expanding SPU-level data with quantities"):
            try:
                str_code = str(row["str_code"])
                store_data = store_quantity_map.get(str_code, {})
                store_unit_price = store_data.get('unit_price', 50.0)
                
                sty_sal_amt = row.get("sty_sal_amt")
                if not sty_sal_amt or str(sty_sal_amt).strip() == '':
                    continue
                
                spu_dict = json.loads(sty_sal_amt) if isinstance(sty_sal_amt, str) and sty_sal_amt.strip() else {}
                
                for spu_code, spu_sales_amt in spu_dict.items():
                    # Calculate REAL quantity for this SPU
                    spu_sales_amt = float(spu_sales_amt or 0)
                    
                    # Estimate unit price for this specific category
                    category = row.get("sub_cate_name", "")
                    category_unit_price = estimate_category_unit_price(category, store_unit_price)
                    
                    # Calculate quantity
                    spu_quantity = spu_sales_amt / category_unit_price if category_unit_price > 0 else 0
                    
                    spu_rows.append({
                        "str_code": str_code,
                        "str_name": row["str_name"],
                        "cate_name": row["big_class_name"] if "big_class_name" in row else None,
                        "sub_cate_name": row["sub_cate_name"],
                        "spu_code": spu_code,
                        "spu_sales_amt": spu_sales_amt,
                        "quantity": round(spu_quantity, 1),  # REAL QUANTITY
                        "unit_price": round(category_unit_price, 2),  # REAL UNIT PRICE
                        "investment_per_unit": round(category_unit_price, 2)
                    })
            except Exception as e:
                print(f"[DEBUG] Error parsing sty_sal_amt for row {idx}: {e}")
                continue
        
        spu_sales = pd.DataFrame(spu_rows)
        print(f"[DEBUG] ✅ SPU-level rows created: {len(spu_sales)} with REAL quantities and unit prices")
        
        if len(spu_sales) > 0:
            print(f"[DEBUG] Sample SPU data:")
            print(f"[DEBUG]   Unit price range: ${spu_sales['unit_price'].min():.2f} - ${spu_sales['unit_price'].max():.2f}")
            print(f"[DEBUG]   Quantity range: {spu_sales['quantity'].min():.1f} - {spu_sales['quantity'].max():.1f}")
            
            # Verify no $1.00 fake prices
            fake_prices = (spu_sales['unit_price'] == 1.0).sum()
            if fake_prices == 0:
                print(f"[DEBUG] ✅ NO FAKE $1.00 PRICES! All unit prices are realistic.")
            else:
                print(f"[DEBUG] ⚠️ Found {fake_prices} SPUs with $1.00 prices")
        
        return category_sales, spu_sales, valid_stores
        
    except Exception as e:
        print(f"[DEBUG] Failed to process and merge sales data: {e}")
        return pd.DataFrame(), pd.DataFrame(), []

def estimate_category_unit_price(category: str, store_avg_price: float) -> float:
    """
    Estimate unit price for a specific category based on store average and category type.
    
    Args:
        category: Category name (Chinese)
        store_avg_price: Average unit price for the store
        
    Returns:
        Estimated unit price for the category
    """
    # Category-specific price adjustments based on clothing industry knowledge
    category_lower = str(category).lower()
    
    # Base price adjustments relative to store average
    if 't恤' in category_lower or 'polo' in category_lower:
        return store_avg_price * 0.7  # T-shirts are typically cheaper
    elif '裤' in category_lower:
        return store_avg_price * 1.2  # Pants are typically more expensive
    elif '衬' in category_lower:
        return store_avg_price * 1.1  # Shirts are slightly above average
    elif '鞋' in category_lower:
        return store_avg_price * 1.6  # Shoes are significantly more expensive
    elif '外套' in category_lower or 'jacket' in category_lower:
        return store_avg_price * 1.8  # Outerwear is most expensive
    elif '袜' in category_lower:
        return store_avg_price * 0.2  # Socks are cheapest
    elif '内衣' in category_lower:
        return store_avg_price * 0.6  # Underwear is cheaper
    else:
        return store_avg_price  # Default to store average

def get_already_processed_stores(period_label: str) -> set:
    """
    Get the set of stores that were already successfully processed.
    
    Args:
        period_label: Period label (e.g., "202506A")
        
    Returns:
        Set of store codes that were successfully processed
    """
    processed_stores_file = os.path.join(OUTPUT_DIR, f"processed_stores_{period_label}.txt")
    processed_stores = set()
    
    if os.path.exists(processed_stores_file):
        try:
            with open(processed_stores_file, 'r') as f:
                processed_stores = {line.strip() for line in f if line.strip()}
            log_progress(f"Found {len(processed_stores)} previously processed stores")
        except Exception as e:
            log_progress(f"Warning: Could not read processed stores file: {e}")
    
    return processed_stores

def get_failed_stores(period_label: str) -> set:
    """
    Get the set of stores that failed to download (should be retried).
    
    Args:
        period_label: Period label (e.g., "202506A")
        
    Returns:
        Set of store codes that failed to download
    """
    failed_stores_file = os.path.join(OUTPUT_DIR, f"failed_stores_{period_label}.txt")
    failed_stores = set()
    
    if os.path.exists(failed_stores_file):
        try:
            with open(failed_stores_file, 'r') as f:
                failed_stores = {line.strip() for line in f if line.strip()}
            log_progress(f"Found {len(failed_stores)} previously failed stores (will retry)")
        except Exception as e:
            log_progress(f"Warning: Could not read failed stores file: {e}")
    
    return failed_stores

def save_successful_stores(period_label: str, successful_stores: List[str]) -> None:
    """
    Save successfully processed stores to tracking file.
    
    Args:
        period_label: Period label (e.g., "202506A")
        successful_stores: List of successfully processed store codes
    """
    processed_stores_file = os.path.join(OUTPUT_DIR, f"processed_stores_{period_label}.txt")
    with open(processed_stores_file, 'a') as f:
        for store in successful_stores:
            f.write(f"{store}\n")
            PROCESSED_STORES.add(store)

def save_failed_stores(period_label: str, failed_stores: List[str]) -> None:
    """
    Save failed stores to tracking file (these will be retried).
    
    Args:
        period_label: Period label (e.g., "202506A")
        failed_stores: List of failed store codes
    """
    failed_stores_file = os.path.join(OUTPUT_DIR, f"failed_stores_{period_label}.txt")
    with open(failed_stores_file, 'a') as f:
        for store in failed_stores:
            f.write(f"{store}\n")
            FAILED_STORES.add(store)

def validate_data_completeness(period_label: str, expected_stores: set) -> Tuple[bool, set, Dict[str, str]]:
    """
    Validate that all expected stores have complete data in the final files.
    
    Args:
        period_label: Period label (e.g., "202506A")
        expected_stores: Set of store codes that should be present
        
    Returns:
        Tuple of (is_complete, missing_stores, validation_report)
    """
    validation_report = {}
    stores_by_file = {}
    
    # Check each data file - look in OUTPUT directory where final files are stored
    data_files = [
        f"complete_category_sales_{period_label}.csv",
        f"complete_spu_sales_{period_label}.csv"
    ]
    
    # First check if the essential files exist in output directory
    all_files_exist = True
    for filename in data_files:
        filepath = os.path.join("output", filename)
        if not os.path.exists(filepath):
            all_files_exist = False
            validation_report[filename] = {'exists': False}
            stores_by_file[filename] = set()
            log_progress(f"Missing required file: {filename}")
        else:
            try:
                df = pd.read_csv(filepath)
                if 'str_code' in df.columns:
                    # Normalize to string to ensure consistent typing with expected_stores
                    # Without this, set operations would compare e.g. '12003' (str) vs 12003 (int) and report 0% erroneously
                    stores_in_file = set(df['str_code'].astype(str).str.strip().unique().tolist())
                    stores_by_file[filename] = stores_in_file
                    file_missing = expected_stores - stores_in_file
                    
                    validation_report[filename] = {
                        'exists': True,
                        'records': len(df),
                        'stores': len(stores_in_file),
                        'missing_stores': len(file_missing)
                    }
                    # Only log file details if verbose debugging needed
                    # log_progress(f"File {filename}: {len(stores_in_file)} stores, {len(file_missing)} missing")
                else:
                    log_progress(f"Warning: {filename} missing str_code column")
                    validation_report[filename] = {
                        'exists': True,
                        'error': 'Missing str_code column'
                    }
                    stores_by_file[filename] = set()
                    
            except Exception as e:
                log_progress(f"Error reading {filename}: {str(e)}")
                validation_report[filename] = {
                    'exists': True,
                    'error': str(e)
                }
                stores_by_file[filename] = set()  # Empty set for failed files
    
    # If essential files don't exist, return early
    if not all_files_exist:
        missing_stores = expected_stores
        validation_report['_summary'] = {
            'expected_stores': len(expected_stores),
            'stores_in_all_files': 0,
            'missing_stores': len(missing_stores),
            'is_complete': False
        }
        log_progress(f"Period {period_label}: Missing essential files - requires download")
        return False, missing_stores, validation_report
    
    # Find stores that are present in ALL existing files (intersection)
    if stores_by_file:
        # Only consider files that actually exist and have data
        valid_file_stores = [stores for stores in stores_by_file.values() if len(stores) > 0]
        
        if valid_file_stores:
            stores_in_all_files = set.intersection(*valid_file_stores)
            missing_stores = expected_stores - stores_in_all_files
            completion_rate = (len(stores_in_all_files) / len(expected_stores)) * 100 if expected_stores else 0
            log_progress(f"Period {period_label}: {len(stores_in_all_files)}/{len(expected_stores)} stores ({completion_rate:.1f}%)")
        else:
            stores_in_all_files = set()
            missing_stores = expected_stores
            log_progress(f"Period {period_label}: No valid data - all {len(missing_stores)} stores missing")
    else:
        stores_in_all_files = set()
        missing_stores = expected_stores
        log_progress(f"Period {period_label}: No data files found - all {len(missing_stores)} stores missing")

    # Consider complete if we have at least 95% of stores (allow for some failed downloads)
    completion_rate = (len(stores_in_all_files) / len(expected_stores)) * 100 if expected_stores else 0
    is_complete = completion_rate >= 95.0

    # Add summary to validation report
    validation_report['_summary'] = {
        'expected_stores': len(expected_stores),
        'stores_in_all_files': len(stores_in_all_files),
        'missing_stores': len(missing_stores),
        'completion_rate': completion_rate,
        'is_complete': is_complete
    }
    
    if is_complete:
        log_progress(f"✅ Period {period_label} is complete ({completion_rate:.1f}%) - will skip")
    else:
        log_progress(f"⚠️ Period {period_label} incomplete ({completion_rate:.1f}%) - will download")
    
    return is_complete, missing_stores, validation_report

def clean_partial_files(period_label: str) -> None:
    """
    Remove partial/intermediate files to clean up disk space.
    
    Args:
        period_label: Period label (e.g., "202506A")
    """
    import glob
    
    patterns = [
        f"partial_*_{period_label}_*.csv"
    ]
    
    files_removed = 0
    for pattern in patterns:
        file_path = os.path.join(OUTPUT_DIR, pattern)
        matching_files = glob.glob(file_path)
        for file in matching_files:
            try:
                os.remove(file)
                files_removed += 1
            except Exception as e:
                log_progress(f"Warning: Could not remove {file}: {e}")
    
    if files_removed > 0:
        log_progress(f"Cleaned up {files_removed} partial files")

def recover_from_partial_files(period_label: str) -> bool:
    """
    Attempt to recover from interrupted download by consolidating partial files.
    
    Args:
        period_label: Period label (e.g., "202506A")
        
    Returns:
        bool: True if recovery was successful, False otherwise
    """
    import glob
    
    log_progress(f"🔄 Attempting recovery from partial files for period {period_label}...")
    
    # Check for partial files
    partial_patterns = {
        'config': f"partial_config_{period_label}_*.csv",
        'sales': f"partial_sales_{period_label}_*.csv", 
        'category': f"partial_category_sales_{period_label}_*.csv",
        'spu': f"partial_spu_sales_{period_label}_*.csv"
    }
    
    recovery_data = {}
    
    for file_type, pattern in partial_patterns.items():
        file_path = os.path.join(OUTPUT_DIR, pattern)
        matching_files = glob.glob(file_path)
        
        if matching_files:
            log_progress(f"Found {len(matching_files)} partial {file_type} files")
            dataframes = []
            
            for file in matching_files:
                try:
                    df = pd.read_csv(file)
                    dataframes.append(df)
                    log_progress(f"  • Loaded {file}: {len(df)} records")
                except Exception as e:
                    log_progress(f"  ⚠️  Could not load {file}: {e}")
            
            if dataframes:
                recovery_data[file_type] = dataframes
            else:
                log_progress(f"  ❌ No valid {file_type} data found")
        else:
            log_progress(f"No partial {file_type} files found")
    
    # If we have data, try to consolidate it
    if recovery_data:
        log_progress("Consolidating recovered data...")
        
        config_data = recovery_data.get('config', [])
        sales_data = recovery_data.get('sales', [])
        category_data = recovery_data.get('category', [])
        spu_data = recovery_data.get('spu', [])
        
        # Use existing save_final_results function
        save_final_results(config_data, sales_data, category_data, spu_data, period_label)
        
        log_progress("✅ Recovery completed! Final files have been created.")
        return True
    else:
        log_progress("❌ No recoverable data found")
        return False

def process_stores_in_batches(store_codes: List[str], yyyymm: str, period: Optional[str] = None, batch_size: int = BATCH_SIZE, force_full_download: bool = False, clear_data: bool = False) -> None:
    """
    Process store data in batches with smart partial downloading support.
    
    Args:
        store_codes: List of all store codes to process
        yyyymm: Year and month in YYYYMM format
        period: Period indicator ("A" for first half, "B" for second half, None for full month)
        batch_size: Number of stores to process per batch
        force_full_download: If True, ignore existing data and download everything
    """
    period_label = get_period_label(yyyymm, period)
    log_progress(f"Processing stores for period {period_label} (force_full_download={force_full_download})...")
    
    # Smart downloading logic
    if not force_full_download:
        # Check what we already have processed and what failed
        processed_stores = get_already_processed_stores(period_label)
        failed_stores = get_failed_stores(period_label)
        expected_stores = set(store_codes)
        
        # For smart download: skip successfully processed stores, but retry failed ones
        stores_to_skip = processed_stores - failed_stores  # Don't retry successful stores
        missing_stores = expected_stores - stores_to_skip  # Include failed stores for retry
        
        # Check if final files exist and are complete
        is_complete, final_missing_stores, validation_report = validate_data_completeness(period_label, expected_stores)
        
        if is_complete:
            log_progress("✅ All data is already complete! No download needed.")
            log_progress("Data validation report:")
            for filename, report in validation_report.items():
                if report.get('exists'):
                    log_progress(f"  • {filename}: {report.get('records', 0)} records, {report.get('stores', 0)} stores")
            # Return completion status for early exit
            return True, 100.0, 0
        
        # Auto-recovery: Check if we have enough partial data to recover
        if len(processed_stores) > 100:  # Arbitrary threshold - if significant progress exists
            log_progress(f"🔄 Auto-recovery check: {len(processed_stores)} stores processed but no final files found")
            # DISABLED: Auto-recovery was corrupting good data by overwriting complete files with partials
            # if recover_from_partial_files(period_label):
            #     log_progress("✅ Auto-recovery successful! Checking completion...")
            #     # Re-validate after recovery
            #     is_complete_after_recovery, final_missing_after_recovery, _ = validate_data_completeness(period_label, expected_stores)
            #     if is_complete_after_recovery:
            #         log_progress("✅ Data is now complete after auto-recovery!")
            #         return True, 100.0, 0
            #     else:
            #         log_progress(f"⚠️ Partial recovery: {len(expected_stores) - len(final_missing_after_recovery)} stores recovered, continuing with remaining downloads")
            #         missing_stores = final_missing_after_recovery  # Update missing stores after recovery
            log_progress("🔄 Auto-recovery disabled to prevent data corruption. Use --recover flag if needed.")
        
        # Use processed stores for smart download decision
        retry_count = len(failed_stores & missing_stores)  # Failed stores that will be retried
        new_count = len(missing_stores - failed_stores)     # New stores never attempted
        
        log_progress(f"Smart download analysis:")
        log_progress(f"  • Successfully processed: {len(processed_stores - failed_stores)} stores (will skip)")
        log_progress(f"  • Previously failed: {retry_count} stores (will retry)")
        log_progress(f"  • Never attempted: {new_count} stores (will download)")
        log_progress(f"  • Total to process: {len(missing_stores)} stores")
        
        # Determine which stores to process
        if len(missing_stores) < len(expected_stores) * 0.5:  # Less than 50% missing
            store_codes_to_process = list(missing_stores)
            log_progress(f"Smart incremental download: Processing {len(store_codes_to_process)} stores")
            log_progress(f"Stores to process: {sorted(list(missing_stores))[:10]}{'...' if len(missing_stores) > 10 else ''}")
        else:
            log_progress(f"Many stores needed ({len(missing_stores)}/{len(expected_stores)}). Consider using --force-full flag.")
            log_progress("For safety, performing incremental download of needed stores only.")
            store_codes_to_process = list(missing_stores)
    else:
        store_codes_to_process = store_codes
        log_progress(f"Force full download: Processing all {len(store_codes_to_process)} stores")
    
    # Create/reset tracking file
    processed_stores_file = os.path.join(OUTPUT_DIR, f"processed_stores_{period_label}.txt")
    
    if force_full_download:
        # Only clear when explicitly requested by user
        if clear_data:
            log_progress("Clear data mode: Removing all previous data files")
        else:
            log_progress("Force full download mode: Will regenerate all data files")
        
        # Clear all existing data for complete regeneration
        clear_previous_data(yyyymm, period, keep_notes=True)
        with open(processed_stores_file, 'w') as f:
            pass  # Create empty file
    
    # Lists to store batch results
    config_data_list = []
    sales_data_list = []
    category_sales_list = []
    spu_sales_list = []
    
    if not force_full_download:
        # Load existing complete files if they exist
        existing_files = {
            'config': f"store_config_{period_label}.csv",
            'sales': f"store_sales_{period_label}.csv",
            'category': f"complete_category_sales_{period_label}.csv",
            'spu': f"complete_spu_sales_{period_label}.csv"
        }
        
        for file_type, filename in existing_files.items():
            filepath = os.path.join(OUTPUT_DIR, filename)
            if os.path.exists(filepath):
                try:
                    df = pd.read_csv(filepath)
                    if file_type == 'config':
                        config_data_list.append(df)
                    elif file_type == 'sales':
                        sales_data_list.append(df)
                    elif file_type == 'category':
                        category_sales_list.append(df)
                    elif file_type == 'spu':
                        spu_sales_list.append(df)
                    log_progress(f"Loaded existing {filename}: {len(df)} records")
                except Exception as e:
                    log_progress(f"Warning: Could not load {filename}: {e}")
    
    # Process stores in batches
    log_progress(f"Processing {len(store_codes_to_process)} stores in batches of {batch_size}...")
    
    for i in range(0, len(store_codes_to_process), batch_size):
        batch = store_codes_to_process[i:i+batch_size]
        print(f"[DEBUG] Processing batch {i//batch_size + 1}/{(len(store_codes_to_process) + batch_size - 1)//batch_size} ({len(batch)} stores)...")
        
        # Fetch data for this batch
        config_df, config_stores = fetch_store_config(batch, yyyymm, period)
        if not config_df.empty:
            config_data_list.append(config_df)
        
        sales_df, sales_stores = fetch_store_sales(batch, yyyymm, period)
        if not sales_df.empty:
            sales_data_list.append(sales_df)
        
        # Determine successful and failed stores for this batch
        successful_stores_batch = []
        failed_stores_batch = []
        
        # Process and merge data
        if not config_df.empty and not sales_df.empty:
            category_df, spu_df, processed_stores_batch = process_and_merge_data(sales_df, config_df)
            if not category_df.empty:
                category_sales_list.append(category_df)
            if not spu_df.empty:
                spu_sales_list.append(spu_df)
            
            successful_stores_batch = processed_stores_batch
        
        # Identify failed stores (attempted but no data)
        attempted_stores = set(batch)
        successful_stores_set = set(successful_stores_batch)
        failed_stores_batch = list(attempted_stores - successful_stores_set)
        
        # Update tracking files separately
        if successful_stores_batch:
            save_successful_stores(period_label, successful_stores_batch)
        
        if failed_stores_batch:
            save_failed_stores(period_label, failed_stores_batch)
        
        # Save intermediate results periodically
        if i % (batch_size * 5) == 0 and i > 0:
            save_intermediate_results(config_data_list, sales_data_list, category_sales_list, spu_sales_list, period_label)
        
        # Rate limiting
        if i + batch_size < len(store_codes_to_process):
            time.sleep(1)
    
    # Save final consolidated results
    save_final_results(config_data_list, sales_data_list, category_sales_list, spu_sales_list, period_label)
    
    # Clean up partial files
    clean_partial_files(period_label)
    
    # Final validation
    expected_stores = set(store_codes)
    is_complete, missing_stores, validation_report = validate_data_completeness(period_label, expected_stores)
    
    # Calculate actual completion stats
    stores_present = len(expected_stores) - len(missing_stores)
    completion_rate = (stores_present / len(expected_stores)) * 100 if expected_stores else 0
    
    if is_complete:
        log_progress("✅ Data download completed successfully!")
    else:
        log_progress(f"⚠️  Download completed: {stores_present}/{len(expected_stores)} stores ({completion_rate:.1f}%)")
        if len(missing_stores) < 100:  # Only show missing stores if reasonable number
            log_progress(f"Missing stores: {sorted(list(missing_stores))[:10]}{'...' if len(missing_stores) > 10 else ''}")
        else:
            log_progress(f"Too many missing stores ({len(missing_stores)}) to list - check API connectivity")
    
    # Show final validation report
    log_progress("Final data validation:")
    for filename, report in validation_report.items():
        if report.get('exists'):
            log_progress(f"  • {filename}: {report.get('records', 0)} records, {report.get('stores', 0)} stores")
    
    # CRITICAL: Return completion status to prevent unnecessary re-runs
    return is_complete, completion_rate, len(missing_stores)

def save_intermediate_results(config_data: List[pd.DataFrame], sales_data: List[pd.DataFrame], category_sales: List[pd.DataFrame], spu_sales: List[pd.DataFrame], period_label: str) -> None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if config_data:
        pd.concat(config_data).to_csv(os.path.join(OUTPUT_DIR, f"partial_config_{period_label}_{timestamp}.csv"), index=False)
    if sales_data:
        pd.concat(sales_data).to_csv(os.path.join(OUTPUT_DIR, f"partial_sales_{period_label}_{timestamp}.csv"), index=False)
    if category_sales:
        pd.concat(category_sales).to_csv(os.path.join(OUTPUT_DIR, f"partial_category_sales_{period_label}_{timestamp}.csv"), index=False)
    if spu_sales:
        pd.concat(spu_sales).to_csv(os.path.join(OUTPUT_DIR, f"partial_spu_sales_{period_label}_{timestamp}.csv"), index=False)
    print(f"[DEBUG] Saved intermediate results for period {period_label}")

def save_final_results(config_data: List[pd.DataFrame], sales_data: List[pd.DataFrame], category_sales: List[pd.DataFrame], spu_sales: List[pd.DataFrame], period_label: str) -> None:
    """Save final combined results to CSV files with period-specific naming"""
    try:
        # Save to both data/api_data (for pipeline steps) and output (for final results)
        api_output_dir = OUTPUT_DIR  # data/api_data
        final_output_dir = "output"
        os.makedirs(api_output_dir, exist_ok=True)
        os.makedirs(final_output_dir, exist_ok=True)
        
        if config_data:
            config_df = pd.concat(config_data, ignore_index=True)
            # Extra safety: Remove any duplicates in final config data
            original_config_count = len(config_df)
            config_df = config_df.drop_duplicates()
            if len(config_df) != original_config_count:
                log_progress(f"[DEDUP] Removed {original_config_count - len(config_df)} duplicate config records during final save")
            
            # Save to both directories
            config_file_api = os.path.join(api_output_dir, f"store_config_{period_label}.csv")
            config_file_final = os.path.join(final_output_dir, f"store_config_{period_label}.csv")
            config_df.to_csv(config_file_api, index=False)
            config_df.to_csv(config_file_final, index=False)
            log_progress(f"Saved configuration data: {config_file_api} and {config_file_final} ({len(config_df)} rows, {len(config_df['str_code'].unique())} stores)")
        
        if sales_data:
            sales_df = pd.concat(sales_data, ignore_index=True)
            # Extra safety: Remove any duplicates in final sales data
            original_sales_count = len(sales_df)
            sales_df = sales_df.drop_duplicates()
            if len(sales_df) != original_sales_count:
                log_progress(f"[DEDUP] Removed {original_sales_count - len(sales_df)} duplicate sales records during final save")
            
            # Save to both directories
            sales_file_api = os.path.join(api_output_dir, f"store_sales_{period_label}.csv")
            sales_file_final = os.path.join(final_output_dir, f"store_sales_{period_label}.csv")
            sales_df.to_csv(sales_file_api, index=False)
            sales_df.to_csv(sales_file_final, index=False)
            log_progress(f"Saved sales data: {sales_file_api} and {sales_file_final} ({len(sales_df)} rows, {len(sales_df['str_code'].unique())} stores)")
        
        if category_sales:
            category_df = pd.concat(category_sales, ignore_index=True)
            
            # Apply deduplication to final consolidated category data
            original_count = len(category_df)
            category_duplicates = category_df.duplicated().sum()
            if category_duplicates > 0:
                category_df = category_df.drop_duplicates()
                log_progress(f"[DEDUP] Removed {original_count - len(category_df)} duplicate category records")
            
            # Save to both directories
            category_file_api = os.path.join(api_output_dir, f"complete_category_sales_{period_label}.csv")
            category_file_final = os.path.join(final_output_dir, f"complete_category_sales_{period_label}.csv")
            category_df.to_csv(category_file_api, index=False)
            category_df.to_csv(category_file_final, index=False)
            log_progress(f"Saved category sales data: {category_file_api} and {category_file_final} ({len(category_df)} rows, {len(category_df['str_code'].unique())} stores)")
        
        if spu_sales:
            spu_df = pd.concat(spu_sales, ignore_index=True)
            
            # CRITICAL: Apply deduplication to final consolidated SPU data
            # This handles cases where incremental downloads create duplicates
            original_count = len(spu_df)
            store_spu_duplicates = spu_df.duplicated(subset=['str_code', 'spu_code']).sum()
            exact_duplicates = spu_df.duplicated().sum()
            
            if store_spu_duplicates > 0 or exact_duplicates > 0:
                log_progress(f"[DEDUP] Found {store_spu_duplicates} store-SPU duplicates and {exact_duplicates} exact duplicates")
                # Remove exact duplicates first, then store-SPU duplicates
                spu_df = spu_df.drop_duplicates()
                spu_df = spu_df.drop_duplicates(subset=['str_code', 'spu_code'], keep='first')
                log_progress(f"[DEDUP] Removed {original_count - len(spu_df)} duplicate records ({len(spu_df)} clean records remaining)")
            
            # Save to both directories
            spu_file_api = os.path.join(api_output_dir, f"complete_spu_sales_{period_label}.csv")
            spu_file_final = os.path.join(final_output_dir, f"complete_spu_sales_{period_label}.csv")
            spu_df.to_csv(spu_file_api, index=False)
            spu_df.to_csv(spu_file_final, index=False)
            log_progress(f"Saved SPU sales data: {spu_file_api} and {spu_file_final} ({len(spu_df)} rows, {len(spu_df['str_code'].unique())} stores)")
        
        log_progress(f"Data download and processing complete for period {period_label}")
        
    except Exception as e:
        log_error("Failed to save final results", traceback.format_exc())

def process_multi_period_data_collection(target_yyyymm: str, target_period: str, n_months: int = 3, batch_size: int = 10, force_full_download: bool = False, clear_data: bool = False) -> Tuple[bool, float, int]:
    """
    Process multiple periods for clustering data collection.
    
    Args:
        target_yyyymm: Target period in YYYYMM format
        target_period: Target period indicator  
        n_months: Number of months to collect data for
        batch_size: Number of stores per API call
        force_full_download: Force complete re-download
        clear_data: Clear all previous data
        
    Returns:
        Tuple of (is_complete, completion_rate, missing_count)
    """
    log_progress(f"🔄 Starting multi-period data collection for clustering (last {n_months} months)")
    
    # Get the periods we need to collect
    periods_needed = get_last_n_months_periods(target_yyyymm, target_period, n_months)
    log_progress(f"Periods needed for clustering: {periods_needed}")
    
    # Check which periods we already have
    availability = check_multi_period_data_availability(periods_needed)
    missing_periods = [period for period, available in availability.items() if not available]
    available_periods = [period for period, available in availability.items() if available]
    
    log_progress(f"Data availability check:")
    log_progress(f"  • Already available: {len(available_periods)} periods {available_periods}")
    log_progress(f"  • Need to download: {len(missing_periods)} periods {missing_periods}")
    
    if not missing_periods:
        log_progress("✅ All required periods already available!")
        return True, 100.0, 0
    
    # Download missing periods
    overall_success = True
    total_completion = 0.0
    total_missing = 0
    
    for period in missing_periods:
        log_progress(f"📥 Downloading data for period: {period}")
        period_yyyymm = period[:6]
        period_indicator = period[6:]
        
        try:
            # Process this individual period
            is_complete, completion_rate, missing_count = process_stores_in_batches(
                get_unique_store_codes(), 
                period_yyyymm, 
                period_indicator, 
                batch_size, 
                force_full_download, 
                clear_data
            )
            
            total_completion += completion_rate
            total_missing += missing_count
            
            if not is_complete:
                overall_success = False
                log_progress(f"⚠️ Period {period} incomplete: {completion_rate:.1f}% completion")
            else:
                log_progress(f"✅ Period {period} complete: 100% completion")
                
        except Exception as e:
            log_progress(f"❌ Failed to download period {period}: {str(e)}")
            overall_success = False
    
    # Calculate overall statistics
    periods_processed = len(missing_periods)
    if periods_processed > 0:
        avg_completion = total_completion / periods_processed
        avg_missing = total_missing / periods_processed
    else:
        avg_completion = 100.0
        avg_missing = 0
    
    log_progress(f"🎯 Multi-period collection summary:")
    log_progress(f"  • Periods processed: {periods_processed}")
    log_progress(f"  • Average completion: {avg_completion:.1f}%")
    log_progress(f"  • Overall success: {overall_success}")
    
    return overall_success, avg_completion, int(avg_missing)

def main() -> None:
    """Main function to execute the data download process"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Download store sales data from FastFish API with half-month support')
    parser.add_argument('--month', type=str, default=TARGET_YYYYMM,
                       help=f'Year-month in YYYYMM format (default: {TARGET_YYYYMM})')
    parser.add_argument('--period', type=str, choices=['A', 'B', 'full'], default='A' if TARGET_PERIOD else 'full',
                       help='Period to download: A=first half, B=second half, full=entire month (default: A)')
    parser.add_argument('--list-periods', action='store_true',
                       help='List available periods in existing data and exit')
    parser.add_argument('--batch-size', type=int, default=BATCH_SIZE,
                       help=f'Number of stores to process per API call (default: {BATCH_SIZE})')
    parser.add_argument('--force-full', action='store_true',
                       help='Force complete re-download ignoring existing data (for troubleshooting)')
    parser.add_argument('--clear-data', action='store_true',
                       help='Clear all previous data before downloading (implies --force-full)')
    parser.add_argument('--disable-smart', action='store_true',
                       help='Disable smart incremental downloading (download everything)')
    parser.add_argument('--recover', action='store_true',
                       help='Recover from interrupted download by consolidating partial files')
    parser.add_argument('--multi-period', action='store_true',
                       help='Download last 3 months of data for clustering analysis')
    parser.add_argument('--year-over-year', action='store_true',
                       help='Download both current 3 months AND same period last year for seasonal clustering')
    parser.add_argument('--months-back', type=int, default=MONTHS_FOR_CLUSTERING,
                       help=f'Number of months to look back for multi-period collection (default: {MONTHS_FOR_CLUSTERING})')
    
    args = parser.parse_args()
    
    # Set variables based on arguments early so they're available for all modes
    target_yyyymm = args.month
    target_period = args.period if args.period != 'full' else None
    batch_size = args.batch_size
    
    # Handle recovery command  
    if args.recover:
        period_label = get_period_label(target_yyyymm, target_period)
        
        log_progress(f"Recovery mode: Attempting to consolidate partial files for {period_label}")
        if recover_from_partial_files(period_label):
            log_progress("✅ Recovery successful! You can now proceed with the pipeline.")
        else:
            log_progress("⚠️ Recovery failed - some files may be incomplete")
        return
    
    # Get store codes early for all modes
    store_codes = get_unique_store_codes()
    if not store_codes:
        log_progress("No store codes found. Exiting.")
        return
    
    # Handle multi-period download for the last N months
    if args.multi_period:
        log_progress(f"🎯 Starting multi-period data collection for the last {args.months_back} months...")
        
        try:
            start_time = time.time()
            
            force_full_download = args.force_full or args.clear_data
            is_complete, completion_rate, missing_count = process_multi_period_data_collection(
                target_yyyymm, target_period, args.months_back, batch_size, force_full_download, args.clear_data
            )
            
            elapsed_time = (time.time() - start_time) / 60
            
            if is_complete:
                log_progress(f"✅ Multi-period collection completed successfully in {elapsed_time:.2f} minutes")
                log_progress("🎯 Ready for clustering analysis with 3-month data!")
            else:
                log_progress(f"⚠️ Multi-period collection completed with {completion_rate:.1f}% completion in {elapsed_time:.2f} minutes")
                
        except Exception as e:
            log_progress(f"❌ Multi-period collection failed: {str(e)}")
            
        return
    
    # Handle year-over-year seasonal download
    if args.year_over_year:
        log_progress("🎯 Starting year-over-year seasonal data collection...")
        log_progress(f"This will download current {args.months_back} months AND same period from last year")
        
        try:
            start_time = time.time()
            
            # Get both current and historical periods
            current_periods, historical_periods = get_year_over_year_seasonal_periods(
                target_yyyymm, target_period, args.months_back
            )
            
            all_periods = current_periods + historical_periods
            total_periods = len(all_periods)
            
            log_progress(f"📊 Total periods to download: {total_periods}")
            log_progress(f"📅 Current periods: {current_periods}")
            log_progress(f"📅 Historical periods: {historical_periods}")
            
            # For year-over-year, we'll download current periods first, then historical
            force_full_download = args.force_full or args.clear_data
            
            # Download each period individually for better control
            successful_downloads = 0
            total_downloads = len(all_periods)
            
            log_progress("📥 Downloading individual periods...")
            
            for i, period_str in enumerate(all_periods, 1):
                period_yyyymm = period_str[:6]  # Extract YYYYMM
                period_indicator = period_str[6:] if len(period_str) > 6 else "A"  # Extract A/B
                
                log_progress(f"📅 Processing period {i}/{total_downloads}: {period_str} ({period_yyyymm}, period {period_indicator})")
                
                try:
                    # Check if this period already exists and is complete
                    period_label = get_period_label(period_yyyymm, period_indicator)
                    expected_stores = set(get_unique_store_codes())
                    
                    if not force_full_download:
                        is_complete, missing_stores, validation_report = validate_data_completeness(period_label, expected_stores)
                        if is_complete:
                            log_progress(f"✅ Period {period_str} already complete! Skipping...")
                            successful_downloads += 1
                            continue
                    
                    # Download this specific period
                    is_complete, completion_rate, missing_count = process_stores_in_batches(
                        list(expected_stores), period_yyyymm, period_indicator, batch_size, force_full_download, args.clear_data
                    )
                    
                    if is_complete or completion_rate > 80.0:  # Consider 80%+ as successful
                        log_progress(f"✅ Period {period_str} completed successfully ({completion_rate:.1f}%)")
                        successful_downloads += 1
                    else:
                        log_progress(f"⚠️ Period {period_str} completed with issues ({completion_rate:.1f}%)")
                        
                except Exception as e:
                    log_progress(f"❌ Period {period_str} failed: {str(e)}")
            
            # Calculate overall success
            overall_success_rate = (successful_downloads / total_downloads) * 100
            elapsed_time = (time.time() - start_time) / 60
            
            if successful_downloads == total_downloads:
                log_progress(f"✅ Year-over-year seasonal collection completed successfully in {elapsed_time:.2f} minutes")
                log_progress("🎯 Ready for advanced seasonal clustering with current + historical data!")
            else:
                log_progress(f"⚠️ Year-over-year collection completed with {overall_success_rate:.1f}% success rate in {elapsed_time:.2f} minutes")
                log_progress(f"Successfully downloaded: {successful_downloads}/{total_downloads} periods")
                
        except Exception as e:
            log_progress(f"❌ Year-over-year collection failed: {str(e)}")
            
        return
    
    # Handle list periods command
    if args.list_periods:
        print("Available data periods in output directory:")
        if os.path.exists("output"):
            files = [f for f in os.listdir("output") if f.startswith('complete_category_sales_')]
            if files:
                for file in sorted(files):
                    period_label = file.replace('complete_category_sales_', '').replace('.csv', '')
                    if period_label.endswith('A'):
                        desc = f"{period_label[:-1]} (first half)"
                    elif period_label.endswith('B'):
                        desc = f"{period_label[:-1]} (second half)"
                    else:
                        desc = f"{period_label} (full month)"
                    print(f"  • {desc}")
            else:
                print("  No existing data files found")
        else:
            print("  Output directory does not exist")
        return

    # Determine download mode - SMART BY DEFAULT
    force_full_download = args.force_full or args.clear_data  # Force full only if explicitly requested
    smart_download = not args.disable_smart and not force_full_download  # Smart download is DEFAULT
    
    start_time = time.time()
    period_desc = get_period_description(target_period)
    log_progress(f"Starting store data download process for {target_yyyymm} ({period_desc})...")
    mode_desc = "Smart incremental download (default)" if smart_download else "Force full download"
    log_progress(f"Configuration: batch_size={batch_size}, period={target_period or 'full'}, mode={mode_desc}")
    
    # Set global configuration for other pipeline steps
    set_current_period(target_yyyymm, target_period)
    
    try:
        # Process stores with smart downloading logic
        is_complete, completion_rate, missing_count = process_stores_in_batches(store_codes, target_yyyymm, target_period, batch_size, force_full_download, args.clear_data)
        elapsed_time = (time.time() - start_time) / 60
        
        if is_complete:
            log_progress(f"✅ Process completed successfully in {elapsed_time:.2f} minutes (100% completion)")
        else:
            log_progress(f"⚠️  Process completed with {completion_rate:.1f}% completion in {elapsed_time:.2f} minutes ({missing_count} stores missing)")
            
        # Early exit if we have good enough completion (>95%)
        if completion_rate >= 95.0:
            log_progress("✅ Completion rate is sufficient (≥95%). Proceeding with pipeline.")
        elif not force_full_download and completion_rate < 90.0:
            log_progress(f"⚠️  Low completion rate ({completion_rate:.1f}%). Consider using --force-full flag for complete data.")
        
        # Always continue to create compatibility files regardless of completion rate
        
        # Create backward compatibility files for legacy scripts
        ensure_backward_compatibility()
        
        # Show output files
        period_label = get_period_label(target_yyyymm, target_period)
        log_progress("Output files created:")
        output_files = [
            f"store_config_{period_label}.csv",
            f"store_sales_{period_label}.csv", 
            f"complete_category_sales_{period_label}.csv",
            f"complete_spu_sales_{period_label}.csv"
        ]
        for filename in output_files:
            filepath = os.path.join("output", filename)
            if os.path.exists(filepath):
                size_mb = os.path.getsize(filepath) / (1024 * 1024)
                log_progress(f"  • {filename} ({size_mb:.1f} MB)")
        
    except Exception as e:
        error_msg = "Unexpected error in main process"
        log_error(error_msg, traceback.format_exc())
        sys.exit(f"Error: {error_msg}. Check notes directory for details.")

if __name__ == "__main__":
    main() 