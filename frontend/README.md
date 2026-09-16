# Frontend — Retail Return Intelligence Dashboard

**Owner:** ______________________ (fill in your name, or split across the team)

## Your job in one sentence
A simple web page where a user types in a customer return description
and sees Agent 4's final recommendation.

## Where you fit in
```
User types return text → [YOU: Frontend] → Agent 4 → Recommendation → [YOU: display it]
```

**Important:** browsers cannot call MCP tools directly. Agent 4 needs to
expose a normal HTTP route for you to call (coordinate with whoever is
building Agent 4 — see their README's note on this). Don't build this
in isolation; agree on the exact request/response shape together first.

## What you need to build

1. **`src/main.jsx`** — standard React entry point, mounts `<App />`
2. **`src/App.jsx`** — a page with:
   - A textarea for the customer's return text
   - A submit button
   - A result section showing: root cause, confidence, evidence summary,
     recommendation, and a visible warning if `requires_human_review` is true
3. **`src/api/agent4.js`** — a `fetch()` call to whatever endpoint Agent 4
   exposes (get the exact URL/path from Agent 4's owner)
4. *(Optional, if time allows)* an analytics view — e.g. a chart of
   common root causes over multiple submitted returns

## What's already set up for you
- `package.json` — React, Vite, Recharts (for charts) already listed
- `vite.config.js` — dev server on port 5173
- `Dockerfile` — ready to build/run
- `index.html` — entry HTML file

## Folders you work in
```
frontend/
├── src/
│   ├── main.jsx        <-- create this
│   ├── App.jsx           <-- create this
│   ├── api/
│   │   └── agent4.js       <-- create this
│   ├── components/          <-- optional, split App.jsx into pieces
│   └── pages/                <-- optional, if you add more than one page
```

## Testing your work
```bash
cd frontend
npm install
npm run dev
```
Opens on `http://localhost:5173`. You can build/test your UI with mock
data before Agent 4's endpoint is ready — just hardcode a sample
response shape temporarily and swap in the real fetch call once
Agent 4's HTTP route exists.

## Checklist
- [ ] Basic form (textarea + submit) working
- [ ] Confirmed the exact endpoint/URL Agent 4 exposes for the frontend
- [ ] `src/api/agent4.js` correctly calls that endpoint
- [ ] Result section displays root cause, confidence, evidence, recommendation
- [ ] Human-review flag is visibly shown when true
- [ ] Runs standalone on port 5173 without errors
