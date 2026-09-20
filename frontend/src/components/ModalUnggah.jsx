import { useRef, useState } from 'react'

import { api } from '../api/klien.js'
import { angka, tanggal, ukuranBerkas } from '../format.js'
import { BATAS_BERKAS_MB, HEADER_WAJIB, KESALAHAN_DITAMPILKAN } from '../konstanta.js'
import { IkonUnggah } from './Ikon.jsx'

/**
 * Modal unggah dengan alur Cek File -> Simpan (bagian 8).
 *
 * Tahapan:
 *   kosong    pilih berkas
 *   dipilih   berkas siap, tombol "Cek File" aktif
 *   memeriksa permintaan ke /api/upload/check sedang berjalan
 *   lolos     ringkasan hijau (+ kotak kuning bila ada penyesuaian otomatis),
 *             tombol "Simpan ke database" aktif
 *   gagal     panel merah berisi daftar kesalahan, Simpan nonaktif
 *   menyimpan permintaan ke /api/upload/commit sedang berjalan
 *
 * Penyesuaian wajib terhadap prototipe (bagian 3):
 *   - daftar kolom wajib memakai ke-21 header yang sebenarnya
 *   - kotak kuning dipakai untuk penyesuaian otomatis, bukan "baris dilewati"
 *   - petunjuk tanggal memakai dd/mm/yyyy
 *   - penomoran daftar kesalahan dimulai dari 1
 *   - tombol peraga "Berhasil / Gagal / Kosongkan" dihapus
 */
