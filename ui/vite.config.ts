import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/auth': 'http://localhost:8000',
      '/threads': 'http://localhost:8000',
      '/chat': 'http://localhost:8000',
      '/integrations': 'http://localhost:8000',
    },
  },
});
