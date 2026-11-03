import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/chat': 'http://127.0.0.1:8000',
      '/upload': 'http://127.0.0.1:8000',
      '/history': 'http://127.0.0.1:8000',
      '/new-chat': 'http://127.0.0.1:8000',
      '/clear-history': 'http://127.0.0.1:8000',
      '/conversations': 'http://127.0.0.1:8000',
      '/documents': 'http://127.0.0.1:8000',
      '/tasks': 'http://127.0.0.1:8000',
      '/todos': 'http://127.0.0.1:8000',
      '/settings': 'http://127.0.0.1:8000',
      '/health': 'http://127.0.0.1:8000',
    }
  }
})
