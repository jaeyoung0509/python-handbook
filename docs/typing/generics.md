# Generics

<p class="lead">generic을 이해하면 라이브러리 API가 왜 그렇게 설계되는지 읽을 수 있고, 직접 설계할 때도 훨씬 덜 흔들린다. generic의 목적은 "어려운 타입 수학"보다 "타입 정보를 잃지 않고 재사용 가능한 API를 만드는 것"에 있다.</p>

<div class="quick-takeaway">
  <p><strong>빠른 요약</strong>: generic은 `Any`로 타입 정보를 포기하지 않고도 재사용 가능한 코드를 만들게 해준다. Python 3.12+ 타입 파라미터 문법 덕분에 이제는 generic 선언도 코드에 자연스럽게 녹아든다.</p>
</div>

## 제네릭이 필요한 순간

<MermaidDiagram
  caption="generic은 입력 타입 정보를 함수나 클래스 경계를 지나서 결과 타입까지 보존하는 장치다."
  chart="flowchart LR; A[input type T] --> B[generic function or class]; B --> C[output still typed as T];"
/>

## 타입 파라미터 문법 예제

```py
class Box[T]:
    def __init__(self, value: T) -> None:
        self.value = value

    def unwrap(self) -> T:
        return self.value


def first[T](items: list[T]) -> T:
    return items[0]


type Row[T] = dict[str, T]


print(Box("python").unwrap())
print(first([1, 2, 3]))
print(Row[int])
```

## TypeVar를 아직 알아야 하는 이유

- 새 문법이 생겨도 generic의 개념적 중심은 여전히 type variable이다.
- 기존 라이브러리와 문서에는 `TypeVar`, `Generic` 기반 코드가 많다.
- variance, bound, constraint 같은 개념은 여전히 TypeVar 언어로 설명되는 경우가 많다.

## variance는 어디까지 알면 되나

- 대부분의 앱 개발은 invariant collection 감각만 잘 알아도 충분하다.
- `list[Derived]`가 `list[Base]`의 subtype이 아니라는 점은 꼭 알아야 한다.
- library author나 protocol-heavy 설계에서 covariance/contravariance가 더 중요해진다.

## 실전 연결

- repository abstraction
- typed container/helper
- Pydantic generic model

## 체크리스트

<div class="doc-checklist">
  <div class="check-card">
    <h3>generic이 정말 정보 보존에 필요한가</h3>
    <p>항상 generic이 필요한 건 아니다. 입력과 출력 타입을 연결해야 할 때 가장 가치가 크다.</p>
  </div>
  <div class="check-card">
    <h3>`Any` 대신 generic을 쓰는가</h3>
    <p>재사용 API가 타입 정보를 잃지 않게 하려면 generic이 훨씬 낫다.</p>
  </div>
  <div class="check-card">
    <h3>복잡한 variance를 남발하지 않는가</h3>
    <p>앱 코드에서 variance를 지나치게 전면에 세우면 가독성이 떨어질 수 있다.</p>
  </div>
  <div class="check-card">
    <h3>선언 위치가 읽기 좋은가</h3>
    <p>새 타입 파라미터 문법은 generic 의도를 정의부에서 바로 보이게 해준다.</p>
  </div>
</div>

## 공식 자료

- [typing generics](https://docs.python.org/3/library/typing.html)
- [PEP 695: Type Parameter Syntax](https://peps.python.org/pep-0695/)
