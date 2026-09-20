import { angka, rupiahRingkas } from '../format.js'

/**
 * PKB per kecamatan sebagai baris batang mendatar.
 *
 * Prototipe menggambarnya dengan div biasa, bukan pustaka grafik, sehingga
 * bentuknya ditiru apa adanya. Keempat kecamatan selalu tampil walau
 * nilainya 0 (bagian 12), dan backend sudah mengurutkannya menurun.
 */
export default function GrafikKecamatan({ data }) {
  const tertinggi = data.reduce((maks, d) => Math.max(maks, d.pkb), 0)

  return (
    <div className="kartu" style={{ padding: '20px 22px 22px' }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'baseline',
          justifyContent: 'space-between',
          gap: 16,
          marginBottom: 18,
        }}
      >
        <h2 className="judul-blok">PKB per kecamatan</h2>
        <span className="keterangan">nilai PKB</span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {data.map((d) => (
          <div
            key={d.kecamatan}
            style={{
              display: 'grid',
              gridTemplateColumns: '148px minmax(0, 1fr) 104px',
              gap: 14,
              alignItems: 'center',
            }}
          >
            <div
              style={{
                fontSize: 13,
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                color: 'var(--teks-sedang)',
              }}
              title={d.kecamatan}
            >
              {d.kecamatan}
            </div>
            <div
              style={{
                height: 10,
                borderRadius: 999,
                background: 'var(--jalur-bar)',
                overflow: 'hidden',
              }}
            >
              <div
                style={{
                  height: '100%',
                  borderRadius: 999,
                  background: 'var(--biru-bar)',
                  width: tertinggi > 0 ? `${(d.pkb / tertinggi) * 100}%` : '0%',
                  transition: 'width 220ms ease',
                }}
              />
            </div>
            <div
              style={{ fontSize: 12.5, textAlign: 'right', color: 'var(--teks-lembut)' }}
              title={`${angka(d.pkb)} rupiah`}
            >
              {rupiahRingkas(d.pkb)}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
