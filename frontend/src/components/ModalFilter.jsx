import { useMemo, useState } from 'react'

import Modal from './Modal.jsx'

/**
 * Modal filter data: jenis kendaraan, status, kecamatan, dan kelurahan.
 *
 * Penyesuaian wajib terhadap prototipe (bagian 3): filter "Lokasi proses"
 * DIHAPUS PERMANEN — tidak ada kolom, parameter, maupun elemen UI untuk itu.
 *
 * Tiap kotak pilih dibungkus <label> supaya punya nama yang terbaca pembaca
 * layar; tanpa itu axe-core menandainya sebagai pelanggaran select-name.
 *
 * Pilihan baru hanya berlaku setelah "Terapkan" ditekan.
 */

const KOSONG = { roda: '', status: '', kecamatan: '', kelurahan: '' }

export default function ModalFilter({ filter, wilayah, onTerapkan, onTutup }) {
  const [draf, setDraf] = useState({
    roda: filter.roda || '',
    status: filter.status || '',
    kecamatan: filter.kecamatan || '',
    kelurahan: filter.kelurahan || '',
  })

  const kelurahanTersedia = useMemo(() => {
    if (!draf.kecamatan) return wilayah.flatMap((w) => w.kelurahan)
    const cocok = wilayah.find((w) => w.kecamatan === draf.kecamatan)
    return cocok ? cocok.kelurahan : []
  }, [wilayah, draf.kecamatan])

  function ubah(bagian) {
    setDraf((lama) => ({ ...lama, ...bagian }))
  }

  function gantiKecamatan(nilai) {
    // Kelurahan yang tidak lagi berada di kecamatan terpilih harus dilepas,
    // kalau tidak backend akan menolak kombinasinya.
    ubah({ kecamatan: nilai, kelurahan: '' })
  }

  const kaki = (
    <>
      <button type="button" className="tombol-biasa" onClick={() => setDraf(KOSONG)}>
        Reset filter
      </button>
      <button
        type="button"
        className="tombol-utama"
        onClick={() => onTerapkan(draf)}
        style={{ padding: '11px 22px', fontSize: 13.5 }}
      >
        Terapkan
      </button>
    </>
  )

  return (
    <Modal judul="Filter data" lebar={620} kaki={kaki} onTutup={onTutup}>
      <div className="kisi-filter" style={{ padding: '22px 22px 24px' }}>
        <label className="label-isian">
          Jenis kendaraan
          <select
            className="isian"
            style={{ height: 44 }}
            value={draf.roda}
            onChange={(e) => ubah({ roda: e.target.value })}
          >
            <option value="">SEMUA</option>
            <option value="2">Roda 2</option>
            <option value="4">Roda 4</option>
          </select>
        </label>

        <label className="label-isian">
          Status
          <select
            className="isian"
            style={{ height: 44 }}
            value={draf.status}
            onChange={(e) => ubah({ status: e.target.value })}
          >
            <option value="">SEMUA</option>
            <option value="LUNAS">Lunas</option>
            <option value="BELUM_LUNAS">Belum lunas</option>
          </select>
        </label>

        <label className="label-isian">
          Kecamatan
          <select
            className="isian"
            style={{ height: 44 }}
            value={draf.kecamatan}
            onChange={(e) => gantiKecamatan(e.target.value)}
          >
            <option value="">SEMUA</option>
            {wilayah.map((w) => (
              <option key={w.kecamatan} value={w.kecamatan}>
                {w.kecamatan}
              </option>
            ))}
          </select>
        </label>

        <label className="label-isian">
          Kelurahan / desa
          <select
            className="isian"
            style={{ height: 44 }}
            value={draf.kelurahan}
            onChange={(e) => ubah({ kelurahan: e.target.value })}
          >
            <option value="">SEMUA</option>
            {kelurahanTersedia.map((kel) => (
              <option key={kel} value={kel}>
                {kel}
              </option>
            ))}
          </select>
        </label>
      </div>
    </Modal>
  )
}
