import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true,
    proxy: { "/api": "http://127.0.0.1:8000" },
    hmr: { overlay: false },
  },
  resolve: {
    alias: { "buffer/": "buffer/" },
  },
  optimizeDeps: {
    include: [
      "react-plotly.js", "plotly.js", "buffer",
      "react", "react-dom", "react-router-dom", "axios",
      "framer-motion", "lucide-react",
    ],
    esbuildOptions: {
      define: { global: "globalThis" },
    },
  },
  define: {
    global: "globalThis",
    "process.env": {},
  },
  build: {
    // Split vendor chunks for better caching
    rollupOptions: {
      output: {
        manualChunks: {
          "vendor-react":  ["react", "react-dom", "react-router-dom"],
          "vendor-plotly": ["plotly.js", "react-plotly.js"],
          "vendor-leaflet":["leaflet", "react-leaflet"],
          "vendor-axios":  ["axios"],
        },
      },
    },
    // Faster builds
    target: "esnext",
    minify: "esbuild",
    chunkSizeWarningLimit: 2000,
  },
});
