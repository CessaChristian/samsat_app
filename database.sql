-- database.sql — skema dan data master Dashboard Monitoring PKB
-- Samsat Kota Salatiga.
--
-- Jalankan sekali setelah membuat database yang kosong:
--
--     createdb samsat_app
--     psql -d samsat_app -f database.sql
--
-- Berkas ini TIDAK membuat akun login. Buat akun dengan:
--
--     cd backend && python3 scripts/buat_akun.py <username>

CREATE TABLE dim_wilayah (
    id         SERIAL PRIMARY KEY,
    kecamatan  TEXT NOT NULL,
    kelurahan  TEXT NOT NULL UNIQUE,
    UNIQUE (kecamatan, kelurahan)
);

CREATE TABLE ingest_batch (
    id               BIGSERIAL PRIMARY KEY,
    nama_file        TEXT        NOT NULL,
    hash_file        CHAR(64)    NOT NULL,          -- sengaja TIDAK unique
    ukuran_byte      BIGINT      NOT NULL,
    disimpan_pada    TIMESTAMPTZ NOT NULL DEFAULT now(),
    jumlah_baris     INT         NOT NULL,
    baris_baru       INT         NOT NULL,
    baris_diperbarui INT         NOT NULL,
    peringatan       JSONB       NOT NULL DEFAULT '[]'::jsonb
);
CREATE INDEX idx_batch_hash ON ingest_batch (hash_file);

CREATE TABLE kewajiban_pkb (
    id                    BIGSERIAL PRIMARY KEY,

    -- kunci
    no_polisi             TEXT     NOT NULL,
    tgl_jatuh_tempo_pkb   DATE     NOT NULL,

    -- dipakai dashboard
    wilayah_id            INT      NOT NULL REFERENCES dim_wilayah (id),
    jml_roda              SMALLINT NOT NULL CHECK (jml_roda IN (2, 4)),
    pkb_pokok             NUMERIC(18,2) NOT NULL CHECK (pkb_pokok >= 0),
    pkb_denda             NUMERIC(18,2) NOT NULL DEFAULT 0 CHECK (pkb_denda >= 0),
    pkb_opsen             NUMERIC(18,2) NOT NULL CHECK (pkb_opsen >= 0),
    pkb_denda_opsen       NUMERIC(18,2) NOT NULL DEFAULT 0 CHECK (pkb_denda_opsen >= 0),
    swdkllj               NUMERIC(18,2) NOT NULL CHECK (swdkllj >= 0),
    denda_swdkllj         NUMERIC(18,2) NOT NULL DEFAULT 0 CHECK (denda_swdkllj >= 0),
    lunas                 BOOLEAN  NOT NULL DEFAULT FALSE,

    -- hanya untuk export, disimpan apa adanya
    nama                  TEXT,
    alamat                TEXT,
    nm_kecamatan_asli     TEXT,
    nm_kelurahan_asli     TEXT,
    nm_jenis_kend         TEXT,
    nm_merk_kend          TEXT,
    th_buat               TEXT,
    warna_kend            TEXT,
    warna_tnkb_kend       TEXT,
    tgl_jatuh_tempo_stnk  TEXT,
    pnbp                  NUMERIC(18,2) NOT NULL DEFAULT 0,
    total                 NUMERIC(18,2),

    -- jejak
    pertama_terlihat      TIMESTAMPTZ NOT NULL DEFAULT now(),
    terakhir_diperbarui   TIMESTAMPTZ NOT NULL DEFAULT now(),
    batch_id              BIGINT NOT NULL REFERENCES ingest_batch (id),

    UNIQUE (no_polisi, tgl_jatuh_tempo_pkb)
);
CREATE INDEX idx_kpkb_jt          ON kewajiban_pkb (tgl_jatuh_tempo_pkb);
CREATE INDEX idx_kpkb_wilayah_jt  ON kewajiban_pkb (wilayah_id, tgl_jatuh_tempo_pkb);
CREATE INDEX idx_kpkb_plat        ON kewajiban_pkb (no_polisi);

CREATE TABLE pengguna (
    id             SERIAL PRIMARY KEY,
    username       TEXT NOT NULL UNIQUE,
    password_hash  TEXT NOT NULL,
    dibuat_pada    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Master 4 kecamatan dan 23 kelurahan Kota Salatiga.
--
-- Dua hal yang mudah keliru dan sengaja dicatat di sini:
--   SIDOREJO KIDUL berada di Kecamatan TINGKIR, bukan SIDOREJO.
--   SALATIGA adalah nama kelurahan di Kecamatan SIDOREJO.

INSERT INTO dim_wilayah (kecamatan, kelurahan) VALUES
    ('ARGOMULYO', 'CEBONGAN'),
    ('ARGOMULYO', 'KUMPULREJO'),
    ('ARGOMULYO', 'LEDOK'),
    ('ARGOMULYO', 'NOBOREJO'),
    ('ARGOMULYO', 'RANDUACIR'),
    ('ARGOMULYO', 'TEGALREJO'),

    ('SIDOMUKTI', 'DUKUH'),
    ('SIDOMUKTI', 'KALICACING'),
    ('SIDOMUKTI', 'KECANDRAN'),
    ('SIDOMUKTI', 'MANGUNSARI'),

    ('SIDOREJO', 'BLOTONGAN'),
    ('SIDOREJO', 'BUGEL'),
    ('SIDOREJO', 'KAUMAN KIDUL'),
    ('SIDOREJO', 'PULUTAN'),
    ('SIDOREJO', 'SALATIGA'),
    ('SIDOREJO', 'SIDOREJO LOR'),

    ('TINGKIR', 'GENDONGAN'),
    ('TINGKIR', 'KALIBENING'),
    ('TINGKIR', 'KUTOWINANGUN KIDUL'),
    ('TINGKIR', 'KUTOWINANGUN LOR'),
    ('TINGKIR', 'SIDOREJO KIDUL'),
    ('TINGKIR', 'TINGKIR LOR'),
    ('TINGKIR', 'TINGKIR TENGAH');
