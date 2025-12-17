import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
// SECURITY FIX: Disable source maps in production (LOW-002)
export default defineConfig({
  plugins: [react()],
  build: {
    sourcemap: false,
  },
})
