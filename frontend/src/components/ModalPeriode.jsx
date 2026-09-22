import { useMemo, useState } from 'react'

import { labelPeriode, labelPeriodeBulan, tanggalPendek } from '../format.js'
import { IkonPanahKanan, IkonPanahKiri } from './Ikon.jsx'
import Modal from './Modal.jsx'

/**
 * Modal pemilih periode (bagian 7.2).
 *
 * Dua mode:
 *   Bulan   — kisi 12 bulan; klik bulan pertama lalu bulan kedua untuk
 *             menutup rentang. Bulan di luar data tersedia dinonaktifkan.
 *   Tanggal — dua kotak tanggal untuk rentang bebas.
 *
 * Pilihan baru hanya berlaku setelah tombol "Terapkan" ditekan, jadi
 * dashboard tidak memuat ulang pada tiap klik.
 *
 * Bulan berjalan otomatis berhenti di hari ini: batas.akhir sudah dipotong
 * backend, dan seluruh nilai di sini dijepit ke dalam batas itu.
 */

const BULAN_SINGKAT = [
  'Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun',
  'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des',
]

/** "2026-09-19" -> "2026-09" */
function keBulan(iso) {
  return iso ? String(iso).slice(0, 7) : ''
}

/** "2026-09" -> "2026-09-01" */
function awalBulan(bulan) {
  return bulan ? `${bulan}-01` : ''
}

/** "2026-09" -> "2026-09-30" */
function akhirBulan(bulan) {
  if (!bulan) return ''
  const [thn, bln] = bulan.split('-').map(Number)
  const hari = new Date(thn, bln, 0).getDate()
  return `${bulan}-${String(hari).padStart(2, '0')}`
}

/** "2026-09" digeser -2 -> "2026-07" */
function geserBulan(bulan, langkah) {
  const [thn, bln] = bulan.split('-').map(Number)
  const titik = new Date(thn, bln - 1 + langkah, 1)
  return `${titik.getFullYear()}-${String(titik.getMonth() + 1).padStart(2, '0')}`
}

