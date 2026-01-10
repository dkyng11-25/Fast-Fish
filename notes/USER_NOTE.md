Things to include in `tests` (especially when it comes to subsets for accelerated sampling)
We are currently using 202509A data, but please remember to make the test flexible and use other time periods
We only need "black box" tests that makes the least assumptions when it comes to pipeline functionality
Most of the documentation are in `process_and_merge_docs` so please use that as reference as well
Fix `tests` instead of attempting to refactor `src` since that is not the current responsibility
Is it better to run tests in parallel rather than waiting for a single test to finish
`data` and `output` are generated already for 202509A, please try with past data too e.g. 202508A, 202508B, etc.
Use `schema` and `validator` patterns from `tests` liberally to make sure that the code can be well organized

step 6
- Make sure that even when provided arbitrary subset of stores, the clustering compliant (standard sized clusters)
- Make the subset selection non-random such that we can easily replicate them
- Ensure weather band compliance for each cluster, so sampling 150-250 stores are permissible
- Make sure that each form of clustering is covered based on the step

step 7-12 (for each of the steps)
- Select 5 clusters (with a spread of high/average consumption) as subset to see if missing categories can be filled in properly
- Both subcategory and SPU level "missing" should be checked accordingly to be compliant
- Examine if the output is format-compliant and logic-compliant (similar to the description of documentation)
- Run test against multiple parameter settings to make sure that anomalies are captured in test logs
(Note that steps 10 and 11 are known to be slow)

step 13-14
- Make sure that that the input format from previous steps, as well as output format, is compliant to the standard
- Make sure that the performance metrics are displayed clearly
- The actionable insights has to be visible in order for the step to be considered functional

step 15-16
- Check if the historical data is present before running
- Make sure that the logic comparison is correct FOR 15 store sub-sample
- Double-check the input and output formatting accordingly before proceeding

step 17-18
- The STR calculation and augmentation algorithm should be correct when tested against a 15-store subset
- The input and output formats should be compliant