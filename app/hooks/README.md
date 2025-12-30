# `app/hooks/`

Custom React hooks that wrap `window.openai` APIs and expose ChatGPT Apps SDK globals in a React-friendly way.

## Key hooks
- `useCallTool` / `useSendMessage`: Invoke MCP tools and send follow-up messages directly from the widget.
- `useOpenExternal` / `useRequestDisplayMode`: Bridge external navigation and display mode requests to the ChatGPT host.
- `useDisplayMode`, `useMaxHeight`, `useWidgetProps`, `useWidgetState`, `useOpenAIGlobal`: Subscribe to and synchronize state provided by ChatGPT (theme, layout constraints, tool outputs, and persistent widget state).
- `useIsChatGptApp`: Lightweight check that flags whether the app is running inside ChatGPT, backed by the bootstrap script in `app/layout.tsx`.

## Usage patterns
- All hooks guard against `window` being unavailable during SSR; ensure components importing them are client components.
- The hooks rely on the event contract defined in `types.ts` (`SET_GLOBALS_EVENT_TYPE`) to stay synced with the host environment.
