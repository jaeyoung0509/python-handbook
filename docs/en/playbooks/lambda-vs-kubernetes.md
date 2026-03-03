# Lambda vs Kubernetes

<p class="lead">The common mistake in deployment decisions is to treat hosting as an afterthought once the code already exists. In practice, traffic shape, cold-start tolerance, database connection strategy, long-lived connections, workers, and observability requirements all affect whether Lambda or Kubernetes will hurt less.</p>

<div class="quick-takeaway">
  <p><strong>Quick takeaway</strong>: Lambda fits bursty event-driven workloads with short request lifecycles and a low ops surface. Kubernetes fits long-lived APIs, websockets and streaming, bounded connection pools, sidecars, and tighter runtime control. Database strategy is often the deciding factor.</p>
</div>

## Questions to Answer First

1. Is the traffic bursty or steady?
2. How much cold-start or startup latency can you tolerate?
3. Do you need long-lived connections, workers, or schedulers?
4. How will you control the database connection budget?
5. Do you need sidecars, agents, or custom networking behavior?

## A Quick Decision Flow

<MermaidDiagram
  caption="There is no universal winner. The right answer follows workload shape, operational model, and database strategy."
  chart="flowchart TD; A[Start] --> B{Bursty or event-driven?}; B -->|Yes| C{Short-lived request and minimal ops?}; C -->|Yes| D[Lean toward Lambda]; C -->|No| E[Re-evaluate workload shape]; B -->|No| F{Need long-lived connections, workers, or tight pool control?}; F -->|Yes| G[Lean toward Kubernetes]; F -->|No| H[Compare cost and latency targets];"
/>

## Comparison Table

| Question | Lambda tends to win when | Kubernetes tends to win when |
| --- | --- | --- |
| scaling model | request and event driven auto-scaling is enough | you want direct control over replicas, workers, and autoscaling |
| runtime lifetime | short invocation-shaped execution is fine | you want long-lived processes or pods |
| startup behavior | occasional cold starts are acceptable | you want warmer, more predictable process lifetimes |
| database connections | `NullPool` plus RDS Proxy fits the workload | bounded `QueuePool` plus explicit connection budgeting matters |
| websockets and streaming | constraints or workarounds are acceptable | long-lived connections are first-class requirements |
| sidecars and agents | not needed | service mesh, OTEL collectors, or log agents matter |
| background workers | separate services are acceptable | API plus workers plus schedulers should share one platform |
| operational surface | the team wants less infrastructure control | the team accepts more ops in exchange for more control |

## When Lambda Is the Better First Bet

- the workload is event-driven or highly bursty
- the team prioritizes lower infrastructure overhead
- request lifecycles are short and mostly stateless
- database access can be stabilized with RDS Proxy or a similar layer

## When Kubernetes Is the Better First Bet

- traffic is steady and latency predictability matters
- the service needs websockets, SSE, streaming, or long-lived workers
- sidecars, service mesh, or deeper observability integration are important
- connection pool sizing, worker count, and rollout control all matter together

## The Database Story Changes the Decision

### Lambda

- concurrency spreads across execution environments
- large in-process pools are often less useful than `NullPool`
- initialize the engine outside the handler, but create a fresh session per invocation
- RDS Proxy can soften connection storms significantly

### Kubernetes

- always do the math: `replicas * workers * (pool_size + max_overflow)`
- keep pools bounded and fail fast under saturation
- lifecycle management, shutdown, and rollout behavior all interact with engine disposal

## Practical Selection Guide

### Workloads that lean Lambda

- webhook receivers
- smaller CRUD APIs with burst traffic
- event consumers and scheduled jobs
- teams with small ops capacity and few sidecar needs

### Workloads that lean Kubernetes

- high-throughput APIs
- websocket or streaming gateways
- teams that want APIs, workers, schedulers, and observability agents on one platform
- services that need explicit control of pool size, worker count, and rollout shape

### Hybrid is common

- public API on Lambda
- long-lived workers or consumers on Kubernetes
- or the reverse: core API on Kubernetes, bursty jobs on Lambda

## Avoid These Decision Patterns

- choosing between Lambda and Kubernetes from a cost table alone
- separating deployment choice from database connection strategy
- defaulting to Lambda when long-lived streaming is clearly required
- adopting Kubernetes "just in case" before the operational need exists

## Good Companion Chapters

- [Deployment and Engine Settings](/en/sqlalchemy/deployment-and-engine-settings)
- [Performance and Ops](/en/fastapi/performance-and-ops)
- [Settings and Pydantic Settings](/en/playbooks/settings-and-pydantic-settings)

## Official References

- [AWS Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [Using AWS Lambda with Amazon RDS](https://docs.aws.amazon.com/lambda/latest/dg/services-rds.html)
- [Kubernetes Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
- [Horizontal Pod Autoscaling](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)
- [FastAPI Deployment Concepts](https://fastapi.tiangolo.com/deployment/concepts/)
