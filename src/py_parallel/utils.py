import uuid
from multiprocessing import Process


def generate_unique_id() -> str:
    return uuid.uuid4().hex


def terminate_process_with_timeout(process: Process, timeout: int):
    try:
        process.terminate()
        process.join(timeout)
    except TimeoutError:
        process.kill()
