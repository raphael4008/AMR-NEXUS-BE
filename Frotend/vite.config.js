import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  resolve: {
    dedupe: ['react', 'react-dom']   
  },
  server: {
    proxy: {
      '/analytics': 'http://localhost:8000',
      '/predict': 'http://localhost:8000',
      '/recommendations': 'http://localhost:8000',
      '/ews': 'http://localhost:8000',
      '/alerts': 'http://localhost:8000',
      '/search': 'http://localhost:8000',
      '/me': 'http://localhost:8000',
      '/export': 'http://localhost:8000',
      '/predictions': 'http://localhost:8000',
      '/reports': 'http://localhost:8000',
      '/pathogen-explorer': 'http://localhost:8000'   
    }
  }
})