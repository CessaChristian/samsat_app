# Dashboard Monitoring PKB — Samsat Kota Salatiga

Aplikasi web internal untuk memantau penerimaan PKB, Opsen PKB, dan SWDKLLJ
per kecamatan dan kelurahan. Petugas mengunggah berkas Excel harian dari
kantor pusat; aplikasi memvalidasi, menyimpan, lalu menampilkan rekapitulasi
yang bisa disaring dan diunduh.

> **Data berisi nama dan alamat pemilik kendaraan.** Aplikasi tidak boleh
> diakses tanpa login, dan berkas contoh tidak boleh masuk repositori.
> Folder `samples/` serta kedua berkas `.env` sudah diblokir `.gitignore`.

---

## 1. Yang perlu terpasang

| Kebutuhan | Versi | Cara memeriksa |
|---|---|---|
| Python | 3.11 atau lebih baru | `python3 --version` |
| Node.js | 18 atau lebih baru | `node --version` |
| PostgreSQL | 16 | `psql --version` |

---

## 2. Persiapan pertama kali

Cukup dijalankan sekali. Semua perintah dari dalam folder `pkb-dashboard/`.

### 2.1 Virtualenv dan dependensi backend

```bash
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
```

### 2.2 Dependensi frontend

```bash
cd frontend
npm install
cd ..
```

### 2.3 Berkas konfigurasi

Backend dan frontend punya `.env` **masing-masing**. Yang di backend memuat
rahasia dan tidak pernah sampai ke peramban; yang di frontend hanya memuat
alamat.

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

**`backend/.env`**

| Variabel | Keterangan |
|---|---|
| `DATABASE_URL` | Koneksi PostgreSQL, misal `postgresql://pengguna:sandi@localhost:5432/samsat_app` |
| `SECRET_KEY` | Kunci tanda tangan cookie sesi. Wajib diganti |
| `SESSION_COOKIE_SECURE` | `false` saat pengembangan; `true` hanya bila dilayani lewat HTTPS |
| `HOST`, `PORT` | Alamat server pengembangan. Bawaan `127.0.0.1:5000` |
| `DEBUG` | `true` saat pengembangan agar berkas dimuat ulang otomatis |
| `UPLOAD_TMP_DIR` | Folder unggahan sementara. Lintasan relatif dihitung dari `backend/` |
| `APP_TODAY` | **Biarkan kosong.** Hanya diisi saat menguji |
| `TEST_DATABASE_URL` | Database khusus tes, **harus berbeda** dari `DATABASE_URL` |

Membangkitkan `SECRET_KEY`:

```bash
.venv/bin/python -c "import secrets; print(secrets.token_urlsafe(48))"
```

**`frontend/.env`**

| Variabel | Keterangan |
|---|---|
| `VITE_PORT` | Porta Vite. Bawaan `5173` |
| `VITE_API_TARGET` | Alamat backend yang dituju proxy `/api`. Harus cocok dengan `HOST`/`PORT` backend |

### 2.4 Database dan skema

```bash
createdb samsat_app
cd backend
../.venv/bin/python scripts/migrate.py
```

Keluaran yang benar berakhir dengan:

```
2 migrasi terpasang: 001_init.sql, 002_seed_wilayah.sql
dim_wilayah berisi 23 kelurahan.
```

### 2.5 Akun petugas

```bash
cd backend
../.venv/bin/python scripts/buat_akun.py petugas
```

Kata sandi diminta dua kali lewat prompt, tidak lewat argumen, dan disimpan
sebagai hash. Minimal 8 karakter. Tidak ada halaman pendaftaran — akun hanya
dibuat lewat skrip ini.

---

## 3. Menjalankan aplikasi

Butuh **dua terminal** yang berjalan bersamaan.

### Terminal 1 — backend

```bash
cd pkb-dashboard/backend
source ../.venv/bin/activate
python3 main.py
```

Tanpa mengaktifkan virtualenv, jalankan langsung dengan interpreternya:

