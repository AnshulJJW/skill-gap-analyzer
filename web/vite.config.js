import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The API base URL is read from VITE_API_URL at build time so Stage 7 can
// point the deployed page at the deployed API without a code change.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // Dev-only: proxy /api to the local FastAPI server so the browser sees
    // one origin and CORS never enters the picture while developing.
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/api/, ""),
      },
    },
  },
});
