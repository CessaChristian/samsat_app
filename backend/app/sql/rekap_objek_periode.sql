-- Penyebut angka tengah donut: objek pada periode yang sama TANPA filter
-- roda, status, maupun wilayah (bagian 12).
SELECT COUNT(*) AS objek
  FROM kewajiban_pkb
 WHERE tgl_jatuh_tempo_pkb BETWEEN %(dari)s AND %(sampai)s;
