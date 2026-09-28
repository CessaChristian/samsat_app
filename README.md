# Dashboard Monitoring PKB — Samsat Kota Salatiga

Aplikasi internal untuk memantau penerimaan **Pajak Kendaraan Bermotor
(PKB)**, **Opsen PKB**, dan **SWDKLLJ** di Kota Salatiga.

Petugas mengunggah berkas Excel rekapitulasi dari pusat, lalu dashboard
menampilkan jumlah objek dan nilai penerimaan per kecamatan dan per
kelurahan. Data detail dapat diunduh kembali sebagai Excel atau PDF.

> Aplikasi ini memuat **nama dan alamat pemilik kendaraan**. Jangan
> membagikan berkas unggahan, hasil export, maupun isi databasenya ke luar
> instansi.

---

## 1. Yang perlu terpasang

| Perangkat | Versi | Catatan |
|---|---|---|
| Python | 3.11 atau lebih baru | diuji pada 3.14 |
| Node.js | 18 atau lebih baru | diuji pada 25; ikut membawa `npm` |
| PostgreSQL | 16 | diuji pada 16.11 |

Memastikan semuanya ada:

```bash
python3 --version
node --version
psql --version
```

---

## 2. Pemasangan

### 2.1 Ambil kodenya

```bash
git clone https://github.com/CessaChristian/samsat_app.git
cd samsat_app
```

### 2.2 Virtualenv dan dependensi backend

```bash
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r backend/requirements.txt
```

### 2.3 Dependensi frontend

```bash
cd frontend
npm install
cd ..
```

### 2.4 Database

Buat database kosong, lalu jalankan `database.sql`. Berkas itu membuat
seluruh tabel sekaligus mengisi master 4 kecamatan dan 23 kelurahan Kota
Salatiga:

```bash
createdb samsat_app
psql -d samsat_app -f database.sql
```

Memastikan berhasil — harus keluar angka `23`:

```bash
psql -d samsat_app -tAc "SELECT COUNT(*) FROM dim_wilayah"
```

#### Mengetahui alamat databasenya

Langkah berikutnya meminta `DATABASE_URL`. Bentuknya begini:

```
postgresql://PENGGUNA:SANDI@HOST:PORT/NAMA_DATABASE
                     └──────┘
                     boleh dihilangkan bila koneksi tidak minta kata sandi
```

Seluruh bagiannya bisa dilihat dari terminal — tidak perlu pgAdmin, DBeaver,
atau aplikasi sejenis:

```bash
psql -d samsat_app -c "\conninfo"
```

Keluarannya menyebutkan semuanya sekaligus:

```
You are connected to database "samsat_app" as user "cessac"
on host "localhost" (address "::1") at port "5432".
```

Dari keluaran itu alamatnya disusun menjadi:

```
postgresql://cessac@localhost:5432/samsat_app
```

**Perlu kata sandi atau tidak?** Perhatikan saat menjalankan perintah di
atas. Bila `psql` langsung masuk tanpa bertanya apa-apa, koneksinya tidak
memerlukan kata sandi dan bagian `:SANDI` cukup dihilangkan — ini bawaan
PostgreSQL yang dipasang lewat Homebrew di macOS. Bila `psql` meminta
`Password:`, sisipkan kata sandinya:

```
postgresql://cessac:kata-sandinya@localhost:5432/samsat_app
```

Bila kata sandinya memuat karakter `@ : / # ?`, karakter itu harus ditulis
dalam bentuk sandi-persen — misalnya `@` menjadi `%40` — kalau tidak,
alamatnya akan salah dibaca.

**Mengujinya sebelum dipakai.** Alamat yang sudah disusun bisa langsung
dicoba. Yang di dalam tanda kutip itu persis nilai yang nanti diisikan ke
`DATABASE_URL`:

```bash
psql "postgresql://cessac@localhost:5432/samsat_app" -c "SELECT 1"
```

Keluar tabel berisi angka `1` berarti alamatnya benar.

Perintah lain yang berguna:

