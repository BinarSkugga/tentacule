from tests.depency import subtract


def simple_function():
    return 5


def test_simple_function(pool):
    assert pool.submit_and_fetch(simple_function) == 5


def add(a: int, b: int):
    return a + b


def test_simple_function_with_args(pool):
    assert pool.submit_and_fetch(add, 6, 7) == 13


def test_simple_function_with_kwargs(pool):
    assert pool.submit_and_fetch(add, a=5, b=5) == 10


def default_a(a: int = 0):
    return a


def test_simple_function_with_default(pool):
    assert pool.submit_and_fetch(default_a) == 0
    assert pool.submit_and_fetch(default_a, 80) == 80


def recurse(a: int = 0):
    if a == 10:
        return a
    return recurse(a + 1)


def test_recursive(pool):
    assert pool.submit_and_fetch(recurse) == 10


def dependency_subtract(a: int, b: int):
    return subtract(a, b)


def test_function_with_dependency(pool):
    assert pool.submit_and_fetch(dependency_subtract, 7, 2) == 5


def generator_function(max: int = 10):
    for i in range(max):
        yield i


def test_generator_function(pool):
    expected_val = 0
    for result in pool.submit_and_stream(generator_function):
        assert result == expected_val
        expected_val += 1

    assert expected_val == 10
