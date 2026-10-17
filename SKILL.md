---
name: slideready
description: Bir PowerPoint sunumunun (PPTX) her slaytını, tasarımını ve yerleşimini bozmadan hareketli videoya çevirir ve videoları aynı sunumun içine geri gömer. Sayılar sayaçla, grafikler seri seri, tablolar satır satır açılır. Kullanıcı "PPTX'i işle", "sunumu canlandır", "slaytları videoya çevir", "motion graphic yap" ya da "SlideReady" dediğinde kullan.
---

# SlideReady

Kullanıcının sunumunu **yeniden tasarlamadan** canlandırırsın. Her slaytın kendi şekilleri katman katman açılır,
videonun son karesi orijinal slaytla aynı olmak üzere kurulur. Bu bir hedeftir, kanıt değildir: son kare LibreOffice
render'ından gelir ve gerçek bir referansla karşılaştırılmadan "aynı" diye raporlanmaz (aşağıda 5). Çıktı yine bir PPTX'tir: her slaytta kendi videosu, otomatik
başlar, **döngü yoktur**.

Bütün ağır iş `bin/slideready` aracındadır (Windows'ta `bin\slideready.cmd`). Yollar bu SKILL.md'nin
bulunduğu klasöre göredir; skill başka bir projeden çağrıldıysa aracı tam yoluyla çalıştır. Senin işin aşamaları sırayla
yürütmek, karar gereken yerde karar vermek ve kullanıcıyla kısa, net konuşmaktır. **Koordinat üretme, slaytı
yeniden çizme, HTML yazma.** Yerleşim her zaman dosyadan gelir; senin elindeki tek ayar kolu `plan.json`'dur.

## Ekip ve sıra

Aşağıdaki roller tek akışın aşamalarıdır. Her birini sırayla sen üstlenirsin; ayrı bir ajan açman gerekmez.
Yalnızca **Kontrolcü** için, ortam destekliyorsa `slideready-reviewer` alt ajanını kullanabilirsin.

| # | Rol | Ne zaman | Komut / iş |
|---|---|---|---|
| 0 | **Kurulumcu** | Kullanıcı "kur", "repoyu anla" dediğinde ya da ilk kullanımda | `bin/slideready doctor`; eksik varsa `bash scripts/setup.sh` (Windows: `scripts\setup.ps1`), sonra tekrar `doctor` |
| 1 | **Tanımlayıcı** | PPTX geldiğinde | `bin/slideready analyze SUNUM.pptx` |
| 2 | **Fırsat analisti** | Analizden hemen sonra | Tabloyu oku, `plan.json`'u gerekirse düzenle (aşağıda) |
| 3–4 | **Animatör + Önizlemeci** | Plan hazır olunca | `bin/slideready preview SUNUM.pptx` (en zengin 1–2 slayt, düşük kalite) |
| 5 | **Kontrolcü** | Önizleme çıkınca | `SUNUM.slideready/preview/NNN-sheet.png` kontak sayfalarına bak (aşağıdaki liste) |
| 6 | **Çıktıcı** | Kullanıcı onay verince | `bin/slideready export SUNUM.pptx` → `SUNUM-SlideReady.pptx` |

Kullanıcının gözünden akış üç adımdır: **kur → PPTX'i ver ve önizlemeyi gör → çıktıyı al.** Ara adımları
anlatma, sonucu göster.

## 0. Kurulum

- `bin/slideready doctor` her satırı ✓/✗ ile verir ve eksik için kurulum komutunu yazar.
- `scripts/setup.sh` sistem paketlerini (LibreOffice, ffmpeg, Node), Python paketlerini ve Playwright Chromium'u
  kurar. `sudo` isteyebilir; izin gerekiyorsa kullanıcıya hangi komutu çalıştıracağını tek satırla söyle.
- Kurulum bitince kullanıcıya tek cümle: "Hazır, PPTX'ini gönderebilirsin."

## 1–2. Analiz ve plan

`analyze` her slayt için şekil, grafik, tablo ve sayı sayısını, bir "canlandırma puanını" ve notları basar;
`SUNUM.slideready/plan.json` dosyasını yazar. Plan, slayt başına şu alanlardan oluşur:

```json
{"no": 3, "animate": true, "tempo": 1.0, "hold": 2.0, "static": [], "note": ""}
```

- `animate`: `false` ise slayt sabit kalır, video eklenmez. Kapak, ajanda, kaynakça, hukuki metin, tamamen
  fotoğraftan oluşan ya da yer tutucu metin içeren slaytlar için kullan.
- `tempo`: 1.0 normal; 0.8 daha sakin, 1.2 daha hızlı. Kullanıcı "yavaş/hızlı" derse bunu değiştir.
- `hold`: son hareketten sonraki durağan okuma payı (sn). Varsayılan metin miktarına göre 2–5 sn arasıdır;
  2'nin altına indirme.
- `static`: hareket etmemesi gereken şekil adları (ör. logo, dipnot). Adlar `analysis.json`'dadır. `Picture 3`,
  `Resim 5` gibi otomatik adlardan işlev çıkarma: nesneyi eklemeden önce kontak sayfasında ya da kaynak nesne
  verisinde (boyut, konum, saydamlık, kırpma) ne olduğuna bak. Ekran görselinin altındaki yarı saydam bir PNG
  gölgedir, logo ya da "marka görseli" değildir; raporda da öyle adlandır. `static` yalnızca hareketi durdurur,
  dönüşümde kaybolan görünümü (alfa, kırpma, efekt) geri getirmez.
- `note`: kararının kısa gerekçesi (kullanıcıya rapor ederken kullanırsın).

Bu dosyayı düzenledikten sonra komutları yeniden çalıştır; kullanıcı düzenlemeleri korunur.

## 3–4. Önizleme (hızlı, az kredi)

- `bin/slideready preview SUNUM.pptx` puanı en yüksek 2 slaytı 960×540, 30 fps render eder (birkaç saniye).
  Belirli slaytlar için `--slides 3,7`.
- Kullanıcıya göster: `preview/NNN.mp4` dosyaları. Kısa bir özet yaz: "12 slayt buldum, 9'unu canlandıracağım,
  3'ü sabit kalacak (kapak, ajanda, kaynakça). İşte 4 ve 7. slaytların önizlemesi." Sonra onay iste.
- Tüm sunumu önizleme kalitesinde render etme; amaç hızlı ve ucuz bir fikir vermek.

## 5. Kontrol listesi (kontak sayfası: %25, %50, %75 ve son kare)

**Referans.** Son kareyi gerçek bir referansla karşılaştır. PowerPoint kuruluysa (Windows/Mac) slaytı PowerPoint'in
kendisine dışa aktar ve onu referans al; Windows'ta örneğin PowerShell:
`$pp = New-Object -ComObject PowerPoint.Application; $p = $pp.Presentations.Open("C:\tam\yol\SUNUM.pptx", $true, $false, $false); $p.Slides(3).Export("C:\tam\yol\ref-003.png", "PNG", 1920, 1080); $p.Close()`.
PowerPoint yoksa karşılaştırma yalnızca LibreOffice render'ına dayanır; bunu raporda açıkça yaz, çünkü LibreOffice'in
kendi hatası o durumda görünmez.

- Son kare referansla aynı mı (eksik/kaymış şekil yok)?
- **Saydamlık ve efektler:** gölgeler, saydam PNG'ler, yumuşak kenarlar, kırpılmış görseller, parlama/yansıma gibi
  efektler referanstakiyle aynı genişlikte, koyulukta ve konumda mı? Daralmış, silikleşmiş, sertleşmiş ya da kaybolmuş
  bir gölge veya efekt açık bir sadakat sorunudur.
- Aynı görsel birden çok slaytta kullanılıyorsa (SVG'de paylaşılan bitmap ve `<use>` referansı) her slaytı ayrı
  kontrol et; ilk slaytın doğru olması diğerlerini kanıtlamaz.
- Metin hiçbir anda hareketli bir görselin üstünde ya da yarı saydam durumda okunmaz kalmıyor mu?
- Sayaçlar doğru biçimde bitiyor mu (₺12,4M, %38, 1.250)?
- `analyze` çıktısında "eşlenmedi" ya da "eksik fontlar" uyarısı var mı? Varsa kullanıcıya söyle.

**Eşleme başarısı görsel sadakat değildir.** "Eşlenmedi" uyarısının olmaması (`unmatched=0`) yalnızca her şeklin bir
katmana bağlandığını gösterir; katmanın içeriği LibreOffice'ten geldiği için görünüm orada zaten bozulmuş olabilir.
Raporda ikisini ayrı yaz: "eşleme: tam" ve "görsel sadakat: referansla doğrulandı / yalnızca LibreOffice ile
karşılaştırıldı / sorun var".

Bir sorun görürsen önce `plan.json` ile çöz (`static`, `tempo`, `animate`). Plan ayarı görünümü düzeltmiyorsa (ör.
gölge son karede de silik) sorunu çözülmüş gibi sunma; hangi slaytta, hangi nesnede ve referansa göre ne kadar fark
olduğunu açıkça raporla.

## 6. Çıktı

- `bin/slideready export SUNUM.pptx` (varsayılan 1080p 60 fps; büyük sunumlarda `--quality 720` dosyayı küçültür).
- Çıktı `SUNUM-SlideReady.pptx`: orijinal sunumun kopyası. Her canlandırılan slaytın en üst katmanında kendi
  videosu vardır; otomatik başlar, döngü yoktur, poster karesi tamamlanmış slayttır. Orijinal şekiller altta,
  düzenlenebilir hâlde kalır. Kullanıcı döngü isterse PowerPoint'te Oynatma > "Durdurulana kadar döngü"yü açar.
- Süre: kabaca slayt başına 15–25 sn render. Uzun işlerde başlamadan önce tahmini söyle.

## Teslim raporu (kısa, kullanıcının dilinde)

1. Çıktı dosyasının yolu ve boyutu.
2. Canlandırılan ve sabit bırakılan slaytlar (gerekçeyle).
3. Eksik fontlar ve eşlenemeyen şekiller, varsa.
4. Görsel sadakat: son karenin neyle karşılaştırıldığı (PowerPoint referansı ya da yalnızca LibreOffice) ve kalan
   farklar (gölge, saydamlık, efekt), eşleme sonucundan ayrı.
5. Doğrulayamadığın şeyler: gerçek PowerPoint'te oynatmayı test edemediysen bunu açıkça yaz.

## Bilinen sınırlar

- Grafikler maskeyle açılır (pasta/halka saat yönünde, sütun aşağıdan, çubuk ve çizgi soldan). Seri seri
  yeniden çizim yol haritasındadır.
- Font slaytta var ama sistemde yoksa LibreOffice benzeriyle değiştirir; görünüm değişebilir. Kullanıcıdan fontu
  kurmasını isteyebilirsin.
- SmartArt ve gömülü Excel nesneleri tek parça olarak açılır.
- Görsellerin ek opaklığı (`a:alphaModFix`) dönüşümden önce görselin alfa kanalına gömülür, çünkü LibreOffice bu
  opaklığı alfaya çarpmak yerine alfadan çıkarır ve yumuşak gölgeleri daraltır. PowerPoint'in gölge, yumuşak kenar,
  parlama ve yansıma efektleri ise LibreOffice'in çizdiği hâliyle gelir; bunları referansla kontrol et.
- Otomatik başlatma PowerPoint 2016+ (Windows/Mac) içindir. Google Slides ve Keynote gömülü videoyu otomatik
  başlatmaz.