| Perintah | Gunanya |
|---|---|
| `pg_isready` | memastikan server PostgreSQL hidup |
| `psql -l` | daftar seluruh database beserta pemiliknya |
| `psql -d postgres -tAc "SHOW port"` | porta yang sedang dipakai |
| `whoami` | nama pengguna sistem, yang biasanya juga jadi nama pengguna PostgreSQL |

### 2.5 Berkas konfigurasi

Ada dua berkas `.env` terpisah. Salin contohnya lalu sesuaikan:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

Yang **wajib** diisi di `backend/.env`:

| Variabel | Keterangan |
|---|---|
| `DATABASE_URL` | Alamat database dari langkah 2.4, misal `postgresql://cessac@localhost:5432/samsat_app` |
| `SECRET_KEY` | Kunci penanda tangan cookie sesi. Wajib diganti dengan nilai acak |

Membangkitkan `SECRET_KEY`:

```bash
.venv/bin/python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Sisanya boleh dibiarkan apa adanya. Berkas `.env` **tidak pernah**
di-commit; yang masuk repo hanya `.env.example`.

### 2.6 Akun untuk masuk

Aplikasi tidak menyediakan pendaftaran mandiri. Buat akun lewat skrip —
kata sandi diminta lewat prompt, jadi tidak tertinggal di riwayat terminal:

```bash
cd backend
../.venv/bin/python scripts/buat_akun.py petugas
cd ..
```

Kata sandi minimal 8 karakter dan diminta dua kali.

### 2.7 Bangun tampilannya

```bash
cd frontend
npm run build
cd ..
```

Cukup sekali. Diulang hanya bila kode di `frontend/src` berubah.

---

## 3. Menjalankan

```bash
cd backend
../.venv/bin/python main.py
```

Buka **<http://127.0.0.1:5000>**.

Keluaran yang benar:

```
  Dashboard PKB — Samsat Kota Salatiga
  alamat    http://127.0.0.1:5000
  database  samsat_app
  tampilan  hasil build
  debug     aktif

  Buka http://127.0.0.1:5000 — tampilan dan API dilayani di sini.
```

Satu proses melayani tampilan sekaligus API, jadi tidak ada porta kedua.
Bila barisnya berbunyi `tampilan  BELUM DIBANGUN`, ulangi langkah 2.7.

Pilihan yang tersedia:

```bash
../.venv/bin/python main.py --port 5001     # ganti porta
../.venv/bin/python main.py --tanpa-debug   # matikan muat ulang otomatis
```

### Saat mengubah tampilan

Cara di atas menyajikan hasil build, jadi perubahan kode frontend baru
terlihat setelah `npm run build` diulang. Saat sedang mengerjakan tampilan,
pakai server pengembangan Vite yang memuat ulang sendiri:

```bash
# terminal 1
cd backend && ../.venv/bin/python main.py

