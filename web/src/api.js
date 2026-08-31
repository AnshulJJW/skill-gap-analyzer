/**
 * The only place that knows how to reach the backend.
 *
 * In development VITE_API_URL is unset and requests go to /api, which the
 * Vite dev server proxies to http://127.0.0.1:8000 — so the browser sees a
 * single origin and CORS never comes up. In production Stage 7 sets
 * VITE_API_URL at build time to the deployed API.
 */

const BASE = import.meta.env.VITE_API_URL ?? "/api";

async function request(path, options) {
  let res;
  try {
    res = await fetch(`${BASE}${path}`, options);
  } catch {
    // fetch only rejects when the request never reached a server
    throw new Error(
      "Could not reach the analyzer. If you are running this locally, " +
        "start the API with: uvicorn api.main:app --reload"
    );
  }

  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") detail = body.detail;
      // FastAPI validation errors arrive as a list of field problems
      else if (Array.isArray(body.detail)) detail = body.detail[0]?.msg ?? detail;
    } catch {
      /* response had no JSON body; keep the status message */
    }
    throw new Error(detail);
  }
  return res.json();
}

export const getRoles = () => request("/roles");

export const analyze = (resumeText, roleId) =>
  request("/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      resume_text: resumeText,
      role_id: roleId,
      top_n: 8,
    }),
  });
