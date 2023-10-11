from tests.depency import subtract


def simple_function():
    return 5


def test_simple_function(pool):
    task_id = pool.new_task(simple_function)

    assert pool.get_result(task_id) == 5


def add(a: int, b: int):
    return a + b


def test_simple_function_with_args(pool):
    task_id = pool.new_task(add, 6, 7)

    assert pool.get_result(task_id) == 13


def test_simple_function_with_kwargs(pool):
    task_id = pool.new_task(add, a=5, b=5)

    assert pool.get_result(task_id) == 10


def default_a(a: int = 0):
    return a


def test_simple_function_with_default(pool):
    task_id = pool.new_task(default_a)
    assert pool.get_result(task_id) == 0

    task_id = pool.new_task(default_a, 80)
    assert pool.get_result(task_id) == 80


def recurse(a: int = 0):
    if a == 10:
        return a
    return recurse(a + 1)


def test_recursive(pool):
    task_id = pool.new_task(recurse)
    assert pool.get_result(task_id) == 10


def dependency_subtract(a: int, b: int):
    return subtract(a, b)


def test_function_with_dependency(pool):
    task_id = pool.new_task(dependency_subtract, 7, 2)
    assert pool.get_result(task_id) == 5