```bash
../.venv/bin/python main.py
```

Keluaran yang benar:

```
  Dashboard PKB — Samsat Kota Salatiga
  backend   http://127.0.0.1:5000
  database  samsat_app
  debug     aktif
```

Pilihan yang tersedia:

```bash
python3 main.py --port 5001     # timpa porta sekali jalan
python3 main.py --tanpa-debug   # matikan muat ulang otomatis
```

### Terminal 2 — frontend

```bash
cd pkb-dashboard/frontend
npm run dev
```

### Buka aplikasinya

Buka **<http://localhost:5173>** — bukan porta 5000. Porta 5000 hanya
melayani JSON; Vite yang menyajikan tampilan dan meneruskan `/api` ke Flask,
sehingga cookie sesi berjalan satu origin tanpa perlu CORS.

Masuk memakai akun dari langkah 2.5.

---

## 4. Memakai aplikasi

1. Saat database masih kosong, yang tampil adalah layar **"Belum ada data
   yang ditampilkan"**.
2. Klik **Unggah Excel**, pilih berkas `.xlsx` atau `.xls` dari kantor pusat
   (maksimal 10 MB).
3. Klik **Cek File**. Berkas diperiksa **tanpa menulis apa pun** ke database:
   - lolos → panel hijau berisi ringkasan, ditambah kotak kuning bila ada
     penyesuaian otomatis;
   - gagal → panel merah berisi daftar kesalahan beserta nomor barisnya, dan
     tombol Simpan tetap mati sampai berkas diperbaiki.
4. Klik **Simpan ke database**. Berkas divalidasi ulang dari nol, lalu
   disimpan dalam satu transaksi. Gagal di tengah berarti tidak ada yang
   tersimpan sama sekali.
5. Dashboard dimuat ulang. Saring lewat periode, jenis kendaraan, status,
   kecamatan, dan kelurahan. Export mengikuti filter yang sedang berlaku.

Mengunggah berkas yang sama dua kali **tidak menggandakan data** — baris yang
sudah ada diperbarui, dan muncul peringatan bahwa berkas itu pernah disimpan.

---

## 5. Menjalankan pengujian

Tes yang menyentuh database memakai `TEST_DATABASE_URL`, bukan database
aplikasi. Isinya dikosongkan sebelum setiap tes, jadi arahkan ke database
terpisah:

```bash
createdb samsat_app_test
cd backend
../.venv/bin/python -m pytest
```

Suite **menolak berjalan** bila `TEST_DATABASE_URL` sama dengan
`DATABASE_URL`. Bila `TEST_DATABASE_URL` dikosongkan, tes yang butuh database
dilewati dan sisanya tetap jalan.

Sebagian tes membandingkan hasil dengan berkas contoh di
`samples/data_dummy_bersih.xlsx`. Bila berkas itu tidak ada, tes tersebut
dilewati, bukan gagal.

---

## 6. Struktur proyek

```
pkb-dashboard/
├── backend/
│   ├── main.py              server pengembangan: python3 main.py
│   ├── wsgi.py              titik masuk Gunicorn untuk produksi
│   ├── .env                 rahasia backend, tidak di-commit
│   ├── .env.example
│   ├── app/
│   │   ├── __init__.py      create_app()
│   │   ├── config.py        konfigurasi dari backend/.env
│   │   ├── database.py      pool psycopg 3, SQL mentah, tanpa ORM
│   │   ├── konstanta.py     21 header, master 23 kelurahan, kode pesan
│   │   ├── extensions.py    Flask-Login
│   │   ├── models/          akses data: pengguna, kewajiban, batch, wilayah
│   │   ├── controllers/     rute: auth, upload, meta, rekap
│   │   ├── views/           penyusun respons JSON
│   │   ├── services/        pembaca, normalisasi, validator, penyimpan, rekap
│   │   ├── utils/           waktu, migrasi
│   │   └── sql/             query agregasi sebagai berkas .sql
│   ├── migrations/          001_init.sql, 002_seed_wilayah.sql
│   ├── scripts/             migrate.py, buat_akun.py
│   ├── uploads_tmp/         berkas unggahan sementara, tidak di-commit
│   └── tests/
├── frontend/
│   ├── .env                 alamat backend, tidak di-commit
│   ├── .env.example
│   ├── vite.config.js       porta dan proxy dibaca dari frontend/.env
│   └── src/
│       ├── api/klien.js     klien fetch
│       ├── components/      Header, filter, kartu, grafik, tabel, modal
│       ├── pages/           Login, Dashboard
│       ├── format.js        rupiah dan tanggal dd/mm/yyyy
│       └── konstanta.js     21 header
└── samples/                 berkas contoh, tidak di-commit
```

