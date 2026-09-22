// Ikon garis, disalin dari prototipe Claude Design supaya bentuknya sama.

const dasar = {
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 2,
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
}

export function IkonUnggah({ ukuran = 15, ...sisa }) {
  return (
    <svg width={ukuran} height={ukuran} viewBox="0 0 24 24" {...dasar} {...sisa}>
      <path d="M12 16V4" />
      <path d="M7 9l5-5 5 5" />
      <path d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2" />
    </svg>
  )
}

export function IkonMap({ ukuran = 24, ...sisa }) {
  return (
    <svg width={ukuran} height={ukuran} viewBox="0 0 24 24" {...dasar} strokeWidth={1.7} {...sisa}>
      <path d="M4 19V7a2 2 0 012-2h5l2 2h5a2 2 0 012 2v10a2 2 0 01-2 2H6a2 2 0 01-2-2z" />
      <path d="M9 13h6M9 16h4" />
    </svg>
  )
}

export function IkonPanahBawah({ ukuran = 13, ...sisa }) {
  return (
    <svg width={ukuran} height={ukuran} viewBox="0 0 24 24" {...dasar} strokeWidth={2.2} {...sisa}>
      <path d="M6 9l6 6 6-6" />
    </svg>
  )
}

export function IkonKeluar({ ukuran = 14, ...sisa }) {
  return (
    <svg width={ukuran} height={ukuran} viewBox="0 0 24 24" {...dasar} {...sisa}>
      <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4" />
      <path d="M16 17l5-5-5-5" />
      <path d="M21 12H9" />
    </svg>
  )
}

export function IkonKalender({ ukuran = 16, ...sisa }) {
  return (
    <svg width={ukuran} height={ukuran} viewBox="0 0 24 24" {...dasar} strokeWidth={1.8} {...sisa}>
      <rect x="3" y="5" width="18" height="16" rx="2" />
      <path d="M3 10h18M8 3v4M16 3v4" />
    </svg>
  )
}

export function IkonFilter({ ukuran = 16, ...sisa }) {
  return (
    <svg width={ukuran} height={ukuran} viewBox="0 0 24 24" {...dasar} strokeWidth={1.8} {...sisa}>
      <path d="M4 7h16M7 12h10M10 17h4" />
    </svg>
  )
}

export function IkonPanahKiri({ ukuran = 15, ...sisa }) {
  return (
    <svg width={ukuran} height={ukuran} viewBox="0 0 24 24" {...dasar} strokeWidth={2.2} {...sisa}>
      <path d="M15 6l-6 6 6 6" />
    </svg>
  )
}

export function IkonPanahKanan({ ukuran = 15, ...sisa }) {
  return (
    <svg width={ukuran} height={ukuran} viewBox="0 0 24 24" {...dasar} strokeWidth={2.2} {...sisa}>
      <path d="M9 6l6 6-6 6" />
    </svg>
  )
}