# terminal 2
cd frontend && npm run dev
```

Lalu buka **<http://localhost:5173>** — bukan 5000. Backend tetap wajib
hidup: `npm run dev` sendirian hanya menyajikan halaman tanpa ada yang
menjawab `/api`.

---

## 4. Memakai aplikasi

1. Masuk dengan akun dari langkah 2.6.
2. Saat database masih kosong, yang tampil adalah layar **"Belum ada data
   yang ditampilkan"**.
3. Klik **Unggah Excel**, pilih berkas `.xlsx` atau `.xls` dari pusat
   (maksimal 10 MB).
4. Klik **Cek File**. Berkas diperiksa **tanpa menulis apa pun** ke
   database:
   - lolos → panel hijau berisi ringkasan, ditambah kotak kuning bila ada
     penyesuaian otomatis;
   - gagal → panel merah berisi daftar kesalahan beserta nomor barisnya,
     dan tombol Simpan tetap mati sampai berkasnya diperbaiki.
5. Klik **Simpan ke database**. Berkas divalidasi ulang dari nol, lalu
   disimpan dalam satu transaksi. Gagal di tengah berarti tidak ada yang
   tersimpan sama sekali.
6. Dashboard dimuat ulang. Di atasnya ada dua penyaring:
   - **Periode** — mode *Bulan* memakai kisi 12 bulan (klik bulan awal lalu
     bulan akhir); mode *Tanggal* memakai dua kotak tanggal. Ada juga
     pilihan cepat *Semua periode*, *Bulan terakhir*, dan *3 bulan
     terakhir*.
   - **Filter data** — jenis kendaraan, status, kecamatan, kelurahan.

   Pilihan baru berlaku setelah **Terapkan** ditekan.
7. **Export Excel** dan **Export PDF** di bagian bawah mengunduh seluruh
   baris detail yang lolos filter yang sedang berlaku — 21 kolom yang sama
   dengan berkas dari pusat.

Mengunggah berkas yang sama dua kali **tidak menggandakan data**: baris
yang sudah ada diperbarui, dan muncul peringatan bahwa berkas itu pernah
disimpan.

---

## 5. Struktur proyek

```
samsat_app/
├── database.sql             skema + master wilayah, dijalankan sekali
├── backend/
│   ├── main.py              titik jalan: python main.py
│   ├── requirements.txt
│   ├── scripts/buat_akun.py
│   └── app/
│       ├── __init__.py      pabrik aplikasi Flask
│       ├── config.py        dibaca dari backend/.env
│       ├── database.py      koneksi PostgreSQL, tanpa ORM
│       ├── konstanta.py     21 header berkas pusat, master wilayah
│       ├── controllers/     rute HTTP
│       ├── models/          akses tabel, SQL mentah
│       ├── services/        baca Excel, validasi, hitung, export
│       ├── views/           penyusun balasan JSON
│       ├── utils/
│       └── sql/             query panjang sebagai berkas .sql
└── frontend/
    ├── vite.config.js
    ├── index.html
    └── src/
        ├── App.jsx
        ├── api/klien.js     satu-satunya tempat memanggil backend
        ├── components/
        ├── pages/
        └── styles/
```

Backend memakai pembagian **MVC**: `controllers` hanya mengatur permintaan
HTTP, `models` hanya menyentuh database, `services` memuat aturan
perhitungan, dan `views` menyusun bentuk JSON.

---

## 6. Bila ada masalah

**`Modul "flask" tidak ditemukan`.**
Virtualenv belum aktif. Jalankan lewat interpreternya langsung:
`../.venv/bin/python main.py`.

**`Variabel lingkungan berikut belum diisi: DATABASE_URL, SECRET_KEY`.**
`backend/.env` belum dibuat atau belum dilengkapi. Ulangi langkah 2.5.

**`Porta 5000 sudah dipakai proses lain` (khusus macOS).**
Porta 5000 kerap dipakai AirPlay Receiver bawaan sistem. Pilih salah satu:

```bash
../.venv/bin/python main.py --port 5001
```

atau matikan AirPlay Receiver di *System Settings → General → AirDrop &
Handoff*.

**Halaman membalas "Tampilan belum dibangun".**
`npm run build` belum pernah dijalankan. Ulangi langkah 2.7.

**Proxy membalas 403 saat memakai `npm run dev` (khusus macOS).**
`VITE_API_TARGET` harus `http://127.0.0.1:5000`, bukan `localhost`. Di
macOS `localhost` lebih dulu diarahkan ke `::1`, dan di sana porta 5000
dijawab AirPlay.

---

## 7. Catatan teknis

- Satu baris data ditandai pasangan **nomor polisi + tanggal jatuh tempo
  PKB**. Baris lama tidak pernah dihapus, hanya diperbarui.
- Seluruh perhitungan hanya memakai baris yang tanggal jatuh temponya
  **sudah lewat atau sama dengan hari ini**. Jatuh tempo di masa depan
  tersimpan tetapi tidak ikut dihitung.
- Nilai **Opsen PKB tidak pernah dihitung dari PKB**; angkanya diambil apa
  adanya dari kolom di berkas pusat.
- Tabel rincian selalu menampilkan **23 kelurahan**, termasuk yang
  nilainya nol.
- Akses database memakai **psycopg 3 dengan SQL mentah, tanpa ORM**. Nilai
  selalu dikirim sebagai parameter, tidak pernah disambung ke teks SQL.
- Seluruh halaman dan endpoint selain login mewajibkan sesi yang sah.
- Cabang **`lengkap`** berisi versi yang sama ditambah 319 tes otomatis
  beserta perkakas migrasi database.
