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

task_id = pool.submit(task, 3)
result = pool.fetch(task_id)  # 5

pool.close()
```

You can also do this in a single step:
```python
pool = ProcessPool(workers=3)
pool.start()

def task(arg: int):
    return 2 + arg

result = pool.submit_and_fetch(task, 5)  # 7

pool.close()
```

It is possible to stream a generator from a process:
```python
pool = ProcessPool(workers=3)
pool.start()

def task(max: int = 10):
    for i in range(max):
        yield i

for result in pool.submit_and_stream(task):
    print(result)  # Will print 0 through 9 inclusively

pool.close()
```


## Restrictions
- Anything [dill](https://github.com/uqfoundation/dill) can't pickle, can't be used as a task. 
- Arguments are pickled using the regular pickling for processes.
