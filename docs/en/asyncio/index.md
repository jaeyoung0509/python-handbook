# Asyncio

<p class="lead">This section is less about the syntax of `async def` and more about how to run asynchronous systems safely. Event loops, tasks, cancellation, timeouts, backpressure, and debug mode all belong to one operating model.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: good asyncio code is not just "high concurrency." It is code that handles cancellation and cleanup correctly, limits input pressure, and removes hidden blocking I/O.</p>
</div>

## The Questions This Part Builds

<div class="reading-grid">
  <div class="reading-card">
    <h3>When does work become a task?</h3>
    <p>A coroutine object and a scheduled task are not the same thing. You need to know what is actually on the event loop.</p>
  </div>
  <div class="reading-card">
    <h3>Why is cancellation an exception?</h3>
    <p>Cancellation is modeled as exception propagation, so cleanup and re-raising matter a lot.</p>
  </div>
  <div class="reading-card">
    <h3>Why is backpressure mandatory?</h3>
    <p>Unlimited queues and unlimited fan-out make async systems fail through overload rather than through slow code.</p>
  </div>
  <div class="reading-card">
    <h3>How do you debug timing bugs?</h3>
    <p>Async bugs need timeout guards, debug mode, and task-leak checks more than they need clever print statements.</p>
  </div>
</div>

## Recommended Order

1. [Event Loop and Tasks](/en/asyncio/event-loop-and-tasks)
2. [Cancellation and TaskGroup](/en/asyncio/cancellation-and-taskgroup)
3. [Queues and Backpressure](/en/asyncio/queues-and-backpressure)
4. [Testing and Debugging](/en/asyncio/testing-and-debugging)

## Practical Rules

- If you create a task, ownership of waiting, cancellation, and error collection must be clear.
- Do not call blocking functions directly in the event loop.
- Always limit queue size and concurrency.
- Treat timeout and cleanup paths as first-class behavior.
