import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Dev server mem-proxy /api ke Flask supaya cookie sesi berjalan satu origin,
// tanpa perlu CORS. Acuan: SPESIFIKASI_DASHBOARD_PKB.md bagian 15.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        // Sengaja 127.0.0.1, bukan "localhost": di macOS "localhost" lebih
        // dulu diarahkan ke ::1, dan di sana yang menjawab port 5000 adalah
        // AirPlay Receiver bawaan sistem, sehingga proxy membalas 403.
        target: 'http://127.0.0.1:5000',
        changeOrigin: false,
      },
    },
  },
})
