-- Tabel sementara penampung satu berkas unggahan.
-- Sengaja didefinisikan eksplisit (bukan LIKE kewajiban_pkb) supaya kolom
-- id, lunas, pertama_terlihat, dan batch_id tidak ikut: ketiganya diisi oleh
-- INSERT ... SELECT, bukan oleh COPY.
CREATE TEMP TABLE staging (
    no_polisi            TEXT          NOT NULL,
    tgl_jatuh_tempo_pkb  DATE          NOT NULL,
    wilayah_id           INT           NOT NULL,
    jml_roda             SMALLINT      NOT NULL,
    pkb_pokok            NUMERIC(18,2) NOT NULL,
    pkb_denda            NUMERIC(18,2) NOT NULL,
    pkb_opsen            NUMERIC(18,2) NOT NULL,
    pkb_denda_opsen      NUMERIC(18,2) NOT NULL,
    swdkllj              NUMERIC(18,2) NOT NULL,
    denda_swdkllj        NUMERIC(18,2) NOT NULL,
    nama                 TEXT,
    alamat               TEXT,
    nm_kecamatan_asli    TEXT,
    nm_kelurahan_asli    TEXT,
    nm_jenis_kend        TEXT,
    nm_merk_kend         TEXT,
    th_buat              TEXT,
    warna_kend           TEXT,
    warna_tnkb_kend      TEXT,
    tgl_jatuh_tempo_stnk TEXT,
    pnbp                 NUMERIC(18,2) NOT NULL,
    total                NUMERIC(18,2)
) ON COMMIT DROP;