export default function ModalPeriode({ mode, dari, sampai, batas, onTerapkan, onTutup }) {
  const [modeDraf, setModeDraf] = useState(mode)
  const [dariDraf, setDariDraf] = useState(dari || batas.awal || '')
  const [sampaiDraf, setSampaiDraf] = useState(sampai || batas.akhir || '')
  const [menunggu, setMenunggu] = useState('')
  const [tahun, setTahun] = useState(() =>
    Number((sampai || batas.akhir || `${new Date().getFullYear()}-01-01`).slice(0, 4)),
  )

  const tahunMin = batas.awal ? Number(batas.awal.slice(0, 4)) : tahun
  const tahunMaks = batas.akhir ? Number(batas.akhir.slice(0, 4)) : tahun

  /** Tidak ada nilai yang boleh keluar dari rentang data yang tersedia. */
  function jepit(iso) {
    if (!iso) return ''
    let nilai = iso
    if (batas.awal && nilai < batas.awal) nilai = batas.awal
    if (batas.akhir && nilai > batas.akhir) nilai = batas.akhir
    return nilai
  }

  const pilihanCepat = useMemo(() => {
    if (!batas.awal || !batas.akhir) return []
    const bulanAkhir = keBulan(batas.akhir)
    const dalamBatas = (iso) => {
      if (iso < batas.awal) return batas.awal
      return iso > batas.akhir ? batas.akhir : iso
    }
    return [
      { kunci: 'semua', nama: 'Semua periode', dari: batas.awal, sampai: batas.akhir },
      {
        kunci: 'bulan',
        nama: 'Bulan terakhir',
        dari: dalamBatas(awalBulan(bulanAkhir)),
        sampai: batas.akhir,
      },
      {
        kunci: 'tiga',
        nama: '3 bulan terakhir',
        dari: dalamBatas(awalBulan(geserBulan(bulanAkhir, -2))),
        sampai: batas.akhir,
      },
    ]
  }, [batas.awal, batas.akhir])

  const cepatAktif = pilihanCepat.find(
    (p) => p.dari === dariDraf && p.sampai === sampaiDraf,
  )?.kunci

  const bulanAwalDraf = keBulan(dariDraf)
  const bulanAkhirDraf = keBulan(sampaiDraf)

  function tersedia(kunci) {
    if (!batas.awal || !batas.akhir) return false
    return akhirBulan(kunci) >= batas.awal && awalBulan(kunci) <= batas.akhir
  }

  function klikBulan(kunci) {
    if (!menunggu) {
      // Klik pertama menetapkan satu bulan penuh; klik kedua melebarkannya.
      setMenunggu(kunci)
      setDariDraf(jepit(awalBulan(kunci)))
      setSampaiDraf(jepit(akhirBulan(kunci)))
      return
    }
    const [awal, akhir] = menunggu <= kunci ? [menunggu, kunci] : [kunci, menunggu]
    setDariDraf(jepit(awalBulan(awal)))
    setSampaiDraf(jepit(akhirBulan(akhir)))
    setMenunggu('')
  }

  function pakaiCepat(pilihan) {
    setMenunggu('')
    setDariDraf(pilihan.dari)
    setSampaiDraf(pilihan.sampai)
    setTahun(Number(pilihan.sampai.slice(0, 4)))
  }

  function gantiMode(baru) {
    setMenunggu('')
    // Mode Bulan bekerja pada bulan penuh, jadi rentang bebas dibulatkan
    // lebih dulu supaya kisi bulan menyorot hal yang sama dengan nilainya.
    if (baru === 'bulan' && dariDraf && sampaiDraf) {
      setDariDraf(jepit(awalBulan(keBulan(dariDraf))))
      setSampaiDraf(jepit(akhirBulan(keBulan(sampaiDraf))))
    }
    setModeDraf(baru)
  }

  const tidakUrut = Boolean(dariDraf && sampaiDraf && dariDraf > sampaiDraf)
  const siap = Boolean(dariDraf && sampaiDraf && !tidakUrut)

  const teksTerpilih =
    modeDraf === 'bulan'
      ? labelPeriodeBulan(dariDraf, sampaiDraf)
      : labelPeriode(dariDraf, sampaiDraf)

  const saklar = (
    <div className="segmen" role="group" aria-label="Mode periode">
      <button type="button" aria-pressed={modeDraf === 'bulan'} onClick={() => gantiMode('bulan')}>
        Bulan
      </button>
      <button
        type="button"
        aria-pressed={modeDraf === 'tanggal'}
        onClick={() => gantiMode('tanggal')}
      >
        Tanggal
      </button>
    </div>
  )

  const kaki = (
    <>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, minWidth: 0 }}>
        <span style={{ fontSize: 13, color: 'var(--teks-samar)' }}>Terpilih</span>
        <strong style={{ fontSize: 14, fontWeight: 600 }}>{teksTerpilih}</strong>
      </div>
      <button
        type="button"
        className="tombol-utama"
        onClick={() => onTerapkan({ mode: modeDraf, dari: jepit(dariDraf), sampai: jepit(sampaiDraf) })}
        disabled={!siap}
        style={{ padding: '11px 22px', fontSize: 13.5 }}
      >
        Terapkan
      </button>
    </>
  )

  return (
    <Modal judul="Periode data" alatKepala={saklar} lebar={720} kaki={kaki} onTutup={onTutup}>
      <div className="isi-periode">
        <div className="sisi-periode">
          {pilihanCepat.map((pilihan) => (
            <button
              key={pilihan.kunci}
              type="button"
              className="preset"
              aria-pressed={cepatAktif === pilihan.kunci}
              onClick={() => pakaiCepat(pilihan)}
            >
              {pilihan.nama}
            </button>
          ))}

          <div style={{ marginTop: 'auto', paddingTop: 22, paddingLeft: 14 }}>
            <div style={{ fontSize: 12.5, color: 'var(--teks-samar)' }}>Data tersedia</div>
            <div style={{ fontSize: 13, fontWeight: 600, marginTop: 3 }}>
              {tanggalPendek(batas.awal)} – {tanggalPendek(batas.akhir)}
            </div>
          </div>
        </div>

        <div style={{ padding: '18px 22px 22px' }}>
          {modeDraf === 'bulan' ? (
            <>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: 12,
                  marginBottom: 16,
                }}
              >
                <button
                  type="button"
                  className="tombol-bulat"
                  onClick={() => setTahun((t) => t - 1)}
                  disabled={tahun <= tahunMin}
                  aria-label={`Tahun ${tahun - 1}`}
                >
                  <IkonPanahKiri />
                </button>
                <strong style={{ fontSize: 15.5, fontWeight: 600 }}>{tahun}</strong>
                <button
                  type="button"
                  className="tombol-bulat"
                  onClick={() => setTahun((t) => t + 1)}
                  disabled={tahun >= tahunMaks}
                  aria-label={`Tahun ${tahun + 1}`}
                >
                  <IkonPanahKanan />
                </button>
              </div>

              <div className="kisi-bulan">
                {BULAN_SINGKAT.map((nama, urutan) => {
                  const kunci = `${tahun}-${String(urutan + 1).padStart(2, '0')}`
                  const bisa = tersedia(kunci)
                  const dalamRentang = kunci >= bulanAwalDraf && kunci <= bulanAkhirDraf
                  const ujung = kunci === bulanAwalDraf || kunci === bulanAkhirDraf
                  const kelas = [
                    'sel-bulan',
                    dalamRentang && !ujung ? 'sel-bulan-rentang' : '',
                    ujung ? 'sel-bulan-ujung' : '',
                  ]
                    .filter(Boolean)
                    .join(' ')

                  return (
                    <button
                      key={kunci}
                      type="button"
                      className={kelas}
                      disabled={!bisa}
                      aria-pressed={dalamRentang}
                      onClick={() => klikBulan(kunci)}
                      title={bisa ? undefined : 'Tidak ada data pada bulan ini'}
                    >
                      {nama}
                    </button>
                  )
                })}
              </div>

              <p style={{ margin: '16px 0 0', fontSize: 13, color: 'var(--teks-samar)' }}>
                {menunggu
                  ? 'Klik bulan kedua untuk menutup rentang.'
                  : 'Klik satu bulan untuk memulai rentang.'}
              </p>
            </>
          ) : (
            <>
              <div className="kisi-filter">
                <label className="label-isian">
                  Tanggal mulai
                  <input
                    className="isian"
                    type="date"
                    value={dariDraf || ''}
                    min={batas.awal || undefined}
                    max={batas.akhir || undefined}
                    onChange={(e) => setDariDraf(e.target.value)}
                    style={{ height: 44 }}
                  />
                </label>

                <label className="label-isian">
                  Tanggal akhir
                  <input
                    className="isian"
                    type="date"
                    value={sampaiDraf || ''}
                    min={batas.awal || undefined}
                    max={batas.akhir || undefined}
                    onChange={(e) => setSampaiDraf(e.target.value)}
                    style={{ height: 44 }}
                  />
                </label>
              </div>

              <p style={{ margin: '16px 0 0', fontSize: 13, color: 'var(--teks-samar)' }}>
                Gunakan mode Bulan untuk rekapitulasi bulanan.
              </p>
            </>
          )}

          {tidakUrut && (
            <p style={{ margin: '12px 0 0', fontSize: 13, color: 'var(--merah-teks)' }} role="alert">
              Tanggal mulai melewati tanggal akhir.
            </p>
          )}
        </div>
      </div>
    </Modal>
  )
}
