import { defineConfig } from "vitepress";

export default defineConfig({
  lang: "ko-KR",
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
          "Python 3.14부터 typing, runtime, asyncio, FastAPI, Pydantic, SQLAlchemy 2.0까지 깊게 읽는 문서 사이트",
      },
    ],
  ],
  markdown: {
    lineNumbers: true,
  },
  themeConfig: {
    siteTitle: "Python Handbook",
    logo: {
      light: "/mark.svg",
      dark: "/mark.svg",
    },
    nav: [
      { text: "Intro", link: "/intro/" },
      { text: "Pythonic", link: "/pythonic/" },
      { text: "Typing", link: "/typing/" },
      { text: "Runtime", link: "/runtime/" },
      { text: "Asyncio", link: "/asyncio/" },
      { text: "FastAPI", link: "/fastapi/" },
      { text: "Pydantic", link: "/pydantic/" },
      { text: "SQLAlchemy", link: "/sqlalchemy/" },
      { text: "Playbooks", link: "/playbooks/" },
    ],
    sidebar: [
      {
        text: "Intro",
        items: [
          { text: "Overview", link: "/intro/" },
          { text: "Why This Book", link: "/intro/why-this-book" },
          { text: "How To Read", link: "/intro/how-to-read" },
          {
            text: "Python 3.10~3.14 Deep Dive",
            link: "/python-3.10-3.14-deep-dive",
          },
        ],
      },
      {
        text: "Pythonic",
        items: [
          { text: "Overview", link: "/pythonic/" },
          { text: "Data Model", link: "/pythonic/data-model" },
          {
            text: "Descriptors and Properties",
            link: "/pythonic/descriptors-and-properties",
          },
          { text: "Decorators", link: "/pythonic/decorators" },
          {
            text: "Context Managers",
            link: "/pythonic/context-managers",
          },
          { text: "Metaclasses", link: "/pythonic/metaclasses" },
        ],
      },
      {
        text: "Typing",
        items: [
          { text: "Overview", link: "/typing/" },
          { text: "Modern Typing", link: "/typing/modern-typing" },
          { text: "Generics", link: "/typing/generics" },
          { text: "Protocols", link: "/typing/protocols" },
          { text: "Type Narrowing", link: "/typing/type-narrowing" },
          {
            text: "Runtime vs Static",
            link: "/typing/runtime-vs-static",
          },
        ],
      },
      {
        text: "Runtime",
        items: [
          { text: "Overview", link: "/runtime/" },
          { text: "Execution Model", link: "/runtime/execution-model" },
          { text: "Object Model", link: "/runtime/object-model" },
          { text: "Memory and GC", link: "/runtime/memory-and-gc" },
          {
            text: "GIL and Subinterpreters",
            link: "/runtime/gil-and-subinterpreters",
          },
          {
            text: "Bytecode and Specialization",
            link: "/runtime/bytecode-and-specialization",
          },
          {
            text: "CPython vs Go Runtime",
            link: "/cpython-vs-go-runtime",
          },
        ],
      },
      {
        text: "Asyncio",
        items: [
          { text: "Overview", link: "/asyncio/" },
          { text: "Event Loop and Tasks", link: "/asyncio/event-loop-and-tasks" },
          {
            text: "Cancellation and TaskGroup",
            link: "/asyncio/cancellation-and-taskgroup",
          },
          {
            text: "Queues and Backpressure",
            link: "/asyncio/queues-and-backpressure",
          },
          {
            text: "Testing and Debugging",
            link: "/asyncio/testing-and-debugging",
          },
        ],
      },
      {
        text: "FastAPI",
        items: [
          { text: "Overview", link: "/fastapi/" },
          {
            text: "Project Structure",
            link: "/fastapi/project-structure",
          },
          {
            text: "Dependency Injection",
            link: "/fastapi/dependency-injection",
          },
          {
            text: "Request/Response Modeling",
            link: "/fastapi/request-response-modeling",
          },
          { text: "Lifespan and Testing", link: "/fastapi/lifespan-and-testing" },
          { text: "Performance and Ops", link: "/fastapi/performance-and-ops" },
        ],
      },
      {
        text: "Pydantic",
        items: [
          { text: "Overview", link: "/pydantic/" },
          { text: "Core Schema", link: "/pydantic/core-schema" },
          {
            text: "Validation Pipeline",
            link: "/pydantic/validation-pipeline",
          },
          {
            text: "BaseModel vs TypeAdapter",
            link: "/pydantic/basemodel-vs-typeadapter",
          },
          { text: "Internals", link: "/pydantic/internals" },
        ],
      },
      {
        text: "SQLAlchemy 2.0",
        items: [
          { text: "Overview", link: "/sqlalchemy/" },
          { text: "Core vs ORM", link: "/sqlalchemy/core-vs-orm" },
          {
            text: "Session and Unit of Work",
            link: "/sqlalchemy/session-and-unit-of-work",
          },
          {
            text: "Relationships and Loading",
            link: "/sqlalchemy/relationships-and-loading",
          },
          { text: "Async SQLAlchemy", link: "/sqlalchemy/async-sqlalchemy" },
          {
            text: "Migrations and Patterns",
            link: "/sqlalchemy/migrations-and-patterns",
          },
        ],
      },
      {
        text: "Playbooks",
        items: [
          { text: "Overview", link: "/playbooks/" },
          {
            text: "API Service Template",
            link: "/playbooks/api-service-template",
          },
          {
            text: "FastAPI + Pydantic + SQLAlchemy",
            link: "/playbooks/fastapi-pydantic-sqlalchemy",
          },
          {
            text: "Typing Review Checklist",
            link: "/playbooks/typing-review-checklist",
          },
        ],
      },
    ],
    search: {
      provider: "local",
    },
    socialLinks: [
      { icon: "github", link: "https://github.com/jaeyoung0509/python-handbook" },
    ],
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
    docFooter: {
      prev: "Previous page",
      next: "Next page",
    },
    footer: {
      message: "Built with VitePress. Written for Python 3.14.",
      copyright: "Copyright © 2026 jaeyoung0509",
    },
  },
});
