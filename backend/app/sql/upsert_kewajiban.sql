-- Satu baris = satu kewajiban pajak, dikunci (no_polisi, tgl_jatuh_tempo_pkb).
-- Kunci yang sudah ada diperbarui seluruh kolomnya; kunci baru ditambahkan.
-- Tidak ada baris yang dihapus.
INSERT INTO kewajiban_pkb (
    no_polisi, tgl_jatuh_tempo_pkb, wilayah_id, jml_roda,
    pkb_pokok, pkb_denda, pkb_opsen, pkb_denda_opsen, swdkllj, denda_swdkllj,
    nama, alamat, nm_kecamatan_asli, nm_kelurahan_asli, nm_jenis_kend,
    nm_merk_kend, th_buat, warna_kend, warna_tnkb_kend, tgl_jatuh_tempo_stnk,
    pnbp, total, batch_id
)
SELECT s.no_polisi, s.tgl_jatuh_tempo_pkb, s.wilayah_id, s.jml_roda,
       s.pkb_pokok, s.pkb_denda, s.pkb_opsen, s.pkb_denda_opsen,
       s.swdkllj, s.denda_swdkllj,
       s.nama, s.alamat, s.nm_kecamatan_asli, s.nm_kelurahan_asli,
       s.nm_jenis_kend, s.nm_merk_kend, s.th_buat, s.warna_kend,
       s.warna_tnkb_kend, s.tgl_jatuh_tempo_stnk,
       s.pnbp, s.total, %(batch_id)s
  FROM staging s
ON CONFLICT (no_polisi, tgl_jatuh_tempo_pkb) DO UPDATE SET
    wilayah_id           = EXCLUDED.wilayah_id,
    jml_roda             = EXCLUDED.jml_roda,
    pkb_pokok            = EXCLUDED.pkb_pokok,
    pkb_denda            = EXCLUDED.pkb_denda,
    pkb_opsen            = EXCLUDED.pkb_opsen,
    pkb_denda_opsen      = EXCLUDED.pkb_denda_opsen,
    swdkllj              = EXCLUDED.swdkllj,
    denda_swdkllj        = EXCLUDED.denda_swdkllj,
    nama                 = EXCLUDED.nama,
    alamat               = EXCLUDED.alamat,
    nm_kecamatan_asli    = EXCLUDED.nm_kecamatan_asli,
    nm_kelurahan_asli    = EXCLUDED.nm_kelurahan_asli,
    nm_jenis_kend        = EXCLUDED.nm_jenis_kend,
    nm_merk_kend         = EXCLUDED.nm_merk_kend,
    th_buat              = EXCLUDED.th_buat,
    warna_kend           = EXCLUDED.warna_kend,
    warna_tnkb_kend      = EXCLUDED.warna_tnkb_kend,
    tgl_jatuh_tempo_stnk = EXCLUDED.tgl_jatuh_tempo_stnk,
    pnbp                 = EXCLUDED.pnbp,
    total                = EXCLUDED.total,
    terakhir_diperbarui  = now(),
    batch_id             = EXCLUDED.batch_id;
    -- pertama_terlihat sengaja tidak diperbarui
