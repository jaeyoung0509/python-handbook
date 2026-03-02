import { defineConfig } from "vitepress";

type LocaleCode = "ko" | "en";

type NavSection = {
  ko: string;
  en: string;
  navPath: string;
  items: Array<{
    ko: string;
    en: string;
    path: string;
  }>;
};

const sections: NavSection[] = [
  {
    ko: "입문",
    en: "Intro",
    navPath: "/intro/",
    items: [
      { ko: "개요", en: "Overview", path: "/intro/" },
      { ko: "왜 이 문서를 새로 쓰는가", en: "Why This Book", path: "/intro/why-this-book" },
      { ko: "이 문서를 읽는 법", en: "How To Read", path: "/intro/how-to-read" },
      {
        ko: "Python 3.10~3.14 정리",
        en: "Python 3.10~3.14 Deep Dive",
        path: "/python-3.10-3.14-deep-dive",
      },
    ],
  },
  {
    ko: "Pythonic",
    en: "Pythonic",
    navPath: "/pythonic/",
    items: [
      { ko: "개요", en: "Overview", path: "/pythonic/" },
      { ko: "Data Model", en: "Data Model", path: "/pythonic/data-model" },
      { ko: "Dataclass", en: "Dataclasses", path: "/pythonic/dataclasses" },
      {
        ko: "Descriptor와 Property",
        en: "Descriptors and Properties",
        path: "/pythonic/descriptors-and-properties",
      },
      { ko: "Decorator", en: "Decorators", path: "/pythonic/decorators" },
      { ko: "Context Manager", en: "Context Managers", path: "/pythonic/context-managers" },
      { ko: "Metaclass", en: "Metaclasses", path: "/pythonic/metaclasses" },
    ],
  },
  {
    ko: "Typing",
    en: "Typing",
    navPath: "/typing/",
    items: [
      { ko: "개요", en: "Overview", path: "/typing/" },
      { ko: "현대 Python Typing", en: "Modern Typing", path: "/typing/modern-typing" },
      { ko: "Generics", en: "Generics", path: "/typing/generics" },
      { ko: "Protocol", en: "Protocols", path: "/typing/protocols" },
      { ko: "Type Narrowing", en: "Type Narrowing", path: "/typing/type-narrowing" },
      { ko: "런타임 vs 정적 타입", en: "Runtime vs Static", path: "/typing/runtime-vs-static" },
    ],
  },
  {
    ko: "런타임",
    en: "Runtime",
    navPath: "/runtime/",
    items: [
      { ko: "개요", en: "Overview", path: "/runtime/" },
      { ko: "Execution Model", en: "Execution Model", path: "/runtime/execution-model" },
      { ko: "Object Model", en: "Object Model", path: "/runtime/object-model" },
      { ko: "Memory와 GC", en: "Memory and GC", path: "/runtime/memory-and-gc" },
      { ko: "GIL과 Subinterpreter", en: "GIL and Subinterpreters", path: "/runtime/gil-and-subinterpreters" },
      {
        ko: "Bytecode와 Specialization",
        en: "Bytecode and Specialization",
        path: "/runtime/bytecode-and-specialization",
      },
      { ko: "CPython vs Go Runtime", en: "CPython vs Go Runtime", path: "/cpython-vs-go-runtime" },
    ],
  },
  {
    ko: "Asyncio",
    en: "Asyncio",
    navPath: "/asyncio/",
    items: [
      { ko: "개요", en: "Overview", path: "/asyncio/" },
      { ko: "Event Loop와 Task", en: "Event Loop and Tasks", path: "/asyncio/event-loop-and-tasks" },
      { ko: "Cancellation과 TaskGroup", en: "Cancellation and TaskGroup", path: "/asyncio/cancellation-and-taskgroup" },
      { ko: "Queue와 Backpressure", en: "Queues and Backpressure", path: "/asyncio/queues-and-backpressure" },
      { ko: "테스트와 디버깅", en: "Testing and Debugging", path: "/asyncio/testing-and-debugging" },
    ],
  },
  {
    ko: "FastAPI",
    en: "FastAPI",
    navPath: "/fastapi/",
    items: [
      { ko: "개요", en: "Overview", path: "/fastapi/" },
      { ko: "프로젝트 구조", en: "Project Structure", path: "/fastapi/project-structure" },
      { ko: "의존성 주입", en: "Dependency Injection", path: "/fastapi/dependency-injection" },
      { ko: "요청/응답 모델링", en: "Request/Response Modeling", path: "/fastapi/request-response-modeling" },
      { ko: "Lifespan과 테스트", en: "Lifespan and Testing", path: "/fastapi/lifespan-and-testing" },
      { ko: "성능과 운영", en: "Performance and Ops", path: "/fastapi/performance-and-ops" },
      { ko: "Observability", en: "Observability", path: "/fastapi/observability" },
    ],
  },
  {
    ko: "Pydantic",
    en: "Pydantic",
    navPath: "/pydantic/",
    items: [
      { ko: "개요", en: "Overview", path: "/pydantic/" },
      { ko: "Core Schema", en: "Core Schema", path: "/pydantic/core-schema" },
      { ko: "Validation Pipeline", en: "Validation Pipeline", path: "/pydantic/validation-pipeline" },
      { ko: "BaseModel vs TypeAdapter", en: "BaseModel vs TypeAdapter", path: "/pydantic/basemodel-vs-typeadapter" },
      { ko: "Internals", en: "Internals", path: "/pydantic/internals" },
    ],
  },
  {
    ko: "SQLAlchemy",
    en: "SQLAlchemy 2.0",
    navPath: "/sqlalchemy/",
    items: [
      { ko: "개요", en: "Overview", path: "/sqlalchemy/" },
      { ko: "Core vs ORM", en: "Core vs ORM", path: "/sqlalchemy/core-vs-orm" },
      { ko: "Session과 Unit of Work", en: "Session and Unit of Work", path: "/sqlalchemy/session-and-unit-of-work" },
      { ko: "관계와 로딩 전략", en: "Relationships and Loading", path: "/sqlalchemy/relationships-and-loading" },
      { ko: "Async SQLAlchemy", en: "Async SQLAlchemy", path: "/sqlalchemy/async-sqlalchemy" },
      { ko: "마이그레이션과 패턴", en: "Migrations and Patterns", path: "/sqlalchemy/migrations-and-patterns" },
    ],
  },
  {
    ko: "플레이북",
    en: "Playbooks",
    navPath: "/playbooks/",
    items: [
      { ko: "개요", en: "Overview", path: "/playbooks/" },
      { ko: "API 서비스 템플릿", en: "API Service Template", path: "/playbooks/api-service-template" },
      {
        ko: "Testing with Fixtures",
        en: "Testing with Fixtures",
        path: "/playbooks/testing-with-pytest-fixtures",
      },
      {
        ko: "Use Case + UoW + Interface",
        en: "Use Case + UoW + Interface",
        path: "/playbooks/usecase-uow-and-interfaces",
      },
      {
        ko: "FastAPI + Pydantic + SQLAlchemy",
        en: "FastAPI + Pydantic + SQLAlchemy",
        path: "/playbooks/fastapi-pydantic-sqlalchemy",
      },
      { ko: "Typing 리뷰 체크리스트", en: "Typing Review Checklist", path: "/playbooks/typing-review-checklist" },
    ],
  },
];

