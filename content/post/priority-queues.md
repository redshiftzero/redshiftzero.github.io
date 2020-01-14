+++
date = "2020-01-13"
title = "Handling equal priority jobs using queue.PriorityQueue"
slug = "priority-queue"
categories = [ "Post", "Software Development"]
tags = [ "data structures", "queue", "python" ]
+++

A queue retrives items in FIFO (first in, first out) order. A priority queue retrieves item based on _priority_, higher priority items come first. Well, what happens if you submit items that have equal priorities? It depends on how the priority queue was implemented. Read on for how this is handled in the Python standard library's  `queue.PriorityQueue`.

Let's see `queue.PriorityQueue` in action in a simple case:

```py
>>> from queue import PriorityQueue
>>> q = PriorityQueue()
>>> q.put((1, 'A'))
>>> q.put((2, 'B'))
>>> q.put((3, 'C'))
>>> q.get()
(1, 'A')
>>> q.get()
(2, 'B')
>>> q.get()
(3, 'C')
>>> q.empty()
True
```

As we can see, we've put `(priority_number, data)` into the queue, and retrieved them using the `get()` method. We see that lower numbers correspond to higher priorities. 

Let's now add some jobs with equal priorities and retrieve them:

```py
>>> q.put((1, 'My first job'))
>>> q.put((1, 'Another job'))
>>> q.get()
(1, 'Another job')
>>> q.get()
(1, 'My first job')
```

We did not retrieve items in FIFO order for jobs of equal priority: `'Another job'` was fetched prior to `'My first job'` even though it was added afterwards. Why does this happen?

## Using a min-heap for `queue.PriorityQueue`

The short version is that we grabbed `'Another job'` first, because `'Another job' < 'My first job'` alphabetically.

The longer version is that under the hood, `queue.PriorityQueue` is implemented using `heapq`, Python's heap implementation. Every job is an element in a min-heap. A min-heap is a complete binary tree that satisfies the min-heap propety: the value of each node is greater than or equal to the value of its parent. The root element will be the node with the minimum value. So to get the next job we want to run, we just [grab the element at the top of the min-heap](https://github.com/python/cpython/blob/b2b4a51f7463a0392456f7772f33223e57fa4ccc/Lib/heapq.py#L139), which due to the min-heap property, we know will be the job with the minimum priority value - which remember from above corresponds to the _higher_ priority.

But where is this comparison done: `'Another job' < 'My first job'`? During heap operations, elements are compared with one another (and swapped if needed). In Python, this is done using [the rich comparison operator `__lt__`](https://github.com/python/cpython/blob/b2b4a51f7463a0392456f7772f33223e57fa4ccc/Lib/heapq.py#L264). `'Another job'` will bubble to the top of the heap since `'Another job' < 'My first job'`.

## How we can solve this

Here's an approach I used for Python 3.5 (the version of Python I was writing for when I looked into using [this functionality](https://github.com/freedomofpress/securedrop-client/blob/master/securedrop_client/api_jobs/base.py#L24)). For the application I was working on, I needed to retrieve items based on priority, and for items of equal priority, I needed to retrieve items in FIFO order.

One simple approach if you hit this problem is following [a suggestion in the `heapq` documentation](https://docs.python.org/3/library/heapq.html#priority-queue-implementation-notes): "store entries as 3-element list including the priority, an entry count, and the task", where the entry count is a tie-breaker for jobs of equal priority. Let's see that demonstrated:

```py
>>> q.put((1, 1, 'My next job'))
>>> q.put((1, 2, 'Another job'))
>>> q.get()
(1, 1, 'My next job')
>>> q.get()
(1, 2, 'Another job')
```

In my situation, I was working in a codebase that had already a mediator interface to submit jobs (to `queue.PriorityQueue`), and job objects themselves were separate objects (i.e. not simple strings in the real applicatoin). I ended up making jobs sortable using the following superclass that implemented the `__lt__` rich comparison method:

```py
from typing import TypeVar

QueueJobType = TypeVar('QueueJobType', bound='QueueJob')


class QueueJob():
    def __init__(self, order_number: int, task: str) -> None:
        self.order_number = order_number
        self.task = task

    def __lt__(self, other: QueueJobType) -> bool:
        '''
        We need to use the order_number key to break ties to ensure
        that objects are retrieved in FIFO order.
        '''
        return self.order_number < other.order_number

    def __repr__(self) -> str:
        return self.task
```

When I submitted jobs, I'd do so using an interface like this (application simplified for demonstration purposes, more context is [here](https://github.com/freedomofpress/securedrop-client/blob/master/securedrop_client/queue.py)) that would set the `order_number` such that it would be monotonically increasing:

```py
import itertools
import queue


class App():
    def __init__(self):
        self.order_number = itertools.count()
        self.queue = queue.PriorityQueue()

    def add_task(self, priority: int, task: str):
        current_order_number = next(self.order_number)
        task = QueueJob(current_order_number, task)
        self.queue.put((priority, task))
```

Let's see if jobs with equal priorities are retrieved in FIFO order:

```py
>>> from stuff import App
>>> app = App()
>>> app.add_task(1, 'My first job')
>>> app.add_task(1, 'Another job')
>>> app.queue.get()
(1, My first job)
>>> app.queue.get()
(1, Another job)
```

Jobs with equal priorities are retrieved in FIFO order, which is what we wanted. 
