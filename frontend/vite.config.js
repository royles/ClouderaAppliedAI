import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// BACKEND_PROXY_TARGET is set by start.py. On CML, use internal port 8000 —
// CDSW_READONLY_PORT is not reliable for loopback proxy connections.
const backendTarget =
  process.env.BACKEND_PROXY_TARGET ||
  `http://127.0.0.1:${process.env.BACKEND_PROXY_PORT || process.env.CDSW_READONLY_PORT || "8000"}`;
const frontendPort = parseInt(process.env.CDSW_APP_PORT || "5173", 10);

// CML/CDSW exposes the app on a public *.cloudera.site hostname; Vite blocks
// unknown Host headers unless they are listed here.
const allowedHosts = [".cloudera.site", ".cloudera.com", "localhost", "127.0.0.1"];
if (process.env.CDSW_DOMAIN) {
  allowedHosts.push(process.env.CDSW_DOMAIN);
}

const proxyOptions = {
  target: backendTarget,
  changeOrigin: true,
};

export default defineConfig({
  plugins: [react()],
  server: {
    host: process.env.CDSW_APP_HOST || "127.0.0.1",
    port: frontendPort,
    allowedHosts,
    proxy: {
      "/api": proxyOptions,
      "/docs": proxyOptions,
      "/openapi.json": proxyOptions,
      "/redoc": proxyOptions,
    },
  },
});
