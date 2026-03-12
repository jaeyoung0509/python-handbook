# Lambda vs Kubernetes

<p class="lead">배포 대상을 고를 때 가장 흔한 실수는 "코드만 돌면 된다"는 관점이다. 실제로는 트래픽 모양, cold start 허용치, DB 연결 방식, long-lived connection, background worker, observability agent 같은 운영 조건이 먼저 결정되고, 그 다음에 Lambda와 Kubernetes 중 어느 쪽이 덜 아픈지가 갈린다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: spiky한 event-driven workload, 작은 운영 표면적, 짧은 request lifecycle이면 Lambda가 잘 맞고, long-lived API, websocket/streaming, bounded connection pool, sidecar/agent, 정교한 리소스 제어가 중요하면 Kubernetes가 더 자연스럽다. DB connection strategy는 이 선택을 크게 좌우한다.</p>
</div>

## 먼저 답해야 할 질문

1. 트래픽이 bursty한가, steady한가
2. cold start와 startup latency를 얼마나 허용할 수 있는가
3. websocket, streaming, background worker 같은 long-lived process가 필요한가
4. DB connection budget을 어떻게 관리할 것인가
5. sidecar, daemon, custom networking, observability agent가 필요한가

## 빠른 결정 흐름

<MermaidDiagram
  caption="정답은 하나가 아니라 workload shape에 따라 갈린다. 운영 모델과 DB 전략이 함께 움직여야 한다."
  chart="flowchart TD; A[Start] --> B{Bursty or event-driven?}; B -->|Yes| C{Short-lived request and minimal ops?}; C -->|Yes| D[Lean toward Lambda]; C -->|No| E[Re-evaluate workload shape]; B -->|No| F{Need long-lived connections, workers, or tight pool control?}; F -->|Yes| G[Lean toward Kubernetes]; F -->|No| H[Compare cost and latency targets];"
/>

## 비교 표

| 질문 | Lambda가 유리한 경우 | Kubernetes가 유리한 경우 |
| --- | --- | --- |
| 확장 모델 | 요청/이벤트 기반 자동 확장 | replica / HPA / worker 수를 직접 조절 |
| 런타임 수명 | invocation 중심의 짧은 실행 | long-lived pod/process |
| startup 특성 | cold start를 감수 가능 | 더 예측 가능한 warm process 유지 |
| DB 연결 | RDS Proxy, `NullPool` 중심 | bounded `QueuePool`, connection budget 계산 |
| websocket/streaming | 제약이 크거나 우회가 필요 | 장기 연결을 직접 다루기 쉬움 |
| sidecar/agent | 어려움 | envoy, otel collector, log agent 등과 잘 맞음 |
| background worker | 별도 서비스 분리가 필요 | API + worker + scheduler를 한 플랫폼에서 운영 가능 |
| 운영 표면적 | 작다 | 크지만 제어권이 높다 |

## Lambda를 먼저 보는 게 좋은 경우

- 이벤트 기반 처리나 burst traffic이 많다
- 팀이 인프라 운영보다 기능 개발 속도를 더 우선한다
- 요청 수명주기가 짧고 상태가 거의 없다
- DB 연결을 RDS Proxy 같은 외부 계층으로 안정화할 수 있다

## Kubernetes를 먼저 보는 게 좋은 경우

- steady traffic과 예측 가능한 latency가 중요하다
- websocket, SSE, streaming, long polling, background worker가 필요하다
- sidecar, service mesh, custom networking, observability agent가 중요하다
- replica 수, worker 수, DB pool을 같이 계산해야 한다

## DB 관점에서 차이가 크게 난다

### Lambda

- concurrency가 execution environment 수로 퍼진다
- 앱 내부에서 큰 connection pool을 두기보다 `NullPool`이 단순한 경우가 많다
- engine은 handler 밖에서 초기화하고, session은 invocation마다 만든다
- RDS를 직접 치는 대신 RDS Proxy를 붙이면 connection storm를 완화하기 쉽다

### Kubernetes

- `replicas * workers * (pool_size + max_overflow)`를 실제로 계산해야 한다
- DB pool을 bounded하게 유지하고 saturation을 빨리 드러내야 한다
- pod shutdown과 startup에서 `engine.dispose()` / readiness / rollout 전략을 함께 봐야 한다

## 실전 선택 가이드

### Lambda 쪽으로 기우는 서비스

- webhook receiver
- 작은 CRUD API with burst traffic
- event consumer / scheduled job
- 운영 인력이 작고 sidecar 요구가 적은 팀

### Kubernetes 쪽으로 기우는 서비스

