# Nadesco Indonesia — export HTML (Claude Design)

Isi paket:
- Halaman utama: Main.dc.html (Beranda), about-us.dc.html (Tentang Kami), product-solution.dc.html (Produk & Solusi), career.dc.html (Karier), contact-us.dc.html (Hubungi Kami), privacy-policy.dc.html (Kebijakan Privasi)
- Produk & Solusi – detail: ps-welding-system-equipment, ps-automation-engineering, ps-it-solution, ps-project-construction, ps-standard-parts-supply (.dc.html)
- index.html: langsung membuka Beranda
- assets/: gambar, ikon animasi, stylesheet situs, video hero
- support.js + vendor/react*.js: runtime yang merender halaman di browser (bukan bagian desain)

Cara membuka: jalankan server lokal di folder ini, misalnya `python3 -m http.server`, lalu buka http://localhost:8000/ . Beberapa browser memblokir script bila file dibuka langsung lewat file://.

Catatan: halaman ini adalah mockup desain (referensi), bukan kode produksi. Font dimuat dari Google Fonts, jadi perlu koneksi internet agar tipografinya tampil sesuai.
