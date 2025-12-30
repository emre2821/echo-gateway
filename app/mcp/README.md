# `app/mcp/`

This folder hosts the MCP server route that powers the ChatGPT widget experience.

## Route summary
- `route.ts` uses `createMcpHandler` to expose the server over both GET and POST.
- The handler fetches the rendered homepage HTML (`/`) using `baseURL`, wraps it as a resource (`ui://widget/content-template.html`), and sets OpenAI metadata so ChatGPT can render it as a widget.
- A `show_content` tool is registered with Zod validation for a `name` argument. Tool responses include `structuredContent` and mirror the widget metadata so ChatGPT can hydrate the returned template.

## Runtime expectations
- The server needs the same `assetPrefix`/`baseURL` configuration as the UI so that embedded HTML can load static assets when rendered inside an iframe.
- CORS and iframe safety are handled at the app level (`middleware.ts` and `layout.tsx`); the route assumes those headers are already present on fetches initiated by ChatGPT.
