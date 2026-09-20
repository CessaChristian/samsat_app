import { angka, persen } from '../format.js'

/**
 * Komposisi objek per jumlah roda, dalam bentuk batang.
 * Roda 2 dan Roda 4 selalu tampil walau salah satunya 0 (bagian 12).
 */
export default function KomposisiObjek({ data }) {
  const total = data.reduce((jumlah, d) => jumlah + d.objek, 0)

  return (
    <div className="kartu" style={{ padding: '20px 22px 22px' }}>
      <h2 className="judul-blok" style={{ marginBottom: 18 }}>
        Komposisi objek
      </h2>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        {data.map((d) => (
          <div key={d.roda} style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            <div
              style={{
                display: 'flex',
                alignItems: 'baseline',
                justifyContent: 'space-between',
                gap: 12,
              }}
            >
              <span style={{ fontSize: 13, color: 'var(--teks-sedang)' }}>Roda {d.roda}</span>
              <span style={{ fontSize: 13, fontWeight: 600 }}>
                {angka(d.objek)}
                {total > 0 && (
                  <span style={{ fontWeight: 400, color: 'var(--teks-samar-2)' }}>
                    {' · '}
                    {persen(Math.round((d.objek / total) * 1000) / 10)}
                  </span>
                )}
              </span>
            </div>
            <div
              style={{
                height: 8,
                borderRadius: 999,
                background: 'var(--jalur-bar)',
                overflow: 'hidden',
              }}
            >
              <div
                style={{
                  height: '100%',
                  borderRadius: 999,
                  background: 'var(--biru-bar-muda)',
                  width: total > 0 ? `${(d.objek / total) * 100}%` : '0%',
                  transition: 'width 220ms ease',
                }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
