-- 002_seed_wilayah.sql — master 4 kecamatan dan 23 kelurahan Kota Salatiga.
-- Acuan: SPESIFIKASI_DASHBOARD_PKB.md bagian 5.
--
-- Jebakan yang sengaja dicatat di sini:
--   SIDOREJO KIDUL berada di Kecamatan TINGKIR, bukan SIDOREJO.
--   SALATIGA adalah nama kelurahan di Kecamatan SIDOREJO.

INSERT INTO dim_wilayah (kecamatan, kelurahan) VALUES
    ('ARGOMULYO', 'CEBONGAN'),
    ('ARGOMULYO', 'KUMPULREJO'),
    ('ARGOMULYO', 'LEDOK'),
    ('ARGOMULYO', 'NOBOREJO'),
    ('ARGOMULYO', 'RANDUACIR'),
    ('ARGOMULYO', 'TEGALREJO'),

    ('SIDOMUKTI', 'DUKUH'),
    ('SIDOMUKTI', 'KALICACING'),
    ('SIDOMUKTI', 'KECANDRAN'),
    ('SIDOMUKTI', 'MANGUNSARI'),

    ('SIDOREJO', 'BLOTONGAN'),
    ('SIDOREJO', 'BUGEL'),
    ('SIDOREJO', 'KAUMAN KIDUL'),
    ('SIDOREJO', 'PULUTAN'),
    ('SIDOREJO', 'SALATIGA'),
    ('SIDOREJO', 'SIDOREJO LOR'),

    ('TINGKIR', 'GENDONGAN'),
    ('TINGKIR', 'KALIBENING'),
    ('TINGKIR', 'KUTOWINANGUN KIDUL'),
    ('TINGKIR', 'KUTOWINANGUN LOR'),
    ('TINGKIR', 'SIDOREJO KIDUL'),
    ('TINGKIR', 'TINGKIR LOR'),
    ('TINGKIR', 'TINGKIR TENGAH');