export default function ModalUnggah({ onTutup, onTersimpan }) {
  const [berkas, setBerkas] = useState(null)
  const [tahap, setTahap] = useState('kosong')
  const [hasil, setHasil] = useState(null)
  const [galatBerkas, setGalatBerkas] = useState(null)
  const [seret, setSeret] = useState(false)
  const inputRef = useRef(null)

  const sibuk = tahap === 'memeriksa' || tahap === 'menyimpan'

  function pilihUlang(berkasBaru) {
    // "Ganti berkas" membuang token lama; Simpan kembali nonaktif sampai
    // Cek File dijalankan lagi (bagian 8 butir 4).
    setBerkas(berkasBaru)
    setHasil(null)
    setGalatBerkas(null)
    setTahap(berkasBaru ? 'dipilih' : 'kosong')
  }

  function terimaBerkas(daftar) {
    const satu = daftar?.[0]
    if (!satu) return
    const akhiran = satu.name.toLowerCase().slice(satu.name.lastIndexOf('.'))
    if (!['.xlsx', '.xls'].includes(akhiran)) {
      setBerkas(satu)
      setHasil(null)
      setTahap('gagal')
      setGalatBerkas({
        kode: 'FORMAT_TIDAK_DIDUKUNG',
        pesan: `Format "${akhiran || satu.name}" tidak didukung. Gunakan .xlsx atau .xls.`,
      })
      return
    }
    pilihUlang(satu)
  }

  async function cekBerkas() {
    setTahap('memeriksa')
    setGalatBerkas(null)
    try {
      const balasan = await api.cekBerkas(berkas)
      setHasil(balasan)
      setTahap(balasan.lolos ? 'lolos' : 'gagal')
    } catch (galat) {
      setGalatBerkas(galat.muatan?.kode ? galat.muatan : { kode: 'GAGAL', pesan: galat.message })
      setHasil(null)
      setTahap('gagal')
    }
  }

  async function simpan() {
    setTahap('menyimpan')
    try {
      const balasan = await api.simpanBerkas(hasil.token)
      onTersimpan(balasan)
    } catch (galat) {
      setGalatBerkas(galat.muatan?.kode ? galat.muatan : { kode: 'GAGAL', pesan: galat.message })
      setTahap('gagal')
    }
  }

  const kesalahan = hasil?.kesalahan ?? []
  const peringatan = hasil?.peringatan ?? []
  const ringkasan = hasil?.ringkasan

  return (
    <div
      data-no-print
      role="dialog"
      aria-modal="true"
      aria-label="Unggah data Excel"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget && !sibuk) onTutup()
      }}
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 50,
        background: 'var(--tirai)',
        display: 'grid',
        placeItems: 'center',
        padding: 24,
      }}
    >
      <div
        style={{
          width: 'min(580px, 100%)',
          maxHeight: '86vh',
          overflow: 'auto',
          background: '#fff',
          border: '1px solid var(--garis)',
          borderRadius: 'var(--radius-besar)',
          boxShadow: '0 18px 48px oklch(0.3 0.03 254 / 0.18)',
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 14,
            padding: '16px 20px',
            borderBottom: '1px solid var(--garis-halus-2)',
          }}
        >
          <span style={{ fontSize: 14.5, fontWeight: 600, letterSpacing: '-0.01em' }}>
            Unggah data Excel
          </span>
          <button
            type="button"
            onClick={onTutup}
            disabled={sibuk}
            title="Tutup"
            style={{
              width: 30,
              height: 30,
              border: '1px solid var(--garis-tombol)',
              borderRadius: 'var(--radius-kecil)',
              background: '#fff',
              fontSize: 15,
              lineHeight: 1,
              color: 'var(--teks-label)',
              cursor: sibuk ? 'not-allowed' : 'pointer',
            }}
          >
            ×
          </button>
        </div>

        <div style={{ padding: 20, display: 'flex', flexDirection: 'column', gap: 16 }}>
          <input
            ref={inputRef}
            type="file"
            accept=".xlsx,.xls"
            style={{ display: 'none' }}
            onChange={(e) => terimaBerkas(e.target.files)}
          />

          {!berkas ? (
            <>
              <div
                onClick={() => inputRef.current?.click()}
                onDragOver={(e) => {
                  e.preventDefault()
                  setSeret(true)
                }}
                onDragLeave={() => setSeret(false)}
                onDrop={(e) => {
                  e.preventDefault()
                  setSeret(false)
                  terimaBerkas(e.dataTransfer.files)
                }}
                style={{
                  border: `1.5px dashed ${seret ? 'var(--biru)' : 'oklch(0.83 0.035 254)'}`,
                  borderRadius: 'var(--radius)',
                  background: seret ? 'oklch(0.97 0.02 254)' : 'oklch(0.985 0.008 254)',
                  padding: '26px 20px',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: 12,
                  textAlign: 'center',
                  cursor: 'pointer',
                }}
              >
                <div
                  style={{
                    width: 38,
                    height: 38,
                    borderRadius: 10,
                    background: 'var(--biru-latar)',
                    display: 'grid',
                    placeItems: 'center',
                    color: 'var(--biru)',
                    pointerEvents: 'none',
                  }}
                >
                  <IkonUnggah ukuran={19} />
                </div>
                <div
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 5,
                    pointerEvents: 'none',
                  }}
                >
                  <div style={{ fontSize: 14, fontWeight: 600 }}>
                    Tarik file Excel ke sini atau klik untuk memilih
                  </div>
                  <div style={{ fontSize: 12.5, color: 'var(--teks-samar)' }}>
                    .xlsx atau .xls · maksimal {BATAS_BERKAS_MB} MB
                  </div>
                </div>
                <span className="tombol-utama" style={{ marginTop: 2, padding: '9px 18px' }}>
                  Pilih File
                </span>
              </div>

              <details>
                <summary
                  style={{
                    fontSize: 12.5,
                    fontWeight: 600,
                    color: 'var(--teks-label)',
                    cursor: 'pointer',
                  }}
                >
                  Kolom wajib ({HEADER_WAJIB.length} kolom)
                </summary>
                <div
                  style={{
                    marginTop: 10,
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fill, minmax(155px, 1fr))',
                    gap: '5px 12px',
                    fontSize: 12,
                    color: 'var(--teks-label)',
                  }}
                >
                  {HEADER_WAJIB.map((nama) => (
                    <code
                      key={nama}
                      style={{
                        fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace',
                        fontSize: 11.5,
                      }}
                    >
                      {nama}
                    </code>
                  ))}
                </div>
                <p
                  style={{
                    margin: '10px 0 0',
                    fontSize: 12.5,
                    lineHeight: 1.55,
                    color: 'var(--teks-label)',
                  }}
                >
                  Urutan kolom bebas, nama harus persis. Tanggal memakai format dd/mm/yyyy.
                  Satu berkas per pengiriman, diambil dari kantor pusat tanpa mengubah baris
                  header.
                </p>
              </details>
            </>
          ) : (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: 14,
                flexWrap: 'wrap',
                padding: '13px 15px',
                border: '1px solid var(--garis-input)',
                borderRadius: 10,
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, minWidth: 0 }}>
                <div
                  style={{
                    width: 34,
                    height: 40,
                    borderRadius: 7,
                    background: 'oklch(0.96 0.03 155)',
                    border: '1px solid oklch(0.9 0.05 155)',
                    display: 'grid',
                    placeItems: 'center',
                    fontSize: 10,
                    fontWeight: 700,
                    color: 'oklch(0.45 0.12 155)',
                  }}
                >
                  XLS
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 3, minWidth: 0 }}>
                  <div
                    style={{
                      fontSize: 13.5,
                      fontWeight: 600,
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                    }}
                    title={berkas.name}
                  >
                    {berkas.name}
                  </div>
                  <div style={{ fontSize: 12, color: 'var(--teks-samar)' }}>
                    {ukuranBerkas(berkas.size)}
                  </div>
                </div>
              </div>
              <button
                type="button"
                className="tombol-biasa"
                onClick={() => inputRef.current?.click()}
                disabled={sibuk}
              >
                Ganti berkas
              </button>
            </div>
          )}

          {tahap === 'memeriksa' && <Memuat teks="Memeriksa berkas…" />}
          {tahap === 'menyimpan' && <Memuat teks="Menyimpan ke database…" />}

          {galatBerkas && (
            <div className="panel-info panel-merah" role="alert">
              <strong style={{ display: 'block', marginBottom: 4 }}>Berkas ditolak</strong>
              {galatBerkas.pesan}
            </div>
          )}

          {tahap === 'lolos' && ringkasan && (
            <RingkasanLolos ringkasan={ringkasan} peringatan={peringatan} />
          )}

          {tahap === 'gagal' && kesalahan.length > 0 && <DaftarKesalahan kesalahan={kesalahan} />}
        </div>

        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'flex-end',
            gap: 10,
            flexWrap: 'wrap',
            padding: '14px 20px',
            borderTop: '1px solid var(--garis-halus-2)',
          }}
        >
          <button type="button" className="tombol-biasa" onClick={onTutup} disabled={sibuk}>
            Tutup
          </button>
          <button
            type="button"
            className="tombol-biasa"
            onClick={cekBerkas}
            disabled={!berkas || sibuk || tahap === 'lolos'}
          >
            Cek File
          </button>
          <button
            type="button"
            className="tombol-utama"
            onClick={simpan}
            disabled={tahap !== 'lolos' || !hasil?.token}
          >
            Simpan ke database
          </button>
        </div>
      </div>
    </div>
  )
}

