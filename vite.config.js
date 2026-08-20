import path from "node:path";

import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";

const root = import.meta.dirname;

export default defineConfig({
  plugins: [tailwindcss()],
  base: "/static/dist/",
  build: {
    outDir: path.resolve(root, "static/dist"),
    emptyOutDir: true,
    manifest: "manifest.json",
    rollupOptions: {
      input: {
        main: path.resolve(root, "assets/js/main.js"),
      },
    },
  },
  server: {
    host: "0.0.0.0",
    port: 5173,
  },
});
