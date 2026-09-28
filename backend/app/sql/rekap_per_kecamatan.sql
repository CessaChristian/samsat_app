-- Grafik PKB per kecamatan. Keempat kecamatan selalu tampil, termasuk yang
-- bernilai 0, supaya bentuk grafik tidak berubah-ubah.
WITH dasar AS (
    SELECT k.wilayah_id, k.pkb_pokok, k.pkb_denda
      FROM kewajiban_pkb k
      JOIN dim_wilayah w ON w.id = k.wilayah_id
     WHERE k.tgl_jatuh_tempo_pkb BETWEEN %(dari)s AND %(sampai)s
       AND (%(roda)s::smallint IS NULL OR k.jml_roda = %(roda)s)
       AND (%(lunas)s::boolean  IS NULL OR k.lunas   = %(lunas)s)
       AND (%(kecamatan)s::text IS NULL OR w.kecamatan = %(kecamatan)s)
       AND (%(kelurahan)s::text IS NULL OR w.kelurahan = %(kelurahan)s)
)
SELECT w.kecamatan,
       COALESCE(SUM(d.pkb_pokok + d.pkb_denda), 0) AS pkb
  FROM dim_wilayah w
  LEFT JOIN dasar d ON d.wilayah_id = w.id
 GROUP BY w.kecamatan
 ORDER BY pkb DESC, w.kecamatan;