---

## 7. Bila ada masalah

**`Modul "flask" tidak ditemukan` saat `python3 main.py`.**
Virtualenv belum aktif. Jalankan `source ../.venv/bin/activate` lebih dulu,
atau panggil interpreternya langsung: `../.venv/bin/python main.py`.

**`Porta 5000 sudah dipakai proses lain` (khusus macOS).**
Porta 5000 kerap dipakai AirPlay Receiver bawaan sistem. Pilihan:
matikan lewat Pengaturan Sistem → Umum → AirDrop & Handoff, atau pindahkan
backend ke porta lain:

```bash
python3 main.py --port 5001
```

Bila portanya diganti, sesuaikan juga `VITE_API_TARGET` di `frontend/.env`.

**Vite membalas 403 untuk `/api`.**
Penyebabnya sama seperti di atas: `localhost` di macOS lebih dulu diarahkan ke
`::1`, dan di sana porta 5000 dijawab AirPlay. Karena itu `VITE_API_TARGET`
sengaja memakai `127.0.0.1`, bukan `localhost`.

**`Variabel lingkungan berikut belum diisi`.**
`backend/.env` belum dibuat, atau `DATABASE_URL` / `SECRET_KEY` masih kosong.
Ulangi langkah 2.3.

**`migrate.py` gagal karena tabel sudah ada.**
Skema pernah dipasang manual tanpa lewat `migrate.py`, sehingga tabel
`schema_migrations` kosong. Catat migrasi yang sudah terpasang:

```sql
INSERT INTO schema_migrations (nama)
VALUES ('001_init.sql'), ('002_seed_wilayah.sql')
ON CONFLICT (nama) DO NOTHING;
```

**Angka dashboard berbeda dari yang diharapkan.**
Periksa `APP_TODAY` di `backend/.env` — kalau terisi, aplikasi memakai tanggal
itu sebagai "hari ini". Untuk pemakaian normal, kosongkan.

**Baris dengan jatuh tempo di masa depan tidak muncul.**
Memang begitu. Baris dengan `tgl_jatuh_tempo_pkb` setelah hari ini hanya
menandai bahwa plat tersebut sudah membayar, dan tidak ikut dihitung di
dashboard maupun export.

---

## 8. Catatan teknis

- **Tanpa ORM.** Seluruh akses database memakai SQL mentah lewat psycopg 3
  dengan parameter. Query panjang disimpan di `backend/app/sql/`.
- **Opsen PKB selalu diambil dari data**, tidak pernah dihitung sebagai
  persentase dari PKB.
- **Status lunas tidak berasal dari kolom di berkas.** Untuk setiap nomor
  polisi, baris dengan jatuh tempo terbesar berstatus BELUM LUNAS; sisanya
  LUNAS. Dihitung ulang setiap kali berkas disimpan.
- **Tidak ada data yang dihapus.** Berkas baru memperbarui baris yang
  kuncinya sudah ada dan menambah yang belum ada.
- Untuk produksi jangan memakai `main.py`; pakai Gunicorn lewat `wsgi.py`
  dengan timeout 120 detik:

  ```bash
  gunicorn --timeout 120 --chdir backend wsgi:app
  ```
