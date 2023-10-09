# tentacule
Tentacule is an uncomplicated library to deal with a pool of worker processes

## How to install
```
pip install tentacule
```

## How to use
1. Create a pool and start it
2. Send a new task to it
3. Fetch the task result

```python
pool = ProcessPool(workers=3)
pool.start()

def task(arg: int):
    return 2 + arg

task_id = pool.new_task(task, 3)
result = pool.get_result(task_id)  # 5

pool.close()
```