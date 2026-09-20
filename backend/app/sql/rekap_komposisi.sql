-- Donut dan bar komposisi objek: jumlah objek per jumlah roda.
SELECT k.jml_roda AS roda, COUNT(*) AS objek
  FROM kewajiban_pkb k
  JOIN dim_wilayah w ON w.id = k.wilayah_id
 WHERE k.tgl_jatuh_tempo_pkb BETWEEN %(dari)s AND %(sampai)s
   AND (%(roda)s::smallint IS NULL OR k.jml_roda = %(roda)s)
   AND (%(lunas)s::boolean  IS NULL OR k.lunas   = %(lunas)s)
   AND (%(kecamatan)s::text IS NULL OR w.kecamatan = %(kecamatan)s)
   AND (%(kelurahan)s::text IS NULL OR w.kelurahan = %(kelurahan)s)
 GROUP BY k.jml_roda;