- high-throughput API
- websocket or streaming gateway
- API + worker + cron + observability agent를 한 플랫폼에서 묶고 싶은 팀
- connection pool, worker count, rollout을 세밀하게 제어해야 하는 서비스

### hybrid도 흔하다

- public API는 Lambda
- background worker와 long-lived consumer는 Kubernetes
- 혹은 반대로 core API는 Kubernetes, 간헐성 작업은 Lambda

## 하지 않는 편이 좋은 것

- Lambda와 Kubernetes를 비용표 한 장만 보고 고르는 것
- DB connection strategy를 배포 결정과 분리해 생각하는 것
- websocket/streaming 요구가 있는데도 Lambda를 기본값처럼 택하는 것
- 운영 표면적이 큰데도 Kubernetes를 "언젠가 필요할 것 같아서" 먼저 도입하는 것

## 운영 시나리오로 점검하기

| symptom | 먼저 볼 것 | likely root cause | safe mitigation | what not to do |
| --- | --- | --- | --- | --- |
| burst traffic 때는 잘 버티는데 DB connection이 먼저 죽는다 | traffic shape보다 DB 연결 방식과 pool strategy를 먼저 본다 | Lambda/Kubernetes 선택은 맞아도 connection strategy가 workload와 안 맞는다 | RDS Proxy, bounded pool, worker math 등 DB 전략부터 다시 맞춘다 | 플랫폼만 다시 바꾸면 해결될 거라고 본다 |
| product가 WebSocket/SSE를 요구하는데 운영 복잡도는 최소화하고 싶다 | long-lived connection이 핵심 요구인지부터 본다 | short-lived request 모델인 Lambda에 long-lived requirement를 억지로 올리려 한다 | realtime path는 Kubernetes 또는 별도 stateful runtime으로 분리한다 | workaround를 계속 쌓아 Lambda 하나에 모두 우겨넣는다 |
| observability agent, sidecar, cron, worker를 같이 운영해야 한다 | sidecar/daemon/custom networking 요구를 먼저 본다 | hosting 결정을 API latency만으로 해버렸다 | platform choice를 API + worker + agent 묶음의 운영 모델로 다시 평가한다 | "API만 보면 되니까"라며 worker와 운영 도구를 나중 문제로 미룬다 |

## Code Review Lens

- hosting choice를 비용표보다 workload shape와 운영 조건으로 설명하는지 본다.
- long-lived connection, worker, scheduler, sidecar 요구가 decision input에 포함되는지 본다.
- DB connection strategy가 platform choice와 같이 논의되는지 본다.
- hybrid 선택이 오히려 단순해지는 경계를 인정하는지 본다.

## Common Anti-Patterns

- Lambda와 Kubernetes를 "serverless vs containers" 정도의 표면적 비교로 끝낸다.
- steady traffic과 websocket 요구가 있는데도 낮은 ops surface만 보고 Lambda를 고른다.
- 운영 필요가 아직 없는데도 미래를 핑계로 Kubernetes를 과하게 앞당긴다.
- API hosting 결정과 worker/scheduler/observability 운영 모델을 분리해 생각한다.

## Likely Discussion Questions

- 어떤 신호가 Lambda보다 Kubernetes 쪽으로 무게를 확실히 옮기는가?
- hybrid architecture가 오히려 덜 복잡해지는 시점은 언제인가?
- hosting 결정에서 DB connection budget이 왜 가장 먼저 나와야 하는가?
- sidecar, service mesh, OTEL agent 요구가 설계에 미치는 영향은 무엇인가?

## Strong Answer Frame

- 먼저 traffic shape, request lifetime, realtime 요구, 운영 표면적을 입력값으로 둔다.
- 그 다음 DB connection strategy와 worker model을 hosting decision과 함께 설명한다.
- Lambda, Kubernetes, hybrid를 각각 언제 덜 아픈 선택인지 비교한다.
- 마지막에 팀의 운영 역량과 blast radius를 같이 언급해 결정을 닫는다.

## 같이 읽으면 좋은 페이지

- [Deployment and Engine Settings](/sqlalchemy/deployment-and-engine-settings)
- [Performance and Ops](/fastapi/performance-and-ops)
- [Settings and Pydantic Settings](/playbooks/settings-and-pydantic-settings)
- [Progressive Delivery + Alembic](/playbooks/progressive-delivery-and-alembic)

## 공식 자료

- [AWS Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [Using AWS Lambda with Amazon RDS](https://docs.aws.amazon.com/lambda/latest/dg/services-rds.html)
- [Kubernetes Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
- [Horizontal Pod Autoscaling](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)
- [FastAPI Deployment Concepts](https://fastapi.tiangolo.com/deployment/concepts/)
