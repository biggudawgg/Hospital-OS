// Vite = the dev server + build tool for our React app.
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: { port: 5173 },
  // Put the big chart library in its own file so the main bundle loads faster
  build: { rollupOptions: { output: { manualChunks: { charts: ["recharts"] } } } },
});
