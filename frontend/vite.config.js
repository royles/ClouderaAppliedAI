import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const backendHost = process.env.CDSW_READONLY_HOST || "127.0.0.1";
const backendPort = process.env.CDSW_READONLY_PORT || "8000";
const frontendPort = parseInt(process.env.CDSW_APP_PORT || "5173", 10);

// CML/CDSW exposes the app on a public *.cloudera.site hostname; Vite blocks
// unknown Host headers unless they are listed here.
const allowedHosts = [".cloudera.site", ".cloudera.com", "localhost", "127.0.0.1"];
if (process.env.CDSW_DOMAIN) {
  allowedHosts.push(process.env.CDSW_DOMAIN);
}

export default defineConfig({
  plugins: [react()],
  server: {
    host: process.env.CDSW_APP_HOST || "127.0.0.1",
    port: frontendPort,
    allowedHosts,
    proxy: {
      "/api": {
        target: `http://${backendHost}:${backendPort}`,
        changeOrigin: true,
      },
    },
  },
});
