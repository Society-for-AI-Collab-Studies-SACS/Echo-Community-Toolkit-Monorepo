# Λ — Tiny Vite + React + TypeScript Scaffold (with Vitest)

This is a minimal scaffold to run the **LambdaStateViewer** and test the **operator suite** (𝒢, ℬ, 𝓜, 𝓢, 𝓒).

## Quickstart

```bash
npm install
npm run dev
```

Open http://localhost:5173 in your browser.

## Tests

```bash
npm run test
npm run test:watch
```

## Structure

```
lambda-vite/
  ├─ index.html
  ├─ package.json
  ├─ tsconfig.json
  ├─ vite.config.ts
  └─ src/
     ├─ main.tsx
     ├─ App.tsx
     ├─ LambdaStateViewer.tsx
     └─ ops/
        ├─ ops.ts
        └─ ops.test.ts
```

- `LambdaStateViewer.tsx`: live Hilbert visualizer for |Λ⟩
- `ops/ops.ts`: pure operator helpers for unit tests
- `ops/ops.test.ts`: Vitest suite covering 𝒢, ℬ, 𝓜, 𝓢, 𝓒
