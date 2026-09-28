import { useState } from 'react'

import { api } from '../api/klien.js'
import logoJasaraharja from '../assets/logo-jasaraharja.png'
import logoJateng from '../assets/logo-jateng.png'
import logoPolda from '../assets/logo-polda.png'

/**
 * Layar masuk. Prototipe desain tidak menyediakan layar ini, jadi
 * tampilannya disusun dari token desain yang sama: Plus Jakarta Sans, kartu
 * bergaris tipis, aksen biru, sudut 14px.
 *
 */
export default function Login({ onMasuk }) {
  const [username, setUsername] = useState('')
  const [sandi, setSandi] = useState('')
  const [kesalahan, setKesalahan] = useState('')
  const [mengirim, setMengirim] = useState(false)

  async function kirim(peristiwa) {
    peristiwa.preventDefault()
    setKesalahan('')
    setMengirim(true)
    try {
      const hasil = await api.masuk(username.trim(), sandi)
      onMasuk(hasil)
    } catch (galat) {
      setKesalahan(galat.message || 'Tidak dapat masuk. Coba lagi.')
      setMengirim(false)
    }
  }

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'grid',
        placeItems: 'center',
        padding: 24,
        background: 'oklch(0.985 0.004 254)',
      }}
    >
      <main style={{ width: 'min(400px, 100%)' }}>
        <div
          style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            gap: 12,
            marginBottom: 22,
          }}
        >
          <img src={logoJateng} alt="Lambang Provinsi Jawa Tengah" width={40} height={44} style={{ height: 44 }} />
          <img src={logoPolda} alt="Lambang Polda Jawa Tengah" width={33} height={44} style={{ height: 44 }} />
          <img src={logoJasaraharja} alt="Logo Jasa Raharja" width={38} height={38} style={{ height: 38 }} />
        </div>

        <div
          className="kartu-besar"
          style={{ padding: '28px 30px 30px', display: 'flex', flexDirection: 'column', gap: 22 }}
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6, textAlign: 'center' }}>
            <h1 style={{ margin: 0, fontSize: 19, fontWeight: 600, letterSpacing: '-0.02em' }}>
              Samsat Kota Salatiga
            </h1>
            <p style={{ margin: 0, fontSize: 13, color: 'var(--teks-samar-2)' }}>
              Monitoring Penerimaan PKB
            </p>
          </div>

          <form onSubmit={kirim} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <label className="label-isian">
              Username
              <input
                className="isian"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="username"
                autoFocus
                required
              />
            </label>

            <label className="label-isian">
              Kata sandi
              <input
                className="isian"
                type="password"
                value={sandi}
                onChange={(e) => setSandi(e.target.value)}
                autoComplete="current-password"
                required
              />
            </label>

            {kesalahan && (
              <div className="panel-info panel-merah" role="alert" style={{ padding: '11px 13px' }}>
                {kesalahan}
              </div>
            )}

            <button
              type="submit"
              className="tombol-utama"
              disabled={mengirim || !username.trim() || !sandi}
              style={{ justifyContent: 'center', padding: '11px 18px', fontSize: 13.5 }}
            >
              {mengirim ? 'Memeriksa…' : 'Masuk'}
            </button>
          </form>
        </div>

        <p
          style={{
            margin: '18px 0 0',
            fontSize: 12,
            lineHeight: 1.6,
            textAlign: 'center',
            color: 'var(--teks-samar-3)',
          }}
        >
          Aplikasi internal. Berisi data identitas pemilik kendaraan —
          jangan dibagikan ke luar instansi.
        </p>
      </main>
    </div>
  )
}
