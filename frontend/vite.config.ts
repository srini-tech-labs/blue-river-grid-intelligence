/// <reference types="vitest/config" />
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react()],
  build: {
    // FastAPI serves this directory; it is never committed.
    outDir: '../backend/static',
    emptyOutDir: true,
    // Not '/assets': that path belongs to the Asset 360 client route.
    assetsDir: '_app',
  },
  server: {
    proxy: { '/api': 'http://127.0.0.1:8000' },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
  },
})
