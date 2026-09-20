import { angka, persen, rupiah, rupiahRingkas } from '../format.js'

/**
 * Baris kartu utama: donut persentase di kiri, empat kartu angka di kanan.
 *
 * Donut dibuat dengan conic-gradient persis seperti prototipe — tidak memakai
 * pustaka grafik, karena bentuk di desain memang cincin polos dengan angka di
 * tengah.
 *
 * Angka tengah donut = objek hasil filter dibagi objek pada periode yang sama
 * tanpa filter roda/status/wilayah (bagian 12).
 */

const WARNA_RODA = {
  2: 'oklch(0.62 0.1 254)',
  4: 'oklch(0.46 0.14 254)',
}

const gayaKartu = {
  border: '1px solid var(--garis)',
  borderRadius: 'var(--radius-besar)',
  padding: '26px 28px 28px',
  display: 'flex',
  flexDirection: 'column',
  gap: 14,
  background: '#fff',
}

const gayaLabel = { fontSize: 14, fontWeight: 600, color: 'var(--teks-label)' }

const gayaAngkaBesar = {
  fontSize: 42,
  fontWeight: 600,
  letterSpacing: '-0.035em',
  lineHeight: 1.05,
  whiteSpace: 'nowrap',
}

const gayaSubteks = { fontSize: 13.5, color: 'var(--teks-samar-2)' }

/** Susun conic-gradient dari komposisi roda. */
function gradienDonut(komposisi) {
  const total = komposisi.reduce((jumlah, k) => jumlah + k.objek, 0)
  if (!total) return 'oklch(0.955 0.006 254)'

  let mulai = 0
  const potongan = komposisi.map((k) => {
    const akhir = mulai + (k.objek / total) * 100
    const teks = `${WARNA_RODA[k.roda]} ${mulai.toFixed(3)}% ${akhir.toFixed(3)}%`
    mulai = akhir
    return teks
  })
  return `conic-gradient(${potongan.join(', ')})`
}

export default function KartuKpi({ kpi, persentase, komposisi }) {
  const total = komposisi.reduce((jumlah, k) => jumlah + k.objek, 0)

  return (
    <section style={{ padding: '22px 32px 0' }}>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))',
          gap: 16,
          alignItems: 'start',
        }}
      >
        <div style={{ ...gayaKartu, gap: 22 }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'baseline',
              justifyContent: 'space-between',
              gap: 12,
            }}
          >
            <div style={gayaLabel}>Persentase</div>
            <div style={{ fontSize: 13.5, color: 'var(--teks-samar-2)' }}>
              dari seluruh objek terdata
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'center' }}>
            <div
              style={{
                position: 'relative',
                width: 'min(252px, 58vw)',
                aspectRatio: 1,
                borderRadius: '50%',
                background: gradienDonut(komposisi),
              }}
            >
              <div
                style={{
                  position: 'absolute',
                  inset: '14.5%',
                  borderRadius: '50%',
                  background: '#fff',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: 4,
                }}
              >
                <div
                  style={{
                    fontSize: 'min(38px, 9vw)',
                    fontWeight: 600,
                    letterSpacing: '-0.035em',
                    lineHeight: 1,
                    whiteSpace: 'nowrap',
                    color: 'var(--biru)',
                  }}
                >
                  {persen(persentase.persen)}
                </div>
                <div style={{ fontSize: 13, color: 'var(--teks-samar-2)' }}>
                  {angka(persentase.objek_filter)} unit
                </div>
              </div>
            </div>
          </div>

          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: 9,
              fontSize: 13,
              color: 'var(--teks-redup)',
            }}
          >
            {komposisi.map((k) => (
              <div
                key={k.roda}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: 12,
                }}
              >
                <span style={{ display: 'flex', alignItems: 'center', gap: 9 }}>
                  <span
                    style={{
                      width: 9,
                      height: 9,
                      borderRadius: 3,
                      background: WARNA_RODA[k.roda],
                      flex: '0 0 auto',
                    }}
                  />
                  Roda {k.roda}
                </span>
                <span
                  style={{ fontWeight: 500, color: 'var(--teks-sedang)', whiteSpace: 'nowrap' }}
                >
                  {angka(k.objek)} unit
                  {total > 0 && ` · ${persen(Math.round((k.objek / total) * 1000) / 10)}`}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(272px, 1fr))',
            gap: 16,
          }}
        >
          <div style={gayaKartu}>
            <div style={gayaLabel}>Objek</div>
            <div style={gayaAngkaBesar}>{angka(kpi.objek)}</div>
            <div style={gayaSubteks}>
              unit · dari {angka(persentase.objek_periode)} unit terdata
            </div>
          </div>

          <div style={gayaKartu}>
            <div style={gayaLabel}>PKB</div>
            <div style={gayaAngkaBesar}>{rupiahRingkas(kpi.pkb)}</div>
            <div style={gayaSubteks}>{rupiah(kpi.pkb)}</div>
          </div>

          <div style={gayaKartu}>
            <div style={gayaLabel}>Opsen PKB</div>
            <div style={gayaAngkaBesar}>{rupiahRingkas(kpi.opsen_pkb)}</div>
            <div style={gayaSubteks}>{rupiah(kpi.opsen_pkb)}</div>
          </div>

          <div style={gayaKartu}>
            <div style={gayaLabel}>SWDKLLJ</div>
            <div style={gayaAngkaBesar}>{rupiahRingkas(kpi.swdkllj)}</div>
            <div style={gayaSubteks}>{rupiah(kpi.swdkllj)}</div>
          </div>
        </div>
      </div>
    </section>
  )
}
