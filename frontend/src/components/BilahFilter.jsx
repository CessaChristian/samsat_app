import { useMemo } from 'react'

import { labelPeriode } from '../format.js'

/**
 * Bilah filter dashboard.
 *
 * Penyesuaian wajib terhadap prototipe (bagian 3): filter "Lokasi proses"
 * DIHAPUS PERMANEN — tidak ada kolom, parameter, maupun elemen UI untuk itu.
 *
 * Periode punya dua mode (bagian 7.2):
 *   Bulan   — pilih bulan awal dan akhir; bulan berjalan otomatis berhenti di
 *             hari ini karena backend memotong "sampai".
 *   Tanggal — pilih tanggal awal dan akhir, akhir maksimal hari ini.
 *
 * Label di layar selalu menyebut tanggal, bukan nama bulan saja, supaya tidak
 * disalahpahami sebagai bulan penuh.
 */

const gayaKolom = { display: 'flex', flexDirection: 'column', gap: 7, minWidth: 0 }

const gayaLabel = { fontSize: 12, fontWeight: 600, color: 'var(--teks-label)' }

const gayaKendali = {
  height: 40,
  padding: '0 12px',
  border: '1px solid var(--garis-input)',
  borderRadius: 'var(--radius-kecil)',
  background: '#fff',
  fontSize: 13.5,
  color: 'var(--teks)',
  minWidth: 0,
}

/** "2026-09" -> "2026-09-01" */
function awalBulan(bulan) {
  return bulan ? `${bulan}-01` : ''
}

/** "2026-09" -> "2026-09-30" */
function akhirBulan(bulan) {
  if (!bulan) return ''
  const [tahun, bln] = bulan.split('-').map(Number)
  const hari = new Date(tahun, bln, 0).getDate()
  return `${bulan}-${String(hari).padStart(2, '0')}`
}

/** "2026-09-19" -> "2026-09" */
function keBulan(tanggal) {
  return tanggal ? String(tanggal).slice(0, 7) : ''
}

