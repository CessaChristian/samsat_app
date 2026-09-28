// Pemformatan angka dan tanggal untuk tampilan.
// Uang dikirim backend sebagai angka bulat rupiah; seluruh pemformatan

const angkaId = new Intl.NumberFormat('id-ID')
const satuDesimal = new Intl.NumberFormat('id-ID', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
})

const BULAN = [
  'Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun',
  'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des',
]

/** 8859350800 -> "8.859.350.800" */
export function angka(nilai) {
  return angkaId.format(Number(nilai) || 0)
}

/** 8859350800 -> "Rp 8.859.350.800" */
export function rupiah(nilai) {
  return `Rp ${angka(nilai)}`
}

/** 8859350800 -> "Rp 8,86 M" — dipakai pada angka besar di kartu. */
export function rupiahRingkas(nilai) {
  const n = Number(nilai) || 0
  const tanda = n < 0 ? '-' : ''
  const abs = Math.abs(n)

  if (abs >= 1e12) return `${tanda}Rp ${satuDesimal.format(abs / 1e12)} T`
  if (abs >= 1e9) return `${tanda}Rp ${satuDesimal.format(abs / 1e9)} M`
  if (abs >= 1e6) return `${tanda}Rp ${satuDesimal.format(abs / 1e6)} jt`
  return `${tanda}Rp ${angkaId.format(abs)}`
}

/** "2026-09-19" -> "19/09/2026" */
export function tanggal(iso) {
  if (!iso) return '—'
  const [y, m, d] = String(iso).slice(0, 10).split('-')
  return `${d}/${m}/${y}`
}

/** "2026-09-19" -> "19 Sep 2026" */
export function tanggalPendek(iso) {
  if (!iso) return '—'
  const [y, m, d] = String(iso).slice(0, 10).split('-')
  return `${Number(d)} ${BULAN[Number(m) - 1]} ${y}`
}

/**
 * Label periode selalu menyebut tanggal, bukan nama bulan saja, supaya
 * bulan berjalan tidak disalahpahami sebagai bulan penuh.
 */
export function labelPeriode(dari, sampai) {
  if (!dari || !sampai) return '—'
  return `${tanggalPendek(dari)} – ${tanggalPendek(sampai)}`
}

/** "2026-09-18T16:12:00+07:00" -> "18/09/2026 16:12" */
export function waktu(iso) {
  if (!iso) return '—'
  const t = new Date(iso)
  if (Number.isNaN(t.getTime())) return '—'
  const dua = (n) => String(n).padStart(2, '0')
  return `${dua(t.getDate())}/${dua(t.getMonth() + 1)}/${t.getFullYear()} ${dua(
    t.getHours(),
  )}:${dua(t.getMinutes())}`
}

/** 2400000 -> "2,4 MB" */
export function ukuranBerkas(byte) {
  const n = Number(byte) || 0
  if (n >= 1024 * 1024) return `${(n / (1024 * 1024)).toFixed(1).replace('.', ',')} MB`
  if (n >= 1024) return `${Math.round(n / 1024)} KB`
  return `${n} B`
}

/** 100 -> "100%", 25.5 -> "25,5%" */
export function persen(nilai) {
  const n = Number(nilai) || 0
  const teks = Number.isInteger(n) ? String(n) : n.toFixed(1)
  return `${teks.replace('.', ',')}%`
}

const BULAN_PANJANG = [
  'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
  'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember',
]

/**
 * Label periode dalam nama bulan, dipakai saat mode Bulan.
 *   "2026-01-01","2026-08-31" -> "Januari – Agustus 2026"
 *   "2026-08-01","2026-08-31" -> "Agustus 2026"
 *   "2025-11-01","2026-08-31" -> "November 2025 – Agustus 2026"
 *
 * Nama bulan saja bisa disalahpahami sebagai bulan penuh, jadi tanggal
 * persisnya tetap ditampilkan pada baris keterangan di bawah bilah filter
 *.
 */
export function labelPeriodeBulan(dari, sampai) {
  if (!dari || !sampai) return '—'
  const [thnAwal, blnAwal] = String(dari).slice(0, 10).split('-').map(Number)
  const [thnAkhir, blnAkhir] = String(sampai).slice(0, 10).split('-').map(Number)
  const namaAwal = BULAN_PANJANG[blnAwal - 1]
  const namaAkhir = BULAN_PANJANG[blnAkhir - 1]
  if (thnAwal === thnAkhir && blnAwal === blnAkhir) return `${namaAwal} ${thnAwal}`
  if (thnAwal === thnAkhir) return `${namaAwal} – ${namaAkhir} ${thnAwal}`
  return `${namaAwal} ${thnAwal} – ${namaAkhir} ${thnAkhir}`
}
