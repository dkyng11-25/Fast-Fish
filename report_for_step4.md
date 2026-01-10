# report_for_step4

## Scope
Step 4: Download historical weather data per store coordinate for downstream feels-like and temperature constraints.

## What improvement was made (refactoring)
- **No refactored Step 4 implementation was found** under `src/steps/`.
- Step 4 currently remains as the legacy script: `src/step4_download_weather_data.py`.

## Why no improvement was made
- A Step-based refactor was not implemented for Step 4 in the current codebase.

## What problems remain because it was not refactored
- **Harder testing**: legacy script patterns are typically harder to unit-test and BDD-test.
- **Harder dependency control**: API calls, rate limiting, persistence, progress tracking are less modular.

## What is still effectively “done” in functionality
- Step 4 appears functionally complete for downloading weather data (per earlier exam summary), but this is **not a refactor outcome**—it is legacy behavior.

## Remaining blockers / further work
- **Refactor needed** (if required by project standards):
  - Create `src/steps/weather_download_step.py` (or similar) following 4-phase pattern.
  - Introduce repositories for:
    - coordinate input
    - weather API access
    - weather file persistence
    - progress tracking
- **BDD tests**:
  - Given coordinates, when downloading, then per-store weather files and altitude cache are produced.
  - Given API failure, when retrying, then it backs off and fails clearly after max retries.
