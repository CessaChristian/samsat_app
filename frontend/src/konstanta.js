// Ke-21 nama kolom yang harus ada di berkas dari pusat.
// Daftar ini menggantikan teks kolom wajib di prototipe, yang menyebut kolom
// lama seperti "Objek" dan "Lokasi Proses" (bagian 3 dan 4).
//
// Backend memakai daftar yang sama di app/konstanta.py — bila format berkas
// pusat berubah, keduanya harus disunting bersamaan.
export const HEADER_WAJIB = [
  'no_polisi',
  'nama',
  'alamat',
  'nm_kecamatan',
  'nm_kelurahan',
  'nm_jenis_kend',
  'nm_merk_kend',
  'th_buat',
  'warna_kend',
  'warna_tnkb_kend',
  'jml_roda',
  'tgl_jatuh_tempo_pkb',
  'tgl_jatuh_tempo_stnk',
  'PKB Pokok',
  'PKB Denda',
  'PKB Opsen',
  'PKB Denda Opsen',
  'SWDKLLJ',
  'Denda SWDKLLJ',
  'PNBP',
  'TOTAL',
]

/** Banyaknya kesalahan yang ditampilkan sebelum diringkas (bagian 9.A). */
export const KESALAHAN_DITAMPILKAN = 8

export const BATAS_BERKAS_MB = 10
