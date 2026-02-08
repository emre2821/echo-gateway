# `public/`

Static assets served directly by Next.js. These files are requested via `/_next/static` when rendered in ChatGPT or in the browser.

## Assets
- `next.svg`: Framework logo used by the starter UI.
- `globe.svg`, `file.svg`, `window.svg`: Generic icons available for future UI work.

Assets in this folder are fetched relative to the base URL set in `baseUrl.ts` so they load correctly when the app is embedded in an iframe.
