import { useCallback, useEffect, useState } from 'react'

import { api } from './api/klien.js'
import Dashboard from './pages/Dashboard.jsx'
import Login from './pages/Login.jsx'

/**
 * Menentukan layar mana yang tampil berdasarkan ada tidaknya sesi.
 * Seluruh halaman dan endpoint selain login mewajibkan sesi (bagian 14).
 */
export default function App() {
  const [pengguna, setPengguna] = useState(null)
  const [memeriksaSesi, setMemeriksaSesi] = useState(true)

  useEffect(() => {
    let batal = false
    api
      .siapa()
      .then((hasil) => {
        if (!batal) setPengguna(hasil)
      })
      .catch(() => {
        if (!batal) setPengguna(null)
      })
      .finally(() => {
        if (!batal) setMemeriksaSesi(false)
      })
    return () => {
      batal = true
    }
  }, [])

  const keluar = useCallback(async () => {
    try {
      await api.keluar()
    } finally {
      setPengguna(null)
    }
  }, [])

  if (memeriksaSesi) {
    return (
      <div
        style={{
          minHeight: '100vh',
          display: 'grid',
          placeItems: 'center',
          color: 'var(--teks-samar)',
          fontSize: 13,
        }}
      >
        Memuat…
      </div>
    )
  }

  if (!pengguna) return <Login onMasuk={setPengguna} />

  return <Dashboard pengguna={pengguna} onKeluar={keluar} />
}
