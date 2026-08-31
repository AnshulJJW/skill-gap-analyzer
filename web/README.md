# web/ — Stage 6

One page. A textarea, a role dropdown, a button, and the results.
No router, no state library, no component framework — the page has about a
dozen elements, and a single CSS file is smaller and faster than pulling in
Tailwind for it.

## Running it

The API must be running first:

```bash
uvicorn api.main:app --reload      # from the project root
npm install && npm run dev         # from web/
```

Then http://localhost:5173

## How it reaches the API

In development the Vite dev server proxies `/api` to `http://127.0.0.1:8000`,
so the browser sees a single origin and CORS never arises. In production
`VITE_API_URL` is set at build time to the deployed API — see
`src/api.js`.

## Three decisions worth knowing

**It shows what was found, not only what is missing.** The skills the
extractor picked up are listed alongside the gaps. Hiding them would mean a
wrong extraction looks like a confident score; showing them lets the user
catch it.

**Every recommendation carries its evidence.** "appears in 42% of 4,837
postings" sits next to the number, because a percentage with no denominator
is just an assertion.

**There is a real loading state.** The first request after the API has been
idle pays a cold start, and a frozen button reads as broken.
