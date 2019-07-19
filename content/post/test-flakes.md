+++
date = "2019-07-19"
title = "Strategies for handling flaky test suites"
slug = "test-flakes"
categories = [ "Post", "Testing", "Software Development"]
tags = [ "tests", "flakes", "pytest", "circleci" ]
+++

Test flakes are tests that occasionally fail due to a variety of potential reasons including network instability (for tests making network calls that are not mocked) and other non-deterministic behavior. Test flakes are problematic as they reduce confidence in the results of test runs: they condition developers that the test suite cannot be relied on, and as such can result in legitimate bugs being ignored due to [alert fatigue](https://en.wikipedia.org/wiki/Alarm_fatigue).

This post contains some strategies for identifying and handling flaky tests in Python. 

### Identify, track, and fix

One strategy is once a flake is identified to treat them like any other bug:

1. File an issue to track it such that there is awareness of the flakey test.
2. Reproduce the flake locally.
3. Fix whatever underlying reason is causing the flaky behavior.

A common problem is to skip step 2, and instead take a guess why the flake is happening, and then modify the behavior. To prevent unnecessary implementation/review time, it's worth resisting this urge and to at least try to understand the behavior prior to making changes. If it proves particularly troublesome to identify, _then_ it may be reasonable to make some experimental fixes.

One strategy to identify the underlying problem is to use a plugin like `pytest-repeat` (`pip install pytest-repeat`) to run a _single_ test a large number of times: 

```bash
pytest --count 100 tests/test_app.py::test_my_flaky_behavior
```

You can do this on your main branch to reproduce the flake (adjusting the `count` as needed based on the failure rate of the test), and then run again once you have applied a fix to verify that it indeed resolves the issue.

### Automatically re-run flaky tests

Alternatively, a quick fix if you don't want to take the time to address the underlying issues in the test suite is a pytest plugin called [`flaky`](https://github.com/box/flaky) (`pip install flaky`). One can use this to re-run individual flaky tests or classes of flaky tests up to a configurable number of times, e.g.:

```python
@flaky(max_runs=10)
def test_my_flaky_behavior():
    expected_result = 'result'
    actual_result = my_function('arg1', 'arg2')
    assert expected_result == actual_result
```

### Flaky test dashboard

If you use a CI provider like Circle CI, you can see which tests are the most flaky (and use that to prioritize fixes) if you export test metadata:

```shell
pytest --junitxml=~/project/test-results/junit.xml
```

And then export them to Circle CI using their `store_test_results` and `store_artifacts` steps:

```yaml
- store_test_results:
    path: ~/project/test-results

- store_artifacts:
    path: ~/project/test-results
```

These tests results, as CI jobs fail due to flakes, will populate a dashboard at https://circleci.com/build-insights which will contain the most often failed tests, along with other useful information like the longest running failed tests.
