-- Baris detail untuk export Excel dan PDF.
--
-- Kolom dan namanya mengikuti ke-21 header berkas pusat. Dua di antaranya
-- diambil dari dim_wilayah, yaitu nama kecamatan dan kelurahan yang sudah
-- dibakukan — bukan nm_kecamatan_asli/nm_kelurahan_asli yang mungkin salah
-- ketik di berkas sumber.
--
-- Filternya sama persis dengan filter dashboard, termasuk batas
-- tgl_jatuh_tempo_pkb <= hari ini yang sudah dipotong saat filter disusun.
SELECT k.no_polisi,
       k.nama,
       k.alamat,
       w.kecamatan AS nm_kecamatan,
       w.kelurahan AS nm_kelurahan,
       k.nm_jenis_kend,
       k.nm_merk_kend,
       k.th_buat,
       k.warna_kend,
       k.warna_tnkb_kend,
       k.jml_roda,
       k.tgl_jatuh_tempo_pkb,
       k.tgl_jatuh_tempo_stnk,
       k.pkb_pokok,
       k.pkb_denda,
       k.pkb_opsen,
       k.pkb_denda_opsen,
       k.swdkllj,
       k.denda_swdkllj,
       k.pnbp,
       k.total
  FROM kewajiban_pkb k
  JOIN dim_wilayah w ON w.id = k.wilayah_id
 WHERE k.tgl_jatuh_tempo_pkb BETWEEN %(dari)s AND %(sampai)s
   AND (%(roda)s::smallint IS NULL OR k.jml_roda = %(roda)s)
   AND (%(lunas)s::boolean  IS NULL OR k.lunas   = %(lunas)s)
   AND (%(kecamatan)s::text IS NULL OR w.kecamatan = %(kecamatan)s)
   AND (%(kelurahan)s::text IS NULL OR w.kelurahan = %(kelurahan)s)
 ORDER BY w.kecamatan, w.kelurahan, k.no_polisi, k.tgl_jatuh_tempo_pkb;