const withLocalePrefix = (locale: LocaleCode, path: string) =>
  locale === "en" ? `/en${path}` : path;

const buildNav = (locale: LocaleCode) =>
  sections.map((section) => ({
    text: locale === "ko" ? section.ko : section.en,
    link: withLocalePrefix(locale, section.navPath),
  }));

const buildSidebar = (locale: LocaleCode) =>
  sections.map((section) => ({
    text: locale === "ko" ? section.ko : section.en,
    items: section.items.map((item) => ({
      text: locale === "ko" ? item.ko : item.en,
      link: withLocalePrefix(locale, item.path),
    })),
  }));

const searchConfig = {
  provider: "local" as const,
  options: {
    locales: {
      root: {
        translations: {
          button: {
            buttonText: "검색",
            buttonAriaLabel: "문서 검색",
          },
          modal: {
            displayDetails: "상세 보기",
            resetButtonTitle: "검색 초기화",
            backButtonTitle: "검색 닫기",
            noResultsText: "검색 결과가 없습니다",
            footer: {
              selectText: "선택",
              selectKeyAriaLabel: "enter",
              navigateText: "이동",
              navigateUpKeyAriaLabel: "위 화살표",
              navigateDownKeyAriaLabel: "아래 화살표",
              closeText: "닫기",
              closeKeyAriaLabel: "escape",
            },
          },
        },
      },
      en: {
        translations: {
          button: {
            buttonText: "Search",
            buttonAriaLabel: "Search docs",
          },
          modal: {
            displayDetails: "Display detailed list",
            resetButtonTitle: "Reset search",
            backButtonTitle: "Close search",
            noResultsText: "No results for this query",
            footer: {
              selectText: "Select",
              selectKeyAriaLabel: "enter",
              navigateText: "Navigate",
              navigateUpKeyAriaLabel: "arrow up",
              navigateDownKeyAriaLabel: "arrow down",
              closeText: "Close",
              closeKeyAriaLabel: "escape",
            },
          },
        },
      },
    },
  },
};

