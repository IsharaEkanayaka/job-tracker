import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In development the UI runs on :5173 and forwards API calls to FastAPI on :8000.
const api = { target: "http://127.0.0.1:8000", changeOrigin: true };

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: { "/jobs": api, "/stats": api, "/collect": api },
  },
});
