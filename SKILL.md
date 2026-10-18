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
2. **Efektler tekrar etmez, tek efekt her şeye uygulanmaz.** Sunum tek bir film gibi planlanır: her slaytın
   kahraman koreografisi, giriş yönü ve ritmi bir öncekinden farklıdır; aynı anda tek kahraman oynar. Bir slayttaki
   öğe türleri (başlık, metin, kart, tablo, sayı, grafik, ikon, görsel) birbirinden farklı hareket eder. Bir koreografi sunumda bir kez
   kullanılır (istisnası `references/motion.md`'de). "Hepsi aynı hareket" sonucu başarısızlıktır: teslim etme,
   planı değiştir.
3. **Kamera sabittir; hareket öğelerdedir.** Pan, zoom, kamera turu, geri çekilme ve slaytın bütününe paralaks
   yok; arka plan kımıldamaz. Her öğe kendi katmanıyla, kendi hareketiyle gelir: tablo satır satır ya da hücre
   hücre, grafik seri seri ya da eleman eleman, kartlar tek tek. Bütün slaytın, bir tablonun ya da grafiğin üstünden
   tek bir tarayıcı, ışık perdesi ya da maske geçirmek yasaktır.
4. **Son kare PowerPoint'in kendi çizimidir** (ortalama fark ≤1/255).
5. **Okuma süresinde hiçbir şey kıpırdamaz.**
6. **Geçişte kare kaçmaz.** Boş açılış karesi en az 0,3 sn bekler; PowerPoint slayta geçip videoyu başlatırken ilk
   kareleri yutsa bile hiçbir hareket kaybolmaz ve ekranda dolu bir kare belirmez. Klipte eksik, yinelenen ya da
   donan kare olmaz; kare sayısı süre × fps'e eşittir.

`bin/slideready check` bu kuralları ölçer (4. adım). Kontrolden geçmemiş bir sonucu kullanıcıya gönderme.

## İş akışı

| # | Adım | Ne zaman | Komut / iş |
|---|---|---|---|
| 0 | **Kurulum** | "Kur", "repoyu anla" ya da ilk kullanım | `bin/slideready doctor`; eksik varsa `scripts\setup.ps1`, sonra tekrar `doctor` |
| 1 | **Analiz** | PPTX geldiğinde | `bin/slideready analyze SUNUM.pptx` → `analysis.json`, `plan.json` |
| 2 | **Yönetmen** | Analizden hemen sonra, her render'dan önce | `references/motion.md`'yi oku; bütün sunumu tek film olarak planla, her slayta tekrarsız bir `hero` yaz. Ortam destekliyorsa `slideready-director` alt ajanına ver |
| 3 | **Önizleme** | Plan hazır olunca | `bin/slideready preview SUNUM.pptx` (en zengin 2 slayt, düşük kalite); sonunda kalite kontrolü kendiliğinden çalışır |
| 4 | **Kontrol** | Her önizleme ve çıktıdan sonra | `bin/slideready check SUNUM.pptx` + gözle kontrol; ortam destekliyorsa `slideready-reviewer` alt ajanı |
| 5 | **Çıktı** | Kullanıcı onay verince | `bin/slideready export SUNUM.pptx` → `SUNUM-SlideReady.pptx`; sonra 4. adım tekrar |

Kullanıcının gözünden akış üç adımdır: **kur → PPTX'i ver ve önizlemeyi gör → çıktıyı al.** Ara adımları
anlatma, sonucu göster.

**Başta soru sorma.** Tarzı, tempoyu, koreografiyi ve neyin öne çıkacağını sen seçersin. Analiz et, Yönetmen adımını
yap, önizlemeyi üret, kontrolden geçir ve kullanıcıya kısa bir tabloyla hangi slayta ne seçtiğini söyle. Kullanıcı
bir cümleyle değiştirir ("3. slayt daha sade olsun" → `style: "sakin"`). Yalnızca sonucu gerçekten değiştiren bir
belirsizlikte sor (ör. yer tutucu metin kalmış bir slayt).

**Kullanıcı render istemediyse render etme.** "Bir şey üretme", "dur" ya da "bekle" dediyse `preview` ve `export`
çalıştırma; yalnızca istenen işi yap.

**Kendi işini düzelt.** `check` ya da gözle kontrol bir sorun bulursa kullanıcıya göstermeden önce düzelt: önce
`plan.json` (`hero`, `moves`, `tempo`, `hold`, `static`, `animate`), sorun motordaysa nedenini bul. Yalnızca sorunlu
slaytları yeniden render et (`--slides N`) ve `check`'i yeniden çalıştır. Üç turda çözülmezse sorunu ve nedenini
dürüstçe raporla; "TESLİM ETME" diyen bir sonucu asla "hazır" diye sunma.

## 0. Kurulum

- `bin/slideready doctor` her satırı ✓/✗ ile verir ve eksik için kurulum komutunu yazar.
- Slaytları kullanıcının kendi PowerPoint'i çizer (Windows, COM): PowerPoint yoksa `preview`/`export` çalışmaz.
  `doctor`'da "PowerPoint (COM)" ✗ ise kullanıcıya masaüstü PowerPoint gerektiğini söyle.
- `scripts\setup.ps1` (Windows) ffmpeg ve Node'u, Python paketlerini (pywin32 dahil) ve Playwright Chromium'u kurar.
  İzin gerekiyorsa kullanıcıya hangi komutu çalıştıracağını tek satırla söyle.
- Kurulum bitince kullanıcıya tek cümle: "Hazır, PPTX'ini gönderebilirsin."

## 1. Analiz ve plan

`analyze` her slayt için şekil, grafik, tablo ve sayı sayısını, bir "canlandırma puanını" ve notları basar;
`SUNUM.slideready/plan.json` dosyasını yazar. Plan, slayt başına şu alanlardan oluşur:

```json
{"no": 3, "animate": true, "style": "auto", "chosen": "sinematik", "hero": "sayac", "moves": {"baslik": "harf-araligi", "sayi": "odometre-yay", "kart": "cerceve-cizim", "metin": "kelime-netlesme"}, "zoom": 1, "lead": "number", "tempo": 1.0, "hold": 2.0, "static": [], "media": true, "note": "yönetmen: dört ödül sayısı kahraman; kartlar çizilip dolar"}
```

- `animate`: `false` ise slayt sabit kalır, video eklenmez. Kapak, ajanda, kaynakça, hukuki metin, tamamen
  fotoğraftan oluşan ya da yer tutucu metin içeren slaytlar için kullan.
- `style`: `auto` (varsayılan) ajanın ilk kararıdır: `analyze` slaytın içeriğine bakıp `chosen` (tarz) ve `lead`
  (öne çıkan: başlık, sayı, grafik) yazar; gerekçe `note`'a `otomatik:` önekiyle düşer. Paragraf ağırlıklı slaytlar
  `sakin`, görsel ağırlıklı ve az metinli slaytlar `enerjik`, 180 kelimeyi aşan başvuru metinleri sabit. Tarzlar
  yalnızca öğe hareketlerinin şiddetini ve temposunu belirler: `sinematik` (zengin, örtüşen öğe hareketleri), `sakin`
  (yumuşak ve kısa öğe hareketleri; resmî sunumlar için), `enerjik` (yaylı, hızlı öğe hareketleri; tanıtım ve
  lansman için). Kullanıcı "daha sade" derse `sakin`, "daha hareketli" derse `enerjik`. Hepsi PowerPoint'in çizdiği
  aynı son kareye varır.
- `zoom`: her zaman `1`. Kamera sabittir (kural 3); `analyze` başka bir değer yazdıysa Yönetmen `1` yapar.
- `hero`: slaytın kahraman koreografisi (`parcacik`, `dev-baslik`, `derinlik`, `domino`, `bulusma`, `cizim`,
  `tablo-dalga`, `murekkep`, `sayac`, `grafik`, `daktilo`, `ikon-yagmuru`, `kapanis`). Aynı `hero` sunumda bir kez
  kullanılır.
- `moves`: slayttaki her öğe türünün hareketi, türün havuzundan (`baslik`, `metin`, `kart`, `tablo`, `sayi`, `grafik`,
  `ikon`, `gorsel`, `cizgi`). Ardışık iki slaytta aynı tür aynı hareketle gelmez. Ne oldukları, havuzlar, hangi
  slayta yakıştıkları ve süreler `references/motion.md`'dedir. `hero` ve `moves`'u Yönetmen adımında sen yazarsın.
- `effects` (varsayılan `true`): gösteri efektleri. Kullanıcı "efekt istemiyorum" derse `effects: false`. `sakin`
  tarzında efektler kapalıdır.
- `continuity`: kullanılmaz, her zaman `false`. Klip önceki slaytın son karesinden başlamaz (kural 1).
- `tempo`: 1.0 normal; 0.8 daha sakin, 1.2 daha hızlı. Kullanıcı "yavaş/hızlı" derse bunu değiştir.
- `hold`: son hareketten sonraki durağan okuma payı (sn). Varsayılan metin miktarına göre 2–5 sn arasıdır;
  2'nin altına indirme.
- `static`: hareket etmemesi gereken şekil adları (ör. logo, dipnot). Adlar `analysis.json`'dadır.
- `media`: `true` ise slayttaki, düzendeki ya da asıl slayttaki animasyonlu GIF'ler ve videolar videonun içinde
  oynar (arka plan videosu verilerle tek bütün olur; slayt süresi videonun sonuna kadar uzar, en fazla 60 sn; videonun
  sesi klibe eklenir). `false` ise ilk kareleri durağan kalır.
- `note`: kararın kısa gerekçesi (kullanıcıya rapor ederken kullanırsın). `otomatik:` ile başlıyorsa `analyze`,
  `yönetmen:` ile başlıyorsa Yönetmen adımı yazmıştır; başka bir notu kullanıcı yazmıştır ve korunur.

Bu dosyayı düzenledikten sonra komutları yeniden çalıştır; kullanıcı düzenlemeleri korunur.

## 2. Yönetmen: sunumu tek film olarak planla

`analyze` her slayta ayrı ayrı bakar ve benzer slaytlara benzer karar verir; tek başına bırakılırsa her slayt aynı
biçimde açılır. Bu yüzden her render'dan önce Yönetmen adımı zorunludur:

1. `references/motion.md`'yi oku (değişmezler, slayt anatomisi, ilkeler, öğe hareket havuzları, koreografi
   kataloğu, ritim).
