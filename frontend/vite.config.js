import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Vite dev server runs on port 5173 by default - this must match
// the FRONTEND_ORIGINS allowlist in app/main.py's CORS config.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173
  }
})
