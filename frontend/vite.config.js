import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const backendHost = process.env.CDSW_READONLY_HOST || "127.0.0.1";
const backendPort = process.env.CDSW_READONLY_PORT || "8000";
const frontendPort = parseInt(process.env.CDSW_APP_PORT || "5173", 10);

export default defineConfig({
  plugins: [react()],
  server: {
    host: process.env.CDSW_APP_HOST || "127.0.0.1",
    port: frontendPort,
    proxy: {
      "/api": {
        target: `http://${backendHost}:${backendPort}`,
        changeOrigin: true,
      },
    },
  },
});
