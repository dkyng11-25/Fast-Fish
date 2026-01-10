Feature: Step 9 Below Minimum Rule - Real Data Testing
  As a data pipeline tester
  I want to test step9 below minimum rule with real data files
  So that I can validate the business logic and data outputs

  Background:
    Given real data files are available for period "202509A"
    And environment is configured for period "202509A"

  Scenario: Successful below minimum analysis with real data
    When step9 below minimum rule is executed with real data
    Then opportunities CSV file is generated with valid schema
    And results CSV file is generated with valid schema
    And summary markdown report is generated
    And opportunities contain below minimum cases
    And results contain store level summaries
    And Fast Fish validation is applied
    And investment calculations are correct

  Scenario: Error handling for missing SPU sales file
    Given real data files are available for period "202509A"
    And environment is configured for period "202509A"
    When step9 below minimum rule is executed with real data
    Then error handling works for missing files

  Scenario Outline: Testing with different periods
    Given real data files are available for period "<period>"
    And environment is configured for period "<period>"
    When step9 below minimum rule is executed with real data
    Then opportunities CSV file is generated with valid schema
    And results CSV file is generated with valid schema
    And summary markdown report is generated

    Examples:
      | period  |
      | 202509A |
      | 202508A |
      | 202508B |
