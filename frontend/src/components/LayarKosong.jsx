import { IkonMap } from './Ikon.jsx'

/**
 * Keadaan "belum ada data": kartu dan grafik berupa kerangka abu bergaris
 * putus-putus, ditambah ajakan mengunggah.
 *
 * Disalin dari prototipe "Tampilan Awal.dc.html" dengan satu koreksi wajib:
 * langkah 2 di prototipe menyebut "lokasi" sebagai filter. Filter lokasi
 * proses dihapus permanen (bagian 3), jadi kata itu tidak boleh muncul.
 *
 * Acuan: SPESIFIKASI_DASHBOARD_PKB.md bagian 3 (kondisi layar 2).
 */

const LANGKAH = [
  {
    nomor: '1',
    judul: 'Unggah berkas',
    isi: 'Pilih berkas .xlsx atau .xls yang dikirim kantor pusat.',
  },
  {
    nomor: '2',
    judul: 'Pilih periode dan filter',
    isi: 'Tentukan rentang bulan atau tanggal, jenis kendaraan, status, kecamatan, dan kelurahan.',
  },
  {
    nomor: '3',
    judul: 'Unduh laporan',
    isi: 'Export Excel atau PDF mengikuti filter yang sedang ditampilkan.',
  },
]

const KARTU_KOSONG = ['Objek', 'PKB', 'Opsen PKB', 'SWDKLLJ']

const gayaRangkaKartu = {
  border: '1px dashed var(--garis-input)',
  borderRadius: 'var(--radius-besar)',
  padding: '26px 28px 28px',
  display: 'flex',
  flexDirection: 'column',
  gap: 14,
}

export default function LayarKosong({ onUnggah }) {
  return (
    <>
      <section style={{ padding: '22px 32px 0' }}>
        <div
          className="kartu-besar"
          style={{
            padding: '48px 32px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 26,
            textAlign: 'center',
          }}
        >
          <div
            style={{
              width: 52,
              height: 52,
              borderRadius: 14,
              background: 'oklch(0.96 0.02 254)',
              display: 'grid',
              placeItems: 'center',
              color: 'var(--biru)',
            }}
          >
            <IkonMap />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 10, maxWidth: 560 }}>
            <h1 style={{ margin: 0, fontSize: 21, fontWeight: 600, letterSpacing: '-0.02em' }}>
              Belum ada data yang ditampilkan
            </h1>
            <p
              style={{
                margin: 0,
                fontSize: 14,
                lineHeight: 1.65,
                color: 'var(--teks-label)',
                textWrap: 'pretty',
              }}
            >
              Unggah berkas Excel rekapitulasi dari kantor pusat untuk melihat objek kendaraan,
              PKB, Opsen PKB, dan SWDKLLJ per kecamatan dan kelurahan.
            </p>
          </div>

          <button
            type="button"
            className="tombol-utama"
            onClick={onUnggah}
            style={{ padding: '11px 22px', fontSize: 13.5 }}
          >
            Unggah Excel
          </button>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))',
              gap: 14,
              width: '100%',
              maxWidth: 780,
              marginTop: 6,
              textAlign: 'left',
            }}
          >
            {LANGKAH.map((langkah) => (
              <div
                key={langkah.nomor}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 7,
                  padding: '16px 18px',
                  background: 'oklch(0.982 0.006 254)',
                  border: '1px solid var(--garis-halus)',
                  borderRadius: 'var(--radius)',
                }}
              >
                <span style={{ fontSize: 12, fontWeight: 700, color: 'oklch(0.55 0.09 254)' }}>
                  {langkah.nomor}
                </span>
                <span style={{ fontSize: 13, fontWeight: 600 }}>{langkah.judul}</span>
                <span style={{ fontSize: 12.5, lineHeight: 1.55, color: 'var(--teks-label)' }}>
                  {langkah.isi}
                </span>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section style={{ padding: '16px 32px 0' }}>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))',
            gap: 16,
            alignItems: 'start',
          }}
        >
          <div style={{ ...gayaRangkaKartu, gap: 22 }}>
            <div style={{ fontSize: 14, fontWeight: 600, color: 'oklch(0.62 0.012 254)' }}>
              Persentase
            </div>
            <div style={{ display: 'flex', justifyContent: 'center' }}>
              <div
                style={{
                  position: 'relative',
                  width: 'min(210px, 52vw)',
                  aspectRatio: 1,
                  borderRadius: '50%',
                  background: 'oklch(0.955 0.006 254)',
                }}
              >
                <div
                  style={{
                    position: 'absolute',
                    inset: '14.5%',
                    borderRadius: '50%',
                    background: '#fff',
                    display: 'grid',
                    placeItems: 'center',
                    fontSize: 13,
                    color: 'oklch(0.68 0.012 254)',
                  }}
                >
                  —
                </div>
              </div>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              <div className="rangka" style={{ height: 10, borderRadius: 999 }} />
              <div className="rangka" style={{ height: 10, width: '62%', borderRadius: 999 }} />
            </div>
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(272px, 1fr))',
              gap: 16,
            }}
          >
            {KARTU_KOSONG.map((nama) => (
              <div key={nama} style={gayaRangkaKartu}>
                <div style={{ fontSize: 14, fontWeight: 600, color: 'oklch(0.62 0.012 254)' }}>
                  {nama}
                </div>
                <div
                  style={{
                    fontSize: 42,
                    fontWeight: 600,
                    letterSpacing: '-0.035em',
                    lineHeight: 1.05,
                    color: 'oklch(0.86 0.008 254)',
                  }}
                >
                  —
                </div>
                <div className="rangka" style={{ height: 10, width: '58%', borderRadius: 999 }} />
              </div>
            ))}
          </div>
        </div>
      </section>

      <section style={{ padding: '16px 32px 48px' }}>
        <div
          style={{
            border: '1px dashed var(--garis-input)',
            borderRadius: 'var(--radius)',
            padding: '40px 22px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 8,
            textAlign: 'center',
          }}
        >
          <span style={{ fontSize: 13.5, fontWeight: 600, color: 'oklch(0.52 0.012 254)' }}>
            Rincian per wilayah
          </span>
          <span style={{ fontSize: 13, color: 'oklch(0.62 0.012 254)' }}>
            Tabel 4 kecamatan dan 23 kelurahan akan muncul setelah berkas dimuat.
          </span>
        </div>
      </section>
    </>
  )
}
