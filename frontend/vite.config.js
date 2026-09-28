import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// Porta dan alamat backend dibaca dari frontend/.env supaya tidak perlu
// menyunting berkas konfigurasi saat pindah lingkungan.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')

  return {
    plugins: [react()],
    server: {
      port: Number(env.VITE_PORT) || 5173,
      proxy: {
        // Dev server meneruskan /api ke Flask supaya cookie sesi berjalan
        // satu origin, tanpa perlu CORS.
        '/api': {
          target: env.VITE_API_TARGET || 'http://127.0.0.1:5000',
          changeOrigin: false,
        },
      },
    },
  }
})