export default function BilahFilter({
  filter,
  onUbah,
  onReset,
  wilayah,
  batasPeriode,
  periodeAktif,
  mode,
  onUbahMode,
  filterBawaan,
}) {
  const kelurahanTersedia = useMemo(() => {
    if (!filter.kecamatan) return wilayah.flatMap((w) => w.kelurahan)
    const cocok = wilayah.find((w) => w.kecamatan === filter.kecamatan)
    return cocok ? cocok.kelurahan : []
  }, [wilayah, filter.kecamatan])

  // Tombol Reset hanya berguna bila ada yang menyimpang dari bawaan.
  const adaFilterAktif =
    Boolean(filter.roda || filter.status || filter.kecamatan || filter.kelurahan) ||
    filter.dari !== (filterBawaan?.dari ?? '') ||
    filter.sampai !== (filterBawaan?.sampai ?? '')

  function gantiKecamatan(nilai) {
    // Kelurahan yang tidak lagi berada di kecamatan terpilih harus dilepas,
    // kalau tidak backend akan menolak kombinasinya.
    onUbah({ kecamatan: nilai, kelurahan: '' })
  }

  return (
    <section style={{ padding: '26px 32px 0' }} data-no-print>
      <div style={{ display: 'flex', alignItems: 'flex-end', gap: 14, flexWrap: 'wrap' }}>
        <div style={{ ...gayaKolom, flex: '1 1 260px' }}>
          <span style={gayaLabel}>Periode</span>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
            <select
              style={{ ...gayaKendali, flex: '0 0 auto' }}
              value={mode}
              onChange={(e) => onUbahMode(e.target.value)}
              aria-label="Mode periode"
            >
              <option value="bulan">Bulan</option>
              <option value="tanggal">Tanggal</option>
            </select>

            {mode === 'bulan' ? (
              <>
                <input
                  type="month"
                  style={{ ...gayaKendali, flex: '1 1 130px' }}
                  value={keBulan(filter.dari)}
                  min={keBulan(batasPeriode.awal)}
                  max={keBulan(batasPeriode.akhir)}
                  onChange={(e) => onUbah({ dari: awalBulan(e.target.value) })}
                  aria-label="Bulan awal"
                />
                <span style={{ color: 'var(--teks-samar-3)' }}>–</span>
                <input
                  type="month"
                  style={{ ...gayaKendali, flex: '1 1 130px' }}
                  value={keBulan(filter.sampai)}
                  min={keBulan(batasPeriode.awal)}
                  max={keBulan(batasPeriode.akhir)}
                  onChange={(e) => onUbah({ sampai: akhirBulan(e.target.value) })}
                  aria-label="Bulan akhir"
                />
              </>
            ) : (
              <>
                <input
                  type="date"
                  style={{ ...gayaKendali, flex: '1 1 140px' }}
                  value={filter.dari || ''}
                  min={batasPeriode.awal || undefined}
                  max={batasPeriode.akhir || undefined}
                  onChange={(e) => onUbah({ dari: e.target.value })}
                  aria-label="Tanggal mulai"
                />
                <span style={{ color: 'var(--teks-samar-3)' }}>–</span>
                <input
                  type="date"
                  style={{ ...gayaKendali, flex: '1 1 140px' }}
                  value={filter.sampai || ''}
                  min={batasPeriode.awal || undefined}
                  max={batasPeriode.akhir || undefined}
                  onChange={(e) => onUbah({ sampai: e.target.value })}
                  aria-label="Tanggal akhir"
                />
              </>
            )}
          </div>
        </div>

        <div style={{ ...gayaKolom, flex: '0 1 165px' }}>
          <span style={gayaLabel}>Jenis kendaraan</span>
          <select
            style={gayaKendali}
            value={filter.roda || ''}
            onChange={(e) => onUbah({ roda: e.target.value })}
          >
            <option value="">Semua</option>
            <option value="2">Roda 2</option>
            <option value="4">Roda 4</option>
          </select>
        </div>

        <div style={{ ...gayaKolom, flex: '0 1 175px' }}>
          <span style={gayaLabel}>Status</span>
          <select
            style={gayaKendali}
            value={filter.status || ''}
            onChange={(e) => onUbah({ status: e.target.value })}
          >
            <option value="">Semua</option>
            <option value="LUNAS">Lunas</option>
            <option value="BELUM_LUNAS">Belum lunas</option>
          </select>
        </div>

        <div style={{ ...gayaKolom, flex: '0 1 190px' }}>
          <span style={gayaLabel}>Kecamatan</span>
          <select
            style={gayaKendali}
            value={filter.kecamatan || ''}
            onChange={(e) => gantiKecamatan(e.target.value)}
          >
            <option value="">Semua</option>
            {wilayah.map((w) => (
              <option key={w.kecamatan} value={w.kecamatan}>
                {w.kecamatan}
              </option>
            ))}
          </select>
        </div>

        <div style={{ ...gayaKolom, flex: '0 1 215px' }}>
          <span style={gayaLabel}>Kelurahan / desa</span>
          <select
            style={gayaKendali}
            value={filter.kelurahan || ''}
            onChange={(e) => onUbah({ kelurahan: e.target.value })}
          >
            <option value="">Semua</option>
            {kelurahanTersedia.map((kel) => (
              <option key={kel} value={kel}>
                {kel}
              </option>
            ))}
          </select>
        </div>

        <button
          type="button"
          className="tombol-biasa"
          onClick={onReset}
          disabled={!adaFilterAktif}
          style={{ height: 40 }}
        >
          Reset
        </button>
      </div>

      <div
        style={{
          marginTop: 12,
          fontSize: 12.5,
          color: 'var(--teks-samar-2)',
        }}
      >
        Menampilkan periode{' '}
        <strong style={{ fontWeight: 600, color: 'var(--teks-sedang)' }}>
          {labelPeriode(periodeAktif?.dari, periodeAktif?.sampai)}
        </strong>
        {' · '}jatuh tempo setelah hari ini tidak ikut dihitung
      </div>
    </section>
  )
}
