import { useCallback, useEffect, useState } from 'react'

import { api } from '../api/klien.js'
import BilahFilter from '../components/BilahFilter.jsx'
import GrafikKecamatan from '../components/GrafikKecamatan.jsx'
import Header from '../components/Header.jsx'
import KartuKpi from '../components/KartuKpi.jsx'
import KomposisiObjek from '../components/KomposisiObjek.jsx'
import LayarKosong from '../components/LayarKosong.jsx'
import ModalUnggah from '../components/ModalUnggah.jsx'
import TabelWilayah from '../components/TabelWilayah.jsx'
import { angka, labelPeriode } from '../format.js'

const FILTER_KOSONG = {
  dari: '',
  sampai: '',
  roda: '',
  status: '',
  kecamatan: '',
  kelurahan: '',
}

/**
 * Filter awal: periode diisi rentang penuh yang tersedia supaya kotak tanggal
 * tidak tampil kosong. Nilainya sama dengan bawaan backend, jadi tampilan dan
 * perhitungan tetap sejalan.
 */
function filterAwal(periode) {
  return {
    ...FILTER_KOSONG,
    dari: periode?.awal || '',
    sampai: periode?.akhir || '',
  }
}

/**
 * Halaman utama. Tiga keadaan yang harus ada (bagian 3):
 *   - belum ada data  -> kerangka abu dan ajakan unggah
 *   - berisi data     -> kartu, grafik, dan tabel
 *   - modal unggah    -> alur Cek File lalu Simpan
 */
