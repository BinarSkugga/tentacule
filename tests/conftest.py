import pytest

from tentacule.process_pool import ProcessPool


@pytest.fixture(scope="session")
def pool():
    pool = ProcessPool(workers=3)
    try:
        pool.start()
        yield pool
    finally:
        pool.close(True)