const sharedThemeConfig = {
  siteTitle: "Python Handbook",
  logo: {
    light: "/mark.svg",
    dark: "/mark.svg",
  },
  i18nRouting: true,
  search: searchConfig,
  socialLinks: [
    { icon: "github", link: "https://github.com/jaeyoung0509/python-handbook" },
  ],
};

export default defineConfig({
  title: "Python Handbook",
  description:
    "Python 3.14, typing, CPython runtime, asyncio, FastAPI, Pydantic, and SQLAlchemy 2.0.",
  base: "/python-handbook/",
  cleanUrls: true,
  lastUpdated: true,
  head: [
    ["meta", { name: "theme-color", content: "#0f766e" }],
    ["meta", { property: "og:type", content: "website" }],
    ["meta", { property: "og:title", content: "Python Handbook" }],
    [
      "meta",
      {
        property: "og:description",
        content:
          "Python 3.14, typing, runtime, asyncio, FastAPI, Pydantic, SQLAlchemy 2.0을 한 흐름으로 읽는 핸드북",
      },
    ],
  ],
  themeConfig: sharedThemeConfig,
  locales: {
    root: {
      label: "한국어",
      lang: "ko-KR",
      title: "Python Handbook",
      description:
        "Python 3.14, typing, CPython runtime, asyncio, FastAPI, Pydantic, SQLAlchemy 2.0을 한 흐름으로 읽는 한국어 핸드북",
      themeConfig: {
        nav: buildNav("ko"),
        sidebar: buildSidebar("ko"),
        editLink: {
          pattern: "https://github.com/jaeyoung0509/python-handbook/edit/main/docs/:path",
          text: "GitHub에서 이 페이지 수정하기",
        },
        outline: {
          level: [2, 3],
          label: "이 페이지에서",
        },
        lastUpdatedText: "마지막 업데이트",
        sidebarMenuLabel: "메뉴",
        returnToTopLabel: "맨 위로",
        darkModeSwitchLabel: "테마",
        lightModeSwitchTitle: "라이트 모드로 전환",
        darkModeSwitchTitle: "다크 모드로 전환",
        skipToContentLabel: "본문으로 건너뛰기",
        docFooter: {
          prev: "이전 페이지",
          next: "다음 페이지",
        },
        footer: {
          message: "VitePress로 빌드한 Python 3.14 핸드북",
          copyright: "Copyright © 2026 jaeyoung0509",
        },
      },
    },
    en: {
      label: "English",
      lang: "en-US",
      link: "/en/",
      title: "Python Handbook",
      description:
        "A practical Python 3.14 handbook for typing, CPython internals, asyncio, FastAPI, Pydantic, and SQLAlchemy 2.0.",
      themeConfig: {
        nav: buildNav("en"),
        sidebar: buildSidebar("en"),
        editLink: {
          pattern: "https://github.com/jaeyoung0509/python-handbook/edit/main/docs/:path",
          text: "Edit this page on GitHub",
        },
        outline: {
          level: [2, 3],
          label: "On this page",
        },
        lastUpdatedText: "Last updated",
        sidebarMenuLabel: "Menu",
        returnToTopLabel: "Back to top",
        darkModeSwitchLabel: "Theme",
        lightModeSwitchTitle: "Switch to light mode",
        darkModeSwitchTitle: "Switch to dark mode",
        skipToContentLabel: "Skip to content",
        docFooter: {
          prev: "Previous page",
          next: "Next page",
        },
        footer: {
          message: "Built with VitePress for a Python 3.14 handbook.",
          copyright: "Copyright © 2026 jaeyoung0509",
        },
      },
    },
  },
  markdown: {
    lineNumbers: true,
  },
});
