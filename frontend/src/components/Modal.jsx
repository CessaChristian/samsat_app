import { useEffect, useRef } from 'react'

/**
 * Kerangka modal: tirai gelap, kotak putih, kepala, isi, dan kaki.
 *
 * Dipakai modal Periode dan modal Filter. ModalUnggah sengaja tidak ikut
 * dipindahkan ke sini karena alurnya punya keadaan "sibuk" yang mengunci
 * tombol tutup; menyatukannya berisiko mengubah perilaku yang sudah teruji.
 *
 * Tutup lewat: tombol ×, klik tirai, atau tombol Escape.
 */
export default function Modal({ judul, alatKepala, lebar, kaki, onTutup, children }) {
  const kotakRef = useRef(null)

  useEffect(() => {
    function tekan(peristiwa) {
      if (peristiwa.key === 'Escape') onTutup()
    }
    document.addEventListener('keydown', tekan)
    return () => document.removeEventListener('keydown', tekan)
  }, [onTutup])

  // Fokus dipindahkan ke dalam modal supaya pembaca layar dan tombol Tab
  // tidak tertinggal di halaman yang ada di belakang tirai.
  useEffect(() => {
    kotakRef.current?.focus()
  }, [])

  return (
    <div
      data-no-print
      role="dialog"
      aria-modal="true"
      aria-label={judul}
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onTutup()
      }}
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 50,
        background: 'var(--tirai)',
        display: 'grid',
        placeItems: 'center',
        padding: 24,
      }}
    >
      <div
        ref={kotakRef}
        tabIndex={-1}
        style={{
          width: `min(${lebar || 640}px, 100%)`,
          maxHeight: '88vh',
          display: 'flex',
          flexDirection: 'column',
          background: '#fff',
          border: '1px solid var(--garis)',
          borderRadius: 'var(--radius-besar)',
          boxShadow: '0 18px 48px oklch(0.3 0.03 254 / 0.18)',
          outline: 'none',
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 14,
            padding: '16px 22px',
            borderBottom: '1px solid var(--garis-halus-2)',
          }}
        >
          <span style={{ fontSize: 15.5, fontWeight: 600, letterSpacing: '-0.01em' }}>
            {judul}
          </span>

          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            {alatKepala}
            <button
              type="button"
              onClick={onTutup}
              title="Tutup"
              aria-label="Tutup"
              style={{
                width: 30,
                height: 30,
                border: '1px solid var(--garis-tombol)',
                borderRadius: 'var(--radius-kecil)',
                background: '#fff',
                fontSize: 15,
                lineHeight: 1,
                color: 'var(--teks-label)',
                cursor: 'pointer',
              }}
            >
              ×
            </button>
          </div>
        </div>

        <div style={{ flex: '1 1 auto', minHeight: 0, overflow: 'auto' }}>{children}</div>

        {kaki && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: 14,
              flexWrap: 'wrap',
              padding: '15px 22px',
              borderTop: '1px solid var(--garis-halus-2)',
              background: 'oklch(0.985 0.004 254)',
              borderRadius: '0 0 var(--radius-besar) var(--radius-besar)',
            }}
          >
            {kaki}
          </div>
        )}
      </div>
    </div>
  )
}
