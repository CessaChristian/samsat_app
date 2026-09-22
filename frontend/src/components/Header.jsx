import logoJasaraharja from '../assets/logo-jasaraharja.png'
import logoJateng from '../assets/logo-jateng.png'
import logoPolda from '../assets/logo-polda.png'
import { waktu } from '../format.js'
import { IkonKeluar, IkonUnggah } from './Ikon.jsx'

/**
 * Kepala halaman: lambang instansi, nama, keterangan data terakhir, dan
 * tombol unggah.
 *
 * Spesifikasi bagian 3 meminta header menyebut "Data per <tanggal unggah
 * terakhir>" berdasarkan batch terakhir yang tersimpan.
 */
export default function Header({ batchTerakhir, adaData, onUnggah, pengguna, onKeluar }) {
  return (
    <header
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: 24,
        flexWrap: 'wrap',
        padding: '16px 32px',
        borderBottom: '1px solid var(--garis)',
        background: '#fff',
        position: 'sticky',
        top: 0,
        zIndex: 20,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 13 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 9, flex: '0 0 auto' }}>
          <img
            src={logoJateng}
            alt="Lambang Provinsi Jawa Tengah"
            width={29}
            height={32}
            style={{ height: 32, width: 'auto', display: 'block' }}
          />
          <img
            src={logoPolda}
            alt="Lambang Polda Jawa Tengah"
            width={24}
            height={32}
            style={{ height: 32, width: 'auto', display: 'block' }}
          />
          <img
            src={logoJasaraharja}
            alt="Logo Jasa Raharja"
            width={28}
            height={28}
            style={{ height: 28, width: 'auto', display: 'block' }}
          />
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 1, minWidth: 0 }}>
          {/* Judul halaman yang sebenarnya. Ukurannya tetap seperti desain;
              yang berubah hanya jenis elemennya, agar pembaca layar punya
              satu h1 sebagai titik awal. */}
          <h1
            style={{
              margin: 0,
              fontSize: 14.5,
              fontWeight: 600,
              letterSpacing: '-0.01em',
              whiteSpace: 'nowrap',
            }}
          >
            Samsat Kota Salatiga
          </h1>
          <div style={{ fontSize: 11.5, color: 'var(--teks-samar-2)', whiteSpace: 'nowrap' }}>
            Monitoring Penerimaan PKB
          </div>
        </div>
      </div>

      <div
        style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}
        data-no-print
      >
        {adaData ? (
          <div style={{ fontSize: 12.5, color: 'var(--teks-samar-2)', whiteSpace: 'nowrap' }}>
            Data per {waktu(batchTerakhir?.disimpan_pada)}
          </div>
        ) : (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 9,
              padding: '6px 12px',
              border: '1px solid var(--kuning-garis)',
              borderRadius: 999,
              background: 'oklch(0.985 0.02 85)',
            }}
          >
            <span
              style={{
                width: 7,
                height: 7,
                borderRadius: '50%',
                background: 'oklch(0.75 0.13 75)',
                flex: '0 0 auto',
              }}
            />
            <span style={{ fontSize: 12, color: 'oklch(0.45 0.06 75)', whiteSpace: 'nowrap' }}>
              Belum ada berkas diunggah
            </span>
          </div>
        )}

        <button type="button" className="tombol-utama" onClick={onUnggah}>
          <IkonUnggah />
          Unggah Excel
        </button>

        <button
          type="button"
          className="tombol-biasa"
          onClick={onKeluar}
          title={`Keluar dari akun ${pengguna?.username ?? ''}`}
        >
          <IkonKeluar />
          Keluar
        </button>
      </div>
    </header>
  )
}
