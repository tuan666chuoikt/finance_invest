/// <reference types="vitest" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The API itself is mounted under /api (platform.md §1.1), so the proxy keeps the prefix.
export default defineConfig({
  plugins: [react()],
  server: { proxy: { "/api": "http://127.0.0.1:8001" } },
  test: { css: true, environment: "jsdom", globals: true, setupFiles: ["./src/test/setup.ts"] },
});
