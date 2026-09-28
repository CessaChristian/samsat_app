import { angka, persen } from '../format.js'

/**
 * Tabel rincian per kelurahan.
 *
 * Backend selalu mengirim 23 kelurahan (LEFT JOIN dari dim_wilayah), kecuali
 * bila filter wilayah aktif — kelurahan di luar filter memang tidak
 * ditampilkan. Kelurahan tanpa data bernilai 0, bukan hilang dari tabel.
 *
 */

const gayaTh = {
  padding: '11px 12px',
  fontSize: 12,
  fontWeight: 600,
  color: 'var(--teks-samar)',
  borderBottom: '1px solid var(--garis-halus)',
  whiteSpace: 'nowrap',
}

const gayaThKiri = { ...gayaTh, textAlign: 'left', paddingLeft: 22 }
const gayaThKanan = { ...gayaTh, textAlign: 'right' }
const gayaThKananAkhir = { ...gayaThKanan, paddingRight: 22 }

const gayaTd = { padding: '11px 12px', textAlign: 'right' }

export default function TabelWilayah({ baris, total }) {
  const adaIsi = baris.some((b) => b.objek > 0)

  return (
    <section style={{ padding: '14px 32px 48px' }}>
      <div className="kartu" style={{ overflow: 'hidden' }}>
        <div
          style={{
            display: 'flex',
            alignItems: 'baseline',
            justifyContent: 'space-between',
            gap: 16,
            padding: '17px 22px',
            borderBottom: '1px solid var(--garis-halus)',
          }}
        >
          <h2 className="judul-blok">Rincian per wilayah</h2>
          <span className="keterangan">{baris.length} baris</span>
        </div>

        {adaIsi ? (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr>
                  <th style={gayaThKiri}>Kecamatan</th>
                  <th style={{ ...gayaTh, textAlign: 'left' }}>Kelurahan</th>
                  <th style={gayaThKanan}>Objek</th>
                  <th style={gayaThKanan}>%</th>
                  <th style={gayaThKanan}>PKB</th>
                  <th style={gayaThKanan}>Opsen PKB</th>
                  <th style={gayaThKananAkhir}>SWDKLLJ</th>
                </tr>
              </thead>
              <tbody>
                {baris.map((b) => (
                  <tr
                    key={`${b.kecamatan}-${b.kelurahan}`}
                    style={{ borderBottom: '1px solid var(--garis-tipis)' }}
                  >
                    <td style={{ padding: '11px 22px', color: 'var(--teks-label)' }}>
                      {b.kecamatan}
                    </td>
                    <td style={{ padding: '11px 12px', fontWeight: 500 }}>{b.kelurahan}</td>
                    <td style={gayaTd}>{angka(b.objek)}</td>
                    <td style={{ ...gayaTd, color: 'var(--biru)' }}>{persen(b.persen)}</td>
                    <td style={gayaTd}>{angka(b.pkb)}</td>
                    <td style={gayaTd}>{angka(b.opsen_pkb)}</td>
                    <td style={{ ...gayaTd, paddingRight: 22 }}>{angka(b.swdkllj)}</td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr style={{ borderTop: '1px solid var(--garis)' }}>
                  <td
                    colSpan={2}
                    style={{ padding: '13px 22px', fontWeight: 600, whiteSpace: 'nowrap' }}
                  >
                    Total sesuai filter
                  </td>
                  <td style={{ ...gayaTd, fontWeight: 600 }}>{angka(total.objek)}</td>
                  <td style={{ ...gayaTd, fontWeight: 600, color: 'var(--biru)' }}>
                    {persen(total.persen)}
                  </td>
                  <td style={{ ...gayaTd, fontWeight: 600 }}>{angka(total.pkb)}</td>
                  <td style={{ ...gayaTd, fontWeight: 600 }}>{angka(total.opsen_pkb)}</td>
                  <td style={{ ...gayaTd, fontWeight: 600, paddingRight: 22 }}>
                    {angka(total.swdkllj)}
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
        ) : (
          <div
            style={{
              padding: '44px 22px',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 6,
              textAlign: 'center',
            }}
          >
            <span style={{ fontSize: 13.5, fontWeight: 600, color: 'oklch(0.52 0.012 254)' }}>
              Tidak ada data pada kombinasi filter ini
            </span>
            <span style={{ fontSize: 13, color: 'oklch(0.62 0.012 254)' }}>
              Longgarkan periode atau filter wilayah untuk melihat baris.
            </span>
          </div>
        )}
      </div>
    </section>
  )
}
