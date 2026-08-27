# web/ — Stage 6

Empty until Stage 6. Do not start it early; the frontend is packaging, and
building it before Stage 4 means building a UI around logic that may still
change shape.

    npm create vite@latest . -- --template react
    npm install
    npm run dev

One page. A textarea, a role dropdown, an Analyze button, a results view.
No router, no state library.

Three things the results view must do:
- show the coverage number first, then the ranked gaps as cards
- show a real loading state — the first request hits a cold backend and takes
  several seconds; a frozen button reads as broken
- show the skills that WERE found in the resume, not just the missing ones —
  it builds trust and makes extraction errors visible instead of hidden
