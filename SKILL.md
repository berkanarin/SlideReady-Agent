---
name: slideready
description: Bir PowerPoint sunumunun (PPTX) her slaytını, tasarımını ve yerleşimini bozmadan hareketli videoya çevirir ve videoları aynı sunumun içine geri gömer. Her slayt boş arka plandan başlar ve sunumun geri kalanında tekrarlanmayan kendi koreografisiyle kurulur; görüntüyü kullanıcının PowerPoint'i çizer. Kullanıcı "PPTX'i işle", "sunumu canlandır", "slaytları videoya çevir", "motion graphic yap" ya da "SlideReady" dediğinde kullan.
---

# SlideReady

Kullanıcının sunumunu **yeniden tasarlamadan** canlandırırsın. Her slaytın kendi şekilleri katman katman açılır,
videonun son karesi orijinal slaytın ta kendisidir. Çıktı yine bir PPTX'tir: her slaytta kendi videosu, otomatik
başlar, **döngü yoktur**.

Bütün ağır iş `bin/slideready` aracındadır (Windows'ta `bin\slideready.cmd`). Yollar bu SKILL.md'nin
bulunduğu klasöre göredir; skill başka bir projeden çağrıldıysa aracı tam yoluyla çalıştır. Senin işin aşamaları sırayla
yürütmek, karar gereken yerde karar vermek ve kullanıcıyla kısa, net konuşmaktır. **Koordinat üretme, slaytı
yeniden çizme, HTML yazma.** Yerleşim her zaman dosyadan gelir; senin elindeki tek ayar kolu `plan.json`'dur.

## Değişmez kurallar (hiçbir slaytta, hiçbir tarzda çiğnenmez)

1. **İlk kare boştur.** Her klibin ilk karesinde yalnızca slaytın arka planı (arka plan rengi/görseli/videosu ile
   asıl slayt ve düzen süsleri) görünür; hiçbir içerik şekli, metin ya da önceki slayttan kalan görüntü olmaz. Poster
   de bu boş karedir. PowerPoint videoyu başlatırken dolu bir kare görünürse "önce dolu, sonra boş" sıçraması olur;
   kullanıcı bunu kesinlikle istemiyor. Önceki slaytın son karesinden başlayan geçiş (`continuity`) kullanılmaz.
2. **Efektler tekrar etmez.** Sunum tek bir film gibi planlanır: her slaytın kahraman efekti, giriş yönü, kamera
   hareketi ve ritmi bir öncekinden farklıdır. Bir kahraman efekt sunumda bir kez kullanılır; slayt sayısı efekt
   sayısını aşarsa bile aynı efekt art arda iki slaytta ve aynı birleşimle (efekt + kamera + giriş yönü) iki kez
   gelmez. "Hepsi aynı hareket" sonucu başarısızlıktır: kullanıcıya teslim etme, planı değiştir.
3. **Son kare PowerPoint'in kendi çizimidir** (ortalama fark ≤1/255).
4. **Okuma süresinde hiçbir şey kıpırdamaz.**

Teslimden önce 1 ve 2'yi kendin doğrula (aşağıda "Kontrol listesi"). Doğrulamadığın bir sonucu kullanıcıya
gönderme.

## Ekip ve sıra

Aşağıdaki roller tek akışın aşamalarıdır. Her birini sırayla sen üstlenirsin; ayrı bir ajan açman gerekmez.
Yalnızca **Kontrolcü** için, ortam destekliyorsa `slideready-reviewer` alt ajanını kullanabilirsin.

| # | Rol | Ne zaman | Komut / iş |
|---|---|---|---|
| 0 | **Kurulumcu** | Kullanıcı "kur", "repoyu anla" dediğinde ya da ilk kullanımda | `bin/slideready doctor`; eksik varsa `scripts\setup.ps1` (Windows; render PowerPoint ister), sonra tekrar `doctor` |
| 1 | **Tanımlayıcı** | PPTX geldiğinde | `bin/slideready analyze SUNUM.pptx` |
| 2 | **Yönetmen** | Analizden hemen sonra | Bütün sunumun koreografi tablosunu çıkar (slayt → kahraman efekt → kamera → giriş yönü), tekrarları `plan.json`'da düzelt (aşağıda) |
| 3–4 | **Animatör + Önizlemeci** | Plan hazır olunca | `bin/slideready preview SUNUM.pptx` (en zengin 1–2 slayt, düşük kalite) |
| 5 | **Kontrolcü** | Önizleme çıkınca | `SUNUM.slideready/preview/NNN-sheet.png` kontak sayfalarına bak (aşağıdaki liste) |
| 6 | **Çıktıcı** | Kullanıcı onay verince | `bin/slideready export SUNUM.pptx` → `SUNUM-SlideReady.pptx` |

Kullanıcının gözünden akış üç adımdır: **kur → PPTX'i ver ve önizlemeyi gör → çıktıyı al.** Ara adımları
anlatma, sonucu göster.

**Başta soru sorma.** Tarzı, tempoyu, neyin öne çıkacağını sen seçersin: `analyze` her slayt için bir karar verir
(`plan.json`'da `style: "auto"`, seçilen tarz `chosen`, gerekçe `note`). Analiz et, karar ver, önizlemeyi üret ve
kullanıcıya tek kısa paragrafta hangi slayta ne seçtiğini ve neden seçtiğini söyle. Kullanıcı bir cümleyle değiştirir
("3. slayt daha sade olsun" → `style: "sakin"`). Yalnızca sonucu gerçekten değiştiren bir belirsizlikte sor (ör. yer
tutucu metin kalmış bir slayt).

## 0. Kurulum

- `bin/slideready doctor` her satırı ✓/✗ ile verir ve eksik için kurulum komutunu yazar.
- Slaytları kullanıcının kendi PowerPoint'i çizer (Windows, COM): PowerPoint yoksa `preview`/`export` çalışmaz.
  `doctor`'da "PowerPoint (COM)" ✗ ise kullanıcıya masaüstü PowerPoint gerektiğini söyle.
- `scripts\setup.ps1` (Windows) ffmpeg ve Node'u, Python paketlerini (pywin32 dahil) ve Playwright Chromium'u kurar.
  İzin gerekiyorsa kullanıcıya hangi komutu çalıştıracağını tek satırla söyle.
- Kurulum bitince kullanıcıya tek cümle: "Hazır, PPTX'ini gönderebilirsin."

## 1–2. Analiz ve plan

`analyze` her slayt için şekil, grafik, tablo ve sayı sayısını, bir "canlandırma puanını" ve notları basar;
`SUNUM.slideready/plan.json` dosyasını yazar. Plan, slayt başına şu alanlardan oluşur:

```json
{"no": 3, "animate": true, "style": "auto", "chosen": "sinematik", "zoom": 1.04, "lead": "number", "tempo": 1.0, "hold": 2.0, "static": [], "media": true, "note": ""}
```

- `animate`: `false` ise slayt sabit kalır, video eklenmez. Kapak, ajanda, kaynakça, hukuki metin, tamamen
  fotoğraftan oluşan ya da yer tutucu metin içeren slaytlar için kullan.
- `style`: `auto` (varsayılan) ajanın kararıdır: `analyze` slaytın içeriğine bakıp `chosen` (tarz), `zoom` (kamera
  yakınlığı) ve `lead` (öne çıkan: başlık, sayı, grafik) yazar; gerekçe `note`'a `otomatik:` önekiyle düşer. Kurallar:
  kapak ve az öğeli bölüm slaytları en güçlü kamera; sayı/grafik yoğun slaytlarda kamera sakin, veri önce gelir ve
  açıklama sonra; paragraf ağırlıklı slaytlar `sakin`; görsel ağırlıklı, az metinli slaytlar `enerjik`; kapanış
  slaytı yavaş geri çekilme; 180 kelimeyi aşan başvuru metinleri sabit. Deste tek aile içinde kalır (`sakin` ile
  `enerjik` art arda gelmez). Elle bir tarz yazılırsa karar yalnızca not olarak kalır. Tarzlar: `sinematik` ( kamera başlığın üstünden geri çekilir, katmanlar farklı derinlikte
  kayar, öğeler bulanıktan netleşir, başlık kelime kelime / metin satır satır açılır, panellerden ışık geçer, sayaç
  bitince parlar), `sakin` (kamera yok, yumuşak netleşme ve satır satır metin; resmî sunumlar için), `enerjik` (daha
  yakın kamera, yaylanan ikonlar ve sayılar, hızlı tempo; tanıtım ve lansman için). Kullanıcı "daha sade" derse
  `sakin`, "daha hareketli" derse `enerjik`. Hepsi PowerPoint'in çizdiği aynı son kareye varır.
- `effects` (varsayılan `true`): gösteri efektleri. Slayt başına tek bir kahraman efekt olur (`hero`); hangisinin
  nerede oynayacağını sunumun tamamına bakarak sen seçersin, slayt türüne göre ezbere değil. Kullanıcı "efekt
  istemiyorum" derse `effects: false`. `sakin` tarzında efektler kapalıdır.
- `continuity`: kullanılmaz, her zaman `false`. Klip önceki slaytın son karesinden başlamaz (kural 1).
- `tempo`: 1.0 normal; 0.8 daha sakin, 1.2 daha hızlı. Kullanıcı "yavaş/hızlı" derse bunu değiştir.
- `hold`: son hareketten sonraki durağan okuma payı (sn). Varsayılan metin miktarına göre 2–5 sn arasıdır;
  2'nin altına indirme.
- `static`: hareket etmemesi gereken şekil adları (ör. logo, dipnot). Adlar `analysis.json`'dadır.
- `media`: `true` ise slayttaki, düzendeki ya da asıl slayttaki animasyonlu GIF'ler ve videolar videonun içinde
  oynar (arka plan videosu verilerle tek bütün olur; slayt süresi videonun sonuna kadar uzar, en fazla 60 sn; videonun
  sesi klibe eklenir). `false` ise ilk kareleri durağan kalır.
- `note`: kararın kısa gerekçesi (kullanıcıya rapor ederken kullanırsın). `otomatik:` ile başlıyorsa `analyze` yazmıştır
  ve her çalıştırmada yenilenir; kendi notunu yazarsan korunur.

Bu dosyayı düzenledikten sonra komutları yeniden çalıştır; kullanıcı düzenlemeleri korunur.

### Yönetmen: sunumu tek film olarak planla

`analyze` her slayta ayrı ayrı bakar; benzer slaytlara benzer karar verir. Bu yüzden önizlemeden önce bütün
slaytların kararını yan yana koy ve şu tabloyu kendin için yaz:

| Slayt | Kahraman efekt (`hero`) | Kamera (`zoom`, tarz) | Öne çıkan (`lead`) | Giriş yönü / ritim |
|---|---|---|---|---|

- Aynı kahraman efekt iki slaytta varsa birini başka bir efektle değiştir; benzer slaytlar (ör. altı kartlı slayt)
  farklı giriş yönü, farklı kamera ve farklı ritimle açılmalı.
- Kapak ve kapanış sunumun en güçlü iki anıdır ama aynı hareketi tekrar etmez.
- Kamera yakınlığını (`zoom`) ve tempoyu (`tempo`) slayttan slayta değiştir; art arda üç slayt aynı kamera
  hareketini yapmaz.
- Kullanıcıya raporu bu tablodan, her slayt için bir satırla ver; tabloda tekrar varsa önce düzelt.

## 3–4. Önizleme (hızlı, az kredi)

- `bin/slideready preview SUNUM.pptx` puanı en yüksek 2 slaytı 960×540, 30 fps render eder (birkaç saniye).
  Belirli slaytlar için `--slides 3,7`.
- Kullanıcıya göster: `preview/NNN.mp4` dosyaları. Kısa bir özet yaz: "12 slayt buldum, 9'unu canlandıracağım. Kapakta güçlü bir kamera,
  sayı slaytlarında önce sayılar, metin yoğun 5. slaytta sakin bir giriş seçtim. İşte 1 ve 3. slaytların önizlemesi."
  Sonra onay iste.
- Tüm sunumu önizleme kalitesinde render etme; amaç hızlı ve ucuz bir fikir vermek.

## 5. Kontrol listesi (kontak sayfası: %25, %50, %75 ve son kare)

- **İlk kare boş mu?** Her klibin ilk karesini çıkar ve bak:
  `ffmpeg -v error -i preview/NNN.mp4 -frames:v 1 NNN-ilk.png` (çıktıda her video için aynısını yap). Arka plan
  dışında tek bir şekil, metin ya da önceki slayttan kalıntı görürsen teslim etme; nedenini bul ve düzelt.
- **Tekrar var mı?** Bütün slaytların kontak sayfalarını yan yana koy. İki slayt aynı biçimde açılıyorsa (aynı
  efekt, aynı yön, aynı kamera) Yönetmen tablosuna dön.

- Son kare orijinal slaytla aynı mı (eksik/kaymış şekil yok)?
- Metin hiçbir anda hareketli bir görselin üstünde ya da yarı saydam durumda okunmaz kalmıyor mu?
- Sayaçlar doğru biçimde bitiyor mu (₺12,4M, %38, 1.250)?
- `preview` çıktısındaki "PowerPoint karesinden fark" 1/255'ten büyük mü? Büyükse son kare PowerPoint'ten sapmış
  olabilir; kullanıcıya söyle.

Bir sorun görürsen önce `plan.json` ile çöz (`static`, `tempo`, `animate`). Çözülmüyorsa sorunu dürüstçe raporla.

## 6. Çıktı

- Çıktı varsayılan olarak hareket bulanıklığıyla (4 alt kare) render edilir; 1080p60'ta 30 sn'lik video için
  yaklaşık 7 dakika sürer. Kullanıcı acele ediyorsa `--motion-blur 1` (hareket anlarında 4 kat daha az kare çekilir).

- `bin/slideready export SUNUM.pptx` (varsayılan 1080p 60 fps; büyük sunumlarda `--quality 720` dosyayı küçültür).
- Çıktı `SUNUM-SlideReady.pptx`: orijinal sunumun kopyası. Her canlandırılan slaytın en üst katmanında kendi
  videosu vardır; otomatik başlar, döngü yoktur, poster boş açılış karesidir (yalnızca arka plan; dolu-sonra-boş sıçraması olmasın diye); video bitince tamamlanmış slaytta kalır. Orijinal şekiller altta,
  düzenlenebilir hâlde kalır. Kullanıcı döngü isterse PowerPoint'te Oynatma > "Durdurulana kadar döngü"yü açar.
- Süre: kabaca slayt başına 15–25 sn render. Uzun işlerde başlamadan önce tahmini söyle.

## Teslim raporu (kısa, kullanıcının dilinde)

1. Çıktı dosyasının yolu ve boyutu.
2. Slayt başına bir satır: kahraman efekt, kamera ve giriş (Yönetmen tablosundan); sabit bırakılan slaytlar
   gerekçesiyle.
3. İlk karelerin tek tek kontrol edildiği ve boş olduğu.
4. Eksik fontlar ve eşlenemeyen şekiller, varsa.
5. Doğrulayamadığın şeyler: gerçek PowerPoint'te oynatmayı test edemediysen bunu açıkça yaz.

## Bilinen sınırlar

- Grafikler maskeyle açılır (pasta/halka saat yönünde, sütun aşağıdan, çubuk ve çizgi soldan). Seri seri
  yeniden çizim yol haritasındadır.
- Görüntü PowerPoint'in kendi çizimidir: font sistemde yoksa PowerPoint'te nasıl görünüyorsa videoda da öyle görünür.
- Tablo hücrelerindeki sayılar saymaz (tablo satır satır açılır); tek başına duran sayılar sayar.
- SmartArt ve gömülü Excel nesneleri tek parça olarak açılır.
- Metin, şekil ya da grafik slayta **resim olarak** konmuşsa (ekran görüntüsü vb.) ve resmin zemini düz renkli ya da
  saydamsa, resim okuma sırasıyla blok blok açılır (`analyze` notu: "resim içinde N blok"). Resimdeki sayılar
  sayaçla saymaz (OCR yok); fotoğraflar ve üstünde başka şekil olan resimler tek parça açılır.
- `analyze` notunda "hareketli medya" görürsen önizlemede GIF/videonun oynadığını kontrol et.
- Otomatik başlatma PowerPoint 2016+ (Windows/Mac) içindir. Google Slides ve Keynote gömülü videoyu otomatik
  başlatmaz.