function Memuat({ teks }) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        fontSize: 13,
        color: 'var(--teks-redup)',
      }}
    >
      <span
        style={{
          width: 15,
          height: 15,
          borderRadius: '50%',
          border: '2px solid var(--garis)',
          borderTopColor: 'var(--biru)',
          animation: 'putar 700ms linear infinite',
        }}
      />
      {teks}
    </div>
  )
}

function RingkasanLolos({ ringkasan, peringatan }) {
  return (
    <>
      <div className="panel-info panel-hijau">
        <strong style={{ display: 'block', marginBottom: 6 }}>
          Pemeriksaan selesai, tidak ada kesalahan
        </strong>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
            gap: '4px 16px',
          }}
        >
          <span>{angka(ringkasan.baris_terbaca)} baris terbaca</span>
          <span>
            {tanggal(ringkasan.rentang_tanggal.awal)} – {tanggal(ringkasan.rentang_tanggal.akhir)}
          </span>
          <span>
            {ringkasan.kecamatan_ada} dari {ringkasan.kecamatan_master} kecamatan
          </span>
          <span>
            {ringkasan.kelurahan_ada} dari {ringkasan.kelurahan_master} kelurahan
          </span>
          <span>{angka(ringkasan.baris_baru)} baris baru</span>
          <span>{angka(ringkasan.baris_diperbarui)} baris diperbarui</span>
        </div>
      </div>

      {peringatan.length > 0 && (
        <div className="panel-info panel-kuning">
          <strong style={{ display: 'block', marginBottom: 6 }}>
            Penyesuaian otomatis saat menyimpan
          </strong>
          <ul style={{ margin: 0, paddingLeft: 18, display: 'grid', gap: 3 }}>
            {peringatan.map((p, i) => (
              <li key={`${p.kode}-${i}`}>
                {p.pesan}
                {p.baris?.length > 0 && p.baris.length <= 6 && (
                  <span style={{ opacity: 0.8 }}> — baris {p.baris.join(', ')}</span>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </>
  )
}

function DaftarKesalahan({ kesalahan }) {
  const tampil = kesalahan.slice(0, KESALAHAN_DITAMPILKAN)
  const sisa = kesalahan.length - tampil.length

  return (
    <div className="panel-info panel-merah" role="alert">
      <strong style={{ display: 'block', marginBottom: 8 }}>
        Daftar kesalahan ({kesalahan.length})
      </strong>
      <ol style={{ margin: 0, paddingLeft: 20, display: 'grid', gap: 9 }}>
        {tampil.map((k, i) => (
          <li key={`${k.kode}-${i}`}>
            <div style={{ fontWeight: 600 }}>{k.judul}</div>
            <div style={{ opacity: 0.9 }}>{k.detail}</div>
            {k.baris?.length > 0 && (
              <div style={{ opacity: 0.75, fontSize: 12.5, marginTop: 2 }}>
                Baris {k.baris.slice(0, 12).join(', ')}
                {k.baris.length > 12 && `, dan ${k.baris.length - 12} baris lain`}
              </div>
            )}
          </li>
        ))}
      </ol>
      {sisa > 0 && (
        <div style={{ marginTop: 9, fontWeight: 600 }}>dan {sisa} kesalahan lain</div>
      )}
      <p style={{ margin: '11px 0 0', fontSize: 12.5, opacity: 0.9 }}>
        Perbaiki berkas lalu jalankan Cek File lagi. Tidak ada data yang tersimpan.
      </p>
    </div>
  )
}
