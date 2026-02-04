# `app/custom-page/`

Client-side page that demonstrates navigation within the ChatGPT-hosted widget.

## Behavior
- `page.tsx` renders a simple welcome view with Tailwind styling and a link back to the homepage (`/`).
- The component is marked with `"use client"` so it can share the same client-only environment assumptions as the main page.
- This page provides a minimal example of adding additional routes that remain iframe-safe when embedded in ChatGPT.
