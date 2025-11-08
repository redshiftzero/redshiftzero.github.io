+++
title = "Property-based Testing"
date = "2025-11-08"
slug = "proptests"
categories = [ "testing", "Python" ]
tags = [ "testing", "Python" ]
+++

When we write tests to check the correctness of our code, we're used to thinking of examples: base cases, boundary conditions, edge cases, and so on. We enumerate these examples, and write example-based unit tests that check given a specific example input, we get an expected output.

For example, if we're testing a function that reverses a list, we might write tests like:

```py
def test_reverse_empty():
    assert reverse([]) == []

def test_reverse_single():
    assert reverse([1]) == [1]

def test_reverse_multiple():
    assert reverse([1, 2, 3]) == [3, 2, 1]
```

This approach is fine, but has several problems. First, it's laborious: we need to manually generate these examples, and write tests for each one. Second, what happens if we don't think of some examples we really should be covering - we'll never write that test, and any related bugs will not be found. What about lists with duplicate elements? What about lists with negative numbers? What about very long lists? The combinatorial explosion of possible inputs makes it impractical to test them all manually.

This is where property-based testing can help us.

# What is Property-based testing?

Property-based testing allows us to write down the **properties** that our code should always satisfy, rather than enumerating specific examples. A property is a statement that should be true for all valid inputs.

If we want to test a sorting function, we can identify several properties it should satisfy:

- The output array should always have the same elements as the input (just reordered)
- The output array should be in non-decreasing order
- Applying sort twice should give the same result as sorting once (idempotency)
- The length of the output should match the length of the input

Property-based tests let you write down these properties, and then the framework will:

1. Generate random inputs according to a strategy
2. Execute the code under test with those inputs
3. Verify that the property holds
4. Search for counterexamples - inputs where the property fails
5. Shrink failing examples to find the minimal case that reproduces the bug

By focusing on properties rather than examples, we can test a much larger space of inputs automatically, often catching bugs that manual example-based tests would miss. 

# Property-Based Testing with Python

Hypothesis is a Python library for property-based testing that is based on QuickCheck from Haskell.  

First, we should install Hypothesis following the documentation. In a virtual environment:

```
pip install hypothesis
```

## How Hypothesis Works

When you write a property-based test with Hypothesis, the `@given` decorator takes a **strategy** that describes what kind of data to generate. Strategies are composable - you can build complex data types from simple ones. You can write your own strategies for your own custom data types. 

By default, Hypothesis then runs your test function 100 times (configurable), each time with a different randomly generated input. If an assertion fails, Hypothesis will try to find a simpler input that also fails, a process called **shrinking**.

Also, Hypothesis maintains a database of previously found failing examples, so it can replay them in future test runs to ensure regressions don't reoccur.

Here's a simple example:

```py
from hypothesis import given
from hypothesis import strategies as st

@given(st.lists(st.integers()))
def test_sort_preserves_length(xs):
    sorted_xs = sorted(xs)
    assert len(xs) == len(sorted_xs)
```

In this example, `st.lists(st.integers())` is a strategy that generates random lists of integers. Hypothesis will generate many such lists (empty lists, single-element lists, large lists, lists with negative numbers, etc.) and verify that sorting doesn't change the length.

## Strategies

Strategies define what data Hypothesis should generate. Hypothesis provides many built-in strategies, for example we just saw `st.integers()` which generates integers combined with `st.lists()` which generates lists. 

There are also combination strategies, e.g. `st.one_of(...)` lets us randomly choose from one of several strategies.

You can also constrain strategies, for example `st.integers(min_value=0, max_value=100)` generates integers in the specified range.

# Shrinking

When Hypothesis finds a failure, it doesn't just report the first failing input it encountered. Instead, it performs **shrinking** - it tries to find the simplest example that still violates the property. This makes debugging much easier.

For example, if your test fails on a list with 1000 elements `[1, 2, 3, ..., 1000]`, Hypothesis might shrink it down to just `[1, 2, 3]` or even `[1, 0]` if that's what actually triggers the bug. The shrinking process tries various techniques:

- Removing elements from collections
- Making numbers smaller
- Simplifying strings
- Trying edge cases like empty collections, zero, or negative numbers

This gives you a minimal reproducible example that's much easier to understand and debug than a large, complex input. 

# More Examples

Here are a few more cases where property-based testing can be helpful.

## Round-Trip Testing

One common pattern is testing that operations are inverses of each other. For example, encoding and decoding should round-trip:

```py
@given(st.text())
def test_encode_decode_roundtrip(text):
    encoded = base64.b64encode(text.encode()).decode()
    decoded = base64.b64decode(encoded).decode()
    assert decoded == text
```

Or for serialization/deserialization:

```py
import json

@given(st.dictionaries(st.text(), st.one_of(st.integers(), st.text(), st.booleans())))
def test_json_roundtrip(data):
    serialized = json.dumps(data)
    deserialized = json.loads(serialized)
    assert deserialized == data
```

## Invariants

Properties that should always be true, regardless of input:

```py
@given(st.lists(st.integers()))
def test_sort_is_ordered(xs):
    sorted_xs = sorted(xs)
    for i in range(len(sorted_xs) - 1):
        assert sorted_xs[i] <= sorted_xs[i + 1]

@given(st.lists(st.integers()))
def test_sort_preserves_elements(xs):
    sorted_xs = sorted(xs)
    assert set(xs) == set(sorted_xs)
    assert len(xs) == len(sorted_xs)
```

# Tips and Best Practices

## Configuration

You can configure how Hypothesis runs your tests:

```py
from hypothesis import settings, given
from hypothesis import strategies as st

@settings(max_examples=200, deadline=500)  # Run 200 examples, allow 500ms per test
@given(st.lists(st.integers()))
def test_blah(xs):
    pass
```

Common settings:

- `max_examples`: How many examples to try (default: 100)
- `deadline`: Maximum time per test in milliseconds
- `seed`: Random seed for reproducible test runs

For example, for reproducible test runs you can set the random seed like this:

```py
@settings(seed=42)
@given(st.lists(st.integers()))
def test_deterministic(xs):
    pass
```

## Using `assume()` for Conditional Tests

Sometimes you want to skip certain inputs that aren't relevant to the property you're testing:

```py
from hypothesis import assume

@given(st.integers(), st.integers())
def test_division(a, b):
    assume(b != 0)  # Skip test cases where b is 0
    result = a / b
    assert isinstance(result, (int, float))
```

`assume()` tells Hypothesis to skip this example and try another one.

# Summary

Property-based testing helps you find bugs you didn't know to look for, think more rigorously about your code and the properties it should maintain, document that behavior as an executable specification, and catch and record regressions.

Check out the [Hypothesis documentation](https://hypothesis.readthedocs.io/) for more.

