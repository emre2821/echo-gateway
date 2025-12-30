# `app/` directory

This folder contains the Next.js App Router entrypoint and all application-facing pages for the ChatGPT Apps SDK demo.

## Contents
- `layout.tsx`: Root layout that injects the `NextChatSDKBootstrap` to patch history, fetch, and HTML attributes for iframe-safe rendering. It wires in the global fonts and uses `baseURL` to set `<base>` correctly.
- `page.tsx`: Homepage client component that reads tool output via custom hooks, allows toggling fullscreen display mode, and links to the secondary page.
- `custom-page/`: Additional client page used to demonstrate in-app navigation from widgets.
- `mcp/`: API route that exposes the MCP server for ChatGPT.
- `hooks/`: Shared hooks that wrap the `window.openai` APIs and subscribe to MCP/Apps SDK globals.
- `globals.css`: Global Tailwind styles for the app shell.

## Behavior overview
- All pages are designed for iframe embedding inside ChatGPT, with display mode and max height driven by `window.openai`.
- The MCP server fetches the rendered homepage HTML and exposes it as a widget resource so tool responses can render the UI inside ChatGPT.
- Navigation uses standard Next.js routing; external links are intercepted to call `window.openai.openExternal` when available.
