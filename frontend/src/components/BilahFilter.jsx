import { useMemo, useState } from 'react'

import { labelPeriode, labelPeriodeBulan } from '../format.js'
import { IkonFilter, IkonKalender, IkonPanahBawah } from './Ikon.jsx'
import ModalFilter from './ModalFilter.jsx'
import ModalPeriode from './ModalPeriode.jsx'

/**
 * Bilah filter dashboard.
 *
 * Bilah ini hanya memuat dua pemicu dan satu tombol Reset; seluruh pilihan
 * ada di dalam modal Periode dan modal Filter data. Pilihan baru berlaku
 * setelah "Terapkan", jadi dashboard memuat ulang sekali, bukan pada tiap
 * perubahan satu kotak.
 *
 * Penyesuaian wajib terhadap prototipe: filter "Lokasi proses"
 * DIHAPUS PERMANEN — tidak ada kolom, parameter, maupun elemen UI untuk itu.
 *
 * Pemicu periode menyebut nama bulan saat mode Bulan, tetapi baris keterangan
 * di bawahnya tetap menyebut tanggal persis. Itu wajib: bulan berjalan
 * berhenti di hari ini, jadi "September 2026" saja bisa disalahpahami sebagai
 * bulan penuh.
 */

const gayaLabel = { fontSize: 12, fontWeight: 600, color: 'var(--teks-label)' }

const gayaKolom = { display: 'flex', flexDirection: 'column', gap: 7, minWidth: 0 }

export default function BilahFilter({
  filter,
  onUbah,
  onTerapkanPeriode,
  onReset,
  wilayah,
  batasPeriode,
  periodeAktif,
  mode,
  filterBawaan,
}) {
  const [modal, setModal] = useState('')

  // Tombol Reset hanya berguna bila ada yang menyimpang dari bawaan.
  const adaFilterAktif =
    Boolean(filter.roda || filter.status || filter.kecamatan || filter.kelurahan) ||
    filter.dari !== (filterBawaan?.dari ?? '') ||
    filter.sampai !== (filterBawaan?.sampai ?? '')

  const adaSaringan = Boolean(
    filter.roda || filter.status || filter.kecamatan || filter.kelurahan,
  )

  const teksPeriode =
    mode === 'bulan'
      ? labelPeriodeBulan(filter.dari, filter.sampai)
      : labelPeriode(filter.dari, filter.sampai)

  const teksSaringan = useMemo(() => {
    const bagian = []
    if (filter.roda) bagian.push(`Roda ${filter.roda}`)
    if (filter.status) bagian.push(filter.status === 'LUNAS' ? 'Lunas' : 'Belum lunas')
    if (filter.kelurahan) bagian.push(filter.kelurahan)
    else if (filter.kecamatan) bagian.push(filter.kecamatan)
    return bagian.length ? bagian.join(' · ') : 'Semua data'
  }, [filter.roda, filter.status, filter.kecamatan, filter.kelurahan])

  return (
    <section style={{ padding: '26px 32px 0' }} data-no-print>
      <div style={{ display: 'flex', alignItems: 'flex-end', gap: 16, flexWrap: 'wrap' }}>
        <div style={{ ...gayaKolom, flex: '1 1 280px' }}>
          <span id="label-periode" style={{ ...gayaLabel, color: 'var(--biru-lebih-tua)' }}>
            Periode
          </span>
          <button
            type="button"
            className="pemicu pemicu-terisi"
            aria-haspopup="dialog"
            aria-expanded={modal === 'periode'}
            aria-labelledby="label-periode isi-periode"
            onClick={() => setModal('periode')}
          >
            <IkonKalender className="pemicu-tanda" style={{ flex: '0 0 auto' }} />
            <span id="isi-periode" className="pemicu-isi">
              {teksPeriode}
            </span>
            <IkonPanahBawah className="pemicu-tanda" />
          </button>
        </div>

        <div style={{ ...gayaKolom, flex: '1 1 300px' }}>
          <span id="label-saringan" style={gayaLabel}>
            Filter data
          </span>
          <button
            type="button"
            className={`pemicu${adaSaringan ? ' pemicu-terisi' : ''}`}
            aria-haspopup="dialog"
            aria-expanded={modal === 'filter'}
            aria-labelledby="label-saringan isi-saringan"
            onClick={() => setModal('filter')}
          >
            <IkonFilter className="pemicu-tanda" style={{ flex: '0 0 auto' }} />
            <span id="isi-saringan" className="pemicu-isi">
              {teksSaringan}
            </span>
            <IkonPanahBawah className="pemicu-tanda" />
          </button>
        </div>

        <button
          type="button"
          className="tombol-biasa"
          onClick={onReset}
          disabled={!adaFilterAktif}
          style={{ height: 44, padding: '0 18px' }}
        >
          Reset
        </button>
      </div>

      <div style={{ marginTop: 12, fontSize: 12.5, color: 'var(--teks-samar-2)' }}>
        Menampilkan periode{' '}
        <strong style={{ fontWeight: 600, color: 'var(--teks-sedang)' }}>
          {labelPeriode(periodeAktif?.dari, periodeAktif?.sampai)}
        </strong>
        {' · '}jatuh tempo setelah hari ini tidak ikut dihitung
      </div>

      {modal === 'periode' && (
        <ModalPeriode
          mode={mode}
          dari={filter.dari}
          sampai={filter.sampai}
          batas={batasPeriode}
          onTutup={() => setModal('')}
          onTerapkan={(pilihan) => {
            onTerapkanPeriode(pilihan)
            setModal('')
          }}
        />
      )}

      {modal === 'filter' && (
        <ModalFilter
          filter={filter}
          wilayah={wilayah}
          onTutup={() => setModal('')}
          onTerapkan={(pilihan) => {
            onUbah(pilihan)
            setModal('')
          }}
        />
      )}
    </section>
  )
}