2. Bütün canlandırılan slaytları yan yana koy; her slayt için içeriğe en uygun kahraman koreografiyi ve her öğe türü
   için havuzdan bir hareket seç. Sonra desteye bak: aynı `hero` yok, ardışık slaytlarda aynı tür aynı hareketle
   gelmiyor, art arda üç slayt aynı yönden açılmıyor, yoğunluk dalgalanıyor.
3. Kararını `plan.json`'a yaz (`hero`, `moves`, `tempo`, `zoom: 1`, `note: "yönetmen: …"`).
4. Plan denetimini çalıştır; `check` render'dan önce de plan tekrarını yakalar:
   `python -c "import json,sys; sys.path.insert(0,'.'); from slideready.qa import check_plan; print(check_plan(json.load(open(sys.argv[1], encoding='utf-8'))['slides']))" SUNUM.slideready/plan.json`

Kullanıcıya raporu bu kararlardan, slayt başına bir satırla verirsin.

## 3. Önizleme (hızlı, az kredi)

- `bin/slideready preview SUNUM.pptx` puanı en yüksek 2 slaytı 960×540, 30 fps render eder (birkaç saniye).
  Belirli slaytlar için `--slides 3,7`.
- Önce kontrolden geçir (4. adım). Sonra kullanıcıya göster: `preview/NNN.mp4` dosyaları ve slayt başına bir satırlık
  koreografi tablosu ("1. slayt: başlık parçacıklardan toplanır; 3. slayt: ödül sayıları rakam rakam döner ve
  yaylanarak oturur; 5. slayt: kartlar domino gibi açılır"). Sonra onay iste.
- Tüm sunumu önizleme kalitesinde render etme; amaç hızlı ve ucuz bir fikir vermek.

## 4. Kontrol

**Otomatik:** `bin/slideready check SUNUM.pptx`. `preview` ve `export` bunu sonda kendiliğinden çalıştırır; sonucu
`SUNUM.slideready/qa.json`'a da yazar. Ölçtükleri:

- ilk kare boş ve boş açılış en az 0,3 sn (içerik pikselleri arka plana yakın; hareketli medya kutuları hariç),
- kare sayısı = süre × fps (±1), sabit kare hızı, hareket ortasında takılan (yinelenen) kare yok,
- son kare PowerPoint'in çizdiği slayt, okuma payında hiçbir şey kımıldamıyor,
- `plan.json`'da kahraman koreografi tekrarı ve art arda aynı açılış,
- kamera sabit mi: içeriğin dışında kalan boş arka plan hiçbir karede topluca değişmiyor (zoom, pan, ekranı
  süpüren perde ya da tarayıcı bunu bozar),
- `plan.json`'da `zoom` 1 değilse, `continuity` açıksa, `moves` havuz dışıysa ya da ardışık slaytlarda aynıysa hata,
- kliplerin görsel açılış imzası (içerik hangi yönden, hangi sırayla, ne hızda geliyor): art arda iki slayt aynı
  biçimde açılıyorsa hata,
- çıktı PPTX'te her videonun posteri boş açılış karesi ve video döngüsüz.

Her `✗` engelleyicidir; "✗ TESLİM ETME" çıktısıyla kullanıcıya gitme, önce düzelt.

**Gözle** (kontak sayfası: %25, %50, %75 ve son kare; ayrıca ilk kare ve kahraman anın ortası):

- Slaytlar birbirinden gerçekten farklı açılıyor mu? Hepsi "yukarı kayıp netleşme" ise Yönetmen adımına dön.
- Aynı anda tek kahraman mı var; destek öğeleri okuma sırasıyla mı geliyor?
- Her öğe kendi hareketiyle mi geliyor? Bir tablo, grafik ya da kart grubu tek parça bir maskeyle veya üstünden geçen
  bir tarayıcıyla açılıyorsa, ya da bir slayttaki bütün öğeler aynı hareketle geliyorsa düzelt.
- Satır, hücre ya da sütun hiçbir an yarı kesik görünüyor mu?
- Hızlı harekette hareket bulanıklığı görünüyor, durunca keskinleşiyor mu?
- Metin hiçbir anda hareketli bir görselin arkasında, bulanık ya da yarı saydam kalmıyor mu?
- Sayaçlar doğru biçimde bitiyor mu (₺12,4M, %38, 1.250)?
- Tek parça film ürettiysen slayt sınırlarındaki kareler: önceki slaytın son karesinden sonra doğrudan boş arka plan.

## 5. Çıktı

- Çıktı varsayılan olarak hareket bulanıklığıyla (4 alt kare) render edilir; 1080p60'ta 30 sn'lik video için
  yaklaşık 7 dakika sürer. Kullanıcı acele ediyorsa `--motion-blur 1` (hareket anlarında 4 kat daha az kare çekilir).

- `bin/slideready export SUNUM.pptx` (varsayılan 1080p 60 fps; büyük sunumlarda `--quality 720` dosyayı küçültür).
- Çıktı `SUNUM-SlideReady.pptx`: orijinal sunumun kopyası. Her canlandırılan slaytın en üst katmanında kendi
  videosu vardır; otomatik başlar, döngü yoktur, poster boş açılış karesidir (yalnızca arka plan; dolu-sonra-boş sıçraması olmasın diye); video bitince tamamlanmış slaytta kalır. Orijinal şekiller altta,
  düzenlenebilir hâlde kalır. Kullanıcı döngü isterse PowerPoint'te Oynatma > "Durdurulana kadar döngü"yü açar.
- Süre: kabaca slayt başına 15–25 sn render. Uzun işlerde başlamadan önce tahmini söyle.
- Çıktıdan sonra `check` kendiliğinden çalışır; posterler ve bütün klipler bir kez daha ölçülür.

## Teslim raporu (kısa, kullanıcının dilinde)

1. Çıktı dosyasının yolu ve boyutu.
2. Slayt başına bir satır: kahraman koreografi, öne çıkan öğe hareketleri ve neden (Yönetmen kararından); sabit bırakılan slaytlar gerekçesiyle.
3. `check` sonucu: bütün kurallar sağlanıyor mu; uyarı varsa hangisi.
4. Eksik fontlar ve eşlenemeyen şekiller, varsa.
5. Doğrulayamadığın şeyler: gerçek PowerPoint'te oynatmayı test edemediysen bunu açıkça yaz.

## Bilinen sınırlar

- Koreografi kataloğu ve `moves` havuzları hareket motoruyla yapılan sözleşmedir. Motor bugün parçacıklı başlığı
  (`hero: "parcacik"`, eski adıyla `title`), büyük görselde mürekkep açılışını ve odometre sayacını oynatır; diğerleri
  yazılma aşamasındadır ve motor tanımadığı bir `hero` ya da hareketi yok sayar. Bu durumda `check` yine çalışır:
  kamera hareketi, aynı açılışlar ve kurallara aykırı plan yakalanır, teslim edilmez.
- Bugünkü motorda grafikler ve tablolar tek katman olarak açılır (maskeyle). Kural 3'e göre bu teslim edilemez bir
  durumdur; grafiklerin seri/eleman ve tabloların satır/hücre katmanlarına ayrılması (PowerPoint'in kendi
  konumlarıyla) motorda yazılma aşamasındadır. O zamana kadar grafik ya da tablo içeren bir slaytı `static` ya da
  `animate: false` yapmayı kullanıcıya açıkça söyle.
- Görüntü PowerPoint'in kendi çizimidir: font sistemde yoksa PowerPoint'te nasıl görünüyorsa videoda da öyle görünür.
- Tablo hücrelerindeki sayılar henüz saymaz; tek başına duran sayılar sayar.
- SmartArt ve gömülü Excel nesneleri tek parça olarak açılır.
- Metin, şekil ya da grafik slayta **resim olarak** konmuşsa (ekran görüntüsü vb.) ve resmin zemini düz renkli ya da
  saydamsa, resim okuma sırasıyla blok blok açılır (`analyze` notu: "resim içinde N blok"). Resimdeki sayılar
  sayaçla saymaz (OCR yok); fotoğraflar ve üstünde başka şekil olan resimler tek parça açılır.
- `analyze` notunda "hareketli medya" görürsen önizlemede GIF/videonun oynadığını kontrol et.
- Otomatik başlatma PowerPoint 2016+ (Windows/Mac) içindir. Google Slides ve Keynote gömülü videoyu otomatik
  başlatmaz.
