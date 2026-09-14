import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev proxy: requests to /api go to the FastAPI server (no CORS needed).
// Override the target with ADMIN_API_PROXY when the API runs elsewhere.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": {
        target: process.env.ADMIN_API_PROXY || "http://localhost:8000",
        changeOrigin: true,
        ws: true,
      },
    },
  },
});
