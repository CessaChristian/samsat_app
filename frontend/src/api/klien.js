// Klien HTTP untuk backend Flask.
// Semua permintaan menyertakan cookie sesi; Vite mem-proxy /api ke Flask

/** Dilempar bila backend membalas kode kesalahan. */
export class GagalApi extends Error {
  constructor(status, muatan) {
    super(muatan?.pesan || muatan?.judul || `Permintaan gagal (${status})`)
    this.name = 'GagalApi'
    this.status = status
    this.muatan = muatan || {}
  }
}

async function baca(balasan) {
  const tipe = balasan.headers.get('content-type') || ''
  if (!tipe.includes('application/json')) return null
  try {
    return await balasan.json()
  } catch {
    return null
  }
}

async function minta(jalur, opsi = {}) {
  const balasan = await fetch(jalur, { credentials: 'include', ...opsi })
  const muatan = await baca(balasan)
  if (!balasan.ok) throw new GagalApi(balasan.status, muatan)
  return muatan
}

function kirimJson(jalur, isi) {
  return minta(jalur, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(isi),
  })
}

export const api = {
  masuk: (username, password) =>
    kirimJson('/api/auth/login', { username, password }),

  keluar: () => minta('/api/auth/logout', { method: 'POST' }),

  siapa: () => minta('/api/auth/me'),

  meta: () => minta('/api/meta'),

  rekap: (filter = {}) => {
    const kueri = new URLSearchParams()
    for (const [kunci, nilai] of Object.entries(filter)) {
      if (nilai !== null && nilai !== undefined && nilai !== '') {
        kueri.set(kunci, nilai)
      }
    }
    const teks = kueri.toString()
    return minta(`/api/rekap${teks ? `?${teks}` : ''}`)
  },

  /**
   * Cek File: berkas diperiksa tanpa ditulis ke database.
   * Balasan bisa berstatus 200 dengan `lolos: false` — itu bukan error HTTP,
   * melainkan hasil pemeriksaan yang harus ditampilkan di panel merah.
   */
  cekBerkas: async (berkas) => {
    const muatan = new FormData()
    muatan.append('file', berkas)
    return minta('/api/upload/check', { method: 'POST', body: muatan })
  },

  simpanBerkas: (token) => kirimJson('/api/upload/commit', { token }),

  urlExport: (format, filter = {}) => {
    const kueri = new URLSearchParams()
    for (const [kunci, nilai] of Object.entries(filter)) {
      if (nilai !== null && nilai !== undefined && nilai !== '') {
        kueri.set(kunci, nilai)
      }
    }
    const teks = kueri.toString()
    return `/api/export.${format}${teks ? `?${teks}` : ''}`
  },
}
