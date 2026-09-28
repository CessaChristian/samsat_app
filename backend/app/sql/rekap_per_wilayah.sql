-- Tabel rincian: satu baris per kelurahan, kelurahan tanpa data bernilai 0.
-- LEFT JOIN dari dim_wilayah supaya 23 kelurahan selalu tampil; bila filter
-- wilayah aktif, kelurahan di luar filter memang tidak ditampilkan.
WITH dasar AS (
    SELECT k.id, k.wilayah_id,
           k.pkb_pokok, k.pkb_denda, k.pkb_opsen, k.pkb_denda_opsen,
           k.swdkllj, k.denda_swdkllj
      FROM kewajiban_pkb k
      JOIN dim_wilayah w ON w.id = k.wilayah_id
     WHERE k.tgl_jatuh_tempo_pkb BETWEEN %(dari)s AND %(sampai)s
       AND (%(roda)s::smallint IS NULL OR k.jml_roda = %(roda)s)
       AND (%(lunas)s::boolean  IS NULL OR k.lunas   = %(lunas)s)
       AND (%(kecamatan)s::text IS NULL OR w.kecamatan = %(kecamatan)s)
       AND (%(kelurahan)s::text IS NULL OR w.kelurahan = %(kelurahan)s)
)
SELECT w.kecamatan,
       w.kelurahan,
       COUNT(d.id)                                       AS objek,
       COALESCE(SUM(d.pkb_pokok + d.pkb_denda), 0)       AS pkb,
       COALESCE(SUM(d.pkb_opsen + d.pkb_denda_opsen), 0) AS opsen_pkb,
       COALESCE(SUM(d.swdkllj + d.denda_swdkllj), 0)     AS swdkllj
  FROM dim_wilayah w
  LEFT JOIN dasar d ON d.wilayah_id = w.id
 WHERE (%(kecamatan)s::text IS NULL OR w.kecamatan = %(kecamatan)s)
   AND (%(kelurahan)s::text IS NULL OR w.kelurahan = %(kelurahan)s)
 GROUP BY w.kecamatan, w.kelurahan
 ORDER BY pkb DESC, w.kecamatan, w.kelurahan;
