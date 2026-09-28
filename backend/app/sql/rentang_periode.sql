-- Batas pilihan periode: dari tanggal terawal sampai tanggal terakhir yang
-- ada, tetapi tidak pernah melewati hari ini.
SELECT MIN(tgl_jatuh_tempo_pkb) AS awal,
       MAX(tgl_jatuh_tempo_pkb) AS akhir,
       COUNT(*)                 AS jumlah
  FROM kewajiban_pkb;
