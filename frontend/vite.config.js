import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // In dev, the FastAPI backend runs separately on :8000 (uvicorn app.api:app --reload).
    // In production, FastAPI serves this app's build output directly, so no proxy is needed there.
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
  build: {
    outDir: 'dist',
  },
})
