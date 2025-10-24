# @AceTheDactyl/rhz-stylus-arch

CLI + API for the RHZ Stylus ASCII architecture diagram and LLM usage guide.

## Install

Using GitHub Packages (scoped):

```
npm config set @AceTheDactyl:registry https://npm.pkg.github.com
npm install @AceTheDactyl/rhz-stylus-arch
```

## Usage

- CLI (prints architecture + LLM guide):
  - `npx @AceTheDactyl/rhz-stylus-arch`
- CLI (architecture only):
  - `npx @AceTheDactyl/rhz-stylus-arch arch`
- CLI (LLM guide only):
  - `npx @AceTheDactyl/rhz-stylus-arch llm`

- API:
```js
import { getArchitecture, getLlmGuide } from '@AceTheDactyl/rhz-stylus-arch';
console.log(getArchitecture());
console.log(getLlmGuide());
```

## Publish (GitHub Actions)
- On release tags (v*), CI publishes to GitHub Packages.
- See `.github/workflows/npm-publish.yml` in the repo root.

