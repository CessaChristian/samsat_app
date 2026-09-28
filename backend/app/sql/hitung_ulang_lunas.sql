-- Untuk setiap nomor polisi, baris dengan jatuh tempo TERBESAR berstatus
-- BELUM LUNAS; sisanya LUNAS. Hanya plat yang tersentuh berkas
-- ini yang dihitung ulang.
UPDATE kewajiban_pkb k
   SET lunas = (k.tgl_jatuh_tempo_pkb <> m.maks)
  FROM (SELECT no_polisi, MAX(tgl_jatuh_tempo_pkb) AS maks
          FROM kewajiban_pkb
         WHERE no_polisi IN (SELECT DISTINCT no_polisi FROM staging)
         GROUP BY no_polisi) m
 WHERE k.no_polisi = m.no_polisi
   AND k.lunas IS DISTINCT FROM (k.tgl_jatuh_tempo_pkb <> m.maks);
