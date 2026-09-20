-- Jumlah baris staging yang kuncinya sudah ada di kewajiban_pkb.
-- Dijalankan SEBELUM upsert, selagi angkanya masih bisa dibedakan.
SELECT COUNT(*) AS jumlah
  FROM staging s
  JOIN kewajiban_pkb k
    ON k.no_polisi = s.no_polisi
   AND k.tgl_jatuh_tempo_pkb = s.tgl_jatuh_tempo_pkb;