export default function Dashboard({ pengguna, onKeluar }) {
  const [meta, setMeta] = useState(null)
  const [rekap, setRekap] = useState(null)
  const [filter, setFilter] = useState(FILTER_KOSONG)
  const [modePeriode, setModePeriode] = useState('bulan')
  const [modalBuka, setModalBuka] = useState(false)
  const [memuat, setMemuat] = useState(true)
  const [galat, setGalat] = useState('')
  const [kabar, setKabar] = useState('')

  const muatMeta = useCallback(async () => {
    const hasil = await api.meta()
    setMeta(hasil)
    return hasil
  }, [])

  const muatRekap = useCallback(async (saringan) => {
    const hasil = await api.rekap(saringan)
    setRekap(hasil)
    return hasil
  }, [])

  // Muat pertama kali.
  useEffect(() => {
    let batal = false
    ;(async () => {
      try {
        const hasilMeta = await muatMeta()
        if (batal) return
        if (hasilMeta.ada_data) {
          const awal = filterAwal(hasilMeta.periode)
          setFilter(awal)
          await muatRekap(awal)
        }
      } catch (e) {
        if (!batal) setGalat(e.message || 'Gagal memuat data.')
      } finally {
        if (!batal) setMemuat(false)
      }
    })()
    return () => {
      batal = true
    }
  }, [muatMeta, muatRekap])

  // Muat ulang tiap filter berubah.
  useEffect(() => {
    if (!meta?.ada_data) return
    let batal = false
    ;(async () => {
      try {
        await muatRekap(filter)
        if (!batal) setGalat('')
      } catch (e) {
        if (!batal) setGalat(e.message || 'Gagal memuat rekapitulasi.')
      }
    })()
    return () => {
      batal = true
    }
  }, [filter, meta?.ada_data, muatRekap])

  const ubahFilter = useCallback((bagian) => {
    setFilter((lama) => ({ ...lama, ...bagian }))
  }, [])

  const resetFilter = useCallback(
    () => setFilter(filterAwal(meta?.periode)),
    [meta?.periode],
  )

  /**
   * Periode dan modenya berubah bersamaan saat modal ditutup dengan
   * "Terapkan", supaya rekap hanya dimuat ulang satu kali.
   */
  const terapkanPeriode = useCallback(({ mode, dari, sampai }) => {
    setModePeriode(mode)
    setFilter((lama) => ({ ...lama, dari, sampai }))
  }, [])

  async function setelahTersimpan(hasilSimpan) {
    setModalBuka(false)
    setMemuat(true)
    setKabar(
      `Tersimpan: ${angka(hasilSimpan.baris_baru)} baris baru, ` +
        `${angka(hasilSimpan.baris_diperbarui)} baris diperbarui.`,
    )
    try {
      const hasilMeta = await muatMeta()
      const awal = filterAwal(hasilMeta.periode)
      setFilter(awal)
      if (hasilMeta.ada_data) await muatRekap(awal)
    } catch (e) {
      setGalat(e.message || 'Data tersimpan, tetapi dashboard gagal dimuat ulang.')
    } finally {
      setMemuat(false)
    }
  }

  if (memuat && !meta) {
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
        Memuat dashboard…
      </div>
    )
  }

  const adaData = Boolean(meta?.ada_data)

  return (
    <div className="laman">
      <Header
        adaData={adaData}
        batchTerakhir={meta?.batch_terakhir}
        onUnggah={() => setModalBuka(true)}
        pengguna={pengguna}
        onKeluar={onKeluar}
      />

      {kabar && (
        <div style={{ padding: '14px 32px 0' }} data-no-print>
          <div
            className="panel-info panel-hijau"
            role="status"
            style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}
          >
            <span>{kabar}</span>
            <button
              type="button"
              onClick={() => setKabar('')}
              style={{
                border: 'none',
                background: 'none',
                cursor: 'pointer',
                color: 'inherit',
                fontWeight: 600,
              }}
            >
              Tutup
            </button>
          </div>
        </div>
      )}

      {galat && (
        <div style={{ padding: '14px 32px 0' }} data-no-print>
          <div className="panel-info panel-merah" role="alert">
            {galat}
          </div>
        </div>
      )}

      <main>
      {!adaData ? (
        <LayarKosong onUnggah={() => setModalBuka(true)} />
      ) : (
        <>
          <BilahFilter
            filter={filter}
            onUbah={ubahFilter}
            onReset={resetFilter}
            wilayah={meta.wilayah}
            batasPeriode={meta.periode}
            filterBawaan={filterAwal(meta.periode)}
            periodeAktif={rekap?.periode}
            mode={modePeriode}
            onTerapkanPeriode={terapkanPeriode}
          />

          {rekap && (
            <>
              <KartuKpi
                kpi={rekap.kpi}
                persentase={rekap.persentase}
                komposisi={rekap.komposisi}
              />

              <section
                style={{
                  padding: '14px 32px 0',
                  display: 'grid',
                  gridTemplateColumns: 'minmax(0, 1.6fr) minmax(0, 1fr)',
                  gap: 14,
                  alignItems: 'start',
                }}
              >
                <GrafikKecamatan data={rekap.per_kecamatan} />
                <KomposisiObjek data={rekap.komposisi} />
              </section>

              <TabelWilayah baris={rekap.per_wilayah} total={rekap.total} />

              <section style={{ padding: '0 32px 48px', marginTop: -28 }} data-no-print>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    gap: 14,
                    flexWrap: 'wrap',
                  }}
                >
                  <span style={{ fontSize: 12.5, color: 'var(--teks-samar-2)' }}>
                    Export mengikuti filter yang sedang berlaku ·{' '}
                    {labelPeriode(rekap.periode.dari, rekap.periode.sampai)}
                  </span>
                  <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                    <a
                      className="tombol-biasa"
                      href={api.urlExport('xlsx', filter)}
                      style={{ textDecoration: 'none' }}
                    >
                      Export Excel
                    </a>
                    <a
                      className="tombol-biasa"
                      href={api.urlExport('pdf', filter)}
                      style={{ textDecoration: 'none' }}
                    >
                      Export PDF
                    </a>
                  </div>
                </div>
              </section>
            </>
          )}
        </>
      )}
      </main>

      {modalBuka && (
        <ModalUnggah onTutup={() => setModalBuka(false)} onTersimpan={setelahTersimpan} />
      )}
    </div>
  )
}
