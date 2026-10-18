# SlideReady Agent

**PowerPoint sunumunu bozmadan, elle yapılması çok zor bir hareket diliyle canlandırır.** Her öğe kendi
katmanıyla ve kendi hareketiyle gelir: başlık kendi piksellerinden binlerce parçacıkla toplanır, sayılar odometre
gibi rakam rakam döner, kartlar tek tek yaylanır; kamera sabittir ve hiçbir slayt bir öncekinin hareketini
tekrarlamaz. Hızlı hareketlerde gerçek hareket bulanıklığı vardır. Görüntüyü sizin PowerPoint'iniz çizer: videonun son karesi orijinal slaytın ta kendisidir.
Çıktı yine **PPTX**'tir: her slaytta kendi videosu, otomatik başlar, döngü yoktur.

![SlideReady örnek çıktı](docs/demo.gif)

*Yukarıdaki animasyon, repodaki kurgusal `examples/demo.pptx` dosyasının dört slaytının art arda oynatılmasıdır.
Önceki hareket motoruyla üretildi; kamera hareketi, slaytlar arası geçiş ve tablo/grafik üstünden geçen tarama gibi
artık yasak olan hareketler içerir. Yeni kurallarla yenilenecek.*

Claude (Claude Code skill'i) ve Codex (AGENTS.md) ile ajan olarak çalışır; tek başına komut satırı aracı olarak da
kullanılabilir.

## Kullanıcı olarak üç adım

Repoyu Claude Code ya da Codex'te açın ve şunları yazın:

1. **"Repoyu kur."** Ajan gerekli araçları kontrol eder ve eksikleri kurar.
2. **"Şu PPTX'i işle."** (dosyayı ekleyin) Ajan size soru sormaz: sunumu çözümler, her slayt için hareketi kendisi
   seçer, en zengin 1–2 slaytın önizlemesini gösterir ve neyi neden seçtiğini tek paragrafta anlatır.
3. **"Tamam, çıktı al."** Ajan bütün slaytları render eder ve `SUNUM-SlideReady.pptx` dosyasını verir.

Değişiklik isterseniz tek cümle yeterli: "3. slayt daha sade olsun", "logoyu hareket ettirme", "efekt istemiyorum",
"kapak sabit kalsın".

## Ajan neye nasıl karar verir

Ajan iki aşamada karar verir ve başta soru sormaz:

1. **Analiz:** `analyze` her slayda bakar ve `plan.json`'a tarz ve öne çıkan öğe için bir ilk karar yazar
   (`style: "auto"`, gerekçe `note` alanında). Paragraf ağırlıklı slaytlar `sakin`, görsel ağırlıklılar `enerjik`
   olur; 180 kelimeyi aşan başvuru metinleri sabit kalır.
2. **Yönetmen:** ajan bütün sunumu tek film olarak planlar ve her slayta bir kahraman koreografi (`hero`) seçer:
   parçacıklarla toplanan başlık, yerine oturan dev başlık, uzaktan uçup oturan kartlar, domino, iki yandan
   buluşma, çizilip dolan kartlar, tablo dalgası, mürekkep, sayaç anı, grafik büyümesi, daktilo, ikon yağmuru,
   kapanış. Slayttaki her öğe türüne de kendi havuzundan bir hareket seçer (`moves`). Aynı koreografi sunumda bir
   kez kullanılır, ardışık slaytlarda aynı öğe aynı hareketle gelmez, kamera hiç oynamaz. Ayrıntılar ve süreler: [references/motion.md](references/motion.md).

Elle seçilen tarz (`sinematik`, `sakin`, `enerjik`) ve elle yazılan notlar her zaman korunur.

## Efektler

| Efekt | Ne yapar |
|---|---|
| Parçacıklarla toplanma | Başlık, kendi piksellerinden örneklenmiş 2.500–9.000 parçacıktan oluşur; parçacıklar parlayan, kavisli bir akımla gelip harfleri soldan sağa doldurur, son anda gerçek katmana çözülür |
| Odometre sayaç | PowerPoint her rakam konumu için 0–9 çeşitlerini çizer; her rakam kendi sütununda döner, hızla orantılı bulanıklaşır, kendi gecikmesiyle durur. ₺, %, M ve Türkçe sayı biçimi korunur |
| Kinetik metin | Başlık kelime kelime, harf aralığı daralarak; gövde metni satır satır açılır (satır ve kelime yerleri PowerPoint'ten) |
| Vurgu | Sayı yerine oturunca kısa parıltı; bir slaytta en fazla bir öğede. Ekranı ya da bir tabloyu süpüren ışık perdesi yok |
| Mürekkep açılışı | Büyük görseller gürültü eşiği, parlayan yanık kenar ve sönen bükülmeyle açılır |
| Yay fiziği | İkonlar, kartlar ve sayılar yaylanarak yerine oturur |
| Grafikler ve tablolar | Hedef: her sütun, dilim, seri ve tablo satırı kendi katmanıyla, kendi gecikmesiyle gelir (bkz. Sınırlar) |
| Hareket bulanıklığı | Çıktıda her kare, 180° obtüratörle alınmış 4 alt karenin ortalamasıdır; yalnızca hareket varken |
| GIF ve video | Slayttaki, düzendeki ya da asıl slayttaki GIF ve videolar kendi kareleriyle oynar; arka plan videosu verilerle tek bütündür |
| Resim olarak konmuş metin | Ekran görüntüsü gibi düz zeminli resimler blok blok, okuma sırasıyla açılır |

## Değişmez kurallar

- **İlk kare boştur, içerikten hiçbir kalıntı olmaz.** Her klip yalnızca slaydın arka planıyla açılır; yarım şekil,
  iz, bulanıklık, parçacık ya da yarı saydam hayalet olmaz, önceki slayttan hiçbir şey taşınmaz. `check` ilk kareleri
  arka planla piksel piksel karşılaştırır, tek bir kalıntıda teslimi durdurur.
- **Efektler tekrar etmez, tek efekt her şeye uygulanmaz.** Sunum tek film gibi planlanır: her slaytın kahraman
  koreografisi, giriş yönü ve ritmi farklıdır; bir slayttaki başlık, kart, tablo ve sayılar farklı hareket eder.
  Ajan bütün slaytları yan yana koyup tekrarları düzeltmeden teslim etmez.
- **Kamera sabittir.** Pan, zoom, kamera turu yok; arka plan kımıldamaz. Hareket yalnızca öğelerdedir ve bir tablonun,
  grafiğin ya da slaytın tamamının üstünden tek bir tarayıcı veya maske geçmez.
- **Geçişte kare kaçmaz.** Boş açılış en az 0,3 sn sürer; PowerPoint videoyu başlatırken ilk kareleri yutsa bile
  hareket kaybolmaz. Ajan her klipte kare sayısını ve slayt sınırlarındaki kareleri kontrol eder.
- **Son kare PowerPoint'in kendisidir.** Her efekt PowerPoint'in çizdiği katmandan beslenir ve bitince katmanın
  kendisine devreder. Son kare PowerPoint'in kendi slayt görüntüsüyle ölçülür (`layers/NNN/layers.json` →
  `fidelity`); örnek destelerde ortalama fark 0,05/255'in altındadır.
- **Okuma payında hiçbir şey kımıldamaz.** Bütün öğe hareketleri ve parçacıklar okuma payından önce durur; her slaytın sonunda
  en az 2 saniye (metin arttıkça daha uzun) durağan okuma payı vardır. Metin hareketli bir görselin üstünden geçmez.

## Nasıl çalışır

```
PPTX ──python-pptx──▶ şekil envanteri (tür, metin, grafik verisi, tablo, şekil kimliği)
  │                          │
  │                          ▼
  │                 ajan kararı (style: auto) ──▶ plan.json (elle de düzenlenebilir)
  │                          │
  └──PowerPoint (COM)──▶ arka plan + şekil başına saydam katman (gölge, parlama dahil)
                       + satır/kelime yerleri, rakam çeşitleri, önceki slaydın son karesi
                             ▼
       HTML sahnesi: SVG katmanlar + WebGL/canvas efektleri, render(t) saf fonksiyon
                             ▼
       Playwright (Chromium) ──▶ kareler (hareket bulanıklığı) ──ffmpeg──▶ MP4
                             ▼
       orijinal PPTX + slayt başına video (otomatik, döngüsüz)
```

- Model koordinat üretmez; yerleşim her zaman dosyadan gelir. Ajanın tek ayar kolu `plan.json`'dur.
- Görüntüyü kullanıcının kendi PowerPoint'i çizer: fontlar, efektler ve arka plan görselleri PowerPoint'te nasıl
  görünüyorsa öyledir. Her şekil yalnızca kendisi görünürken bir kez beyaz, bir kez siyah zeminde dışa aktarılır; iki
  karenin farkından gölge ve parlama dahil tam saydamlık çıkar. Sunum her zaman geçici bir kopyadan, salt okunur
  açılır; açık belgenize dokunulmaz.
- Her şey yerelde çalışır; sunum hiçbir servise gönderilmez. LibreOffice gerekmez.

## Kurulum

Gerekenler: **Windows ve masaüstü Microsoft PowerPoint**, Python 3.9+ (pywin32 ile), ffmpeg, Node.js 18+ ve
Playwright Chromium. PowerPoint olmayan bir makinede (macOS, Linux) yalnızca `analyze` çalışır.

```bash
git clone https://github.com/berkanarin/SlideReady-Agent.git
cd SlideReady-Agent
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
bin\slideready doctor          # her şey ✓ olmalı ("PowerPoint (COM)" satırı dahil)
```

Elle kurmak isterseniz: `pip install -r requirements.txt`, `npm install`, `npx playwright install chromium`, ayrıca
ffmpeg (`winget install Gyan.FFmpeg`).

### Claude'a skill olarak eklemek

- **Claude Code:** repoyu açmanız yeterli (`CLAUDE.md` ve `SKILL.md` otomatik okunur). Her projede kullanmak için
  repoyu `~/.claude/skills/slideready/` olarak klonlayın.
- **Codex:** repoyu açın; `AGENTS.md` otomatik okunur.
- Alt ajanlar (`.claude/agents/`): `slideready-director` sunumu tek film olarak planlar ve `plan.json`'a yazar;
  `slideready-reviewer` her önizleme ve çıktıdan sonra `check` sonucunu ve kareleri denetler.

## Komut satırı

```bash
bin/slideready analyze  sunum.pptx                 # çözümleme, ajan kararı + sunum.slideready/plan.json
bin/slideready preview  sunum.pptx                 # en zengin 2 slayt, 960×540, hareket bulanıklığı yok
bin/slideready preview  sunum.pptx --slides 3,7    # belirli slaytlar
bin/slideready export   sunum.pptx                 # tüm slaytlar, 1080p 60 fps, hareket bulanıklığı → sunum-SlideReady.pptx
bin/slideready export   sunum.pptx --quality 720   # daha küçük dosya
bin/slideready export   sunum.pptx --motion-blur 1 # hareket bulanıklığı kapalı: daha hızlı render
bin/slideready check    sunum.pptx                 # kalite kontrolü: boş ilk kare, kare kaybı, son kare, tekrar, posterler
```

`plan.json` slayt başına şu alanları içerir:

| Alan | Anlamı |
|---|---|
| `animate` | `false`: slayt sabit kalır, video eklenmez |
| `style` | `auto` (varsayılan): ajan seçer (`chosen`, `lead` alanlarını yazar). Elle: `sinematik`, `sakin` (efektsiz, sade), `enerjik` (belirgin yaylanma, hızlı tempo) |
| `hero` | Slaytın kahraman koreografisi; sunumda bir kez kullanılır ([references/motion.md](references/motion.md)) |
| `moves` | Öğe türü başına hareket (başlık, metin, kart, tablo, sayı, grafik, ikon, görsel); ardışık slaytlarda aynı tür aynı hareketle gelmez |
| `zoom` | Her zaman 1: kamera sabittir |
| `tempo` | 1.0 normal, 0.8 sakin, 1.2 hızlı (tarzın kendi temposuyla çarpılır) |
| `effects` | `true` (varsayılan): yukarıdaki gösteri efektleri. `false`: yalnızca tarzın temel hareketleri |
| `hold` | Son hareketten sonraki okuma payı (sn, en az 2) |
| `static` | Hareket etmemesi gereken şekil adları (logo, dipnot…) |
| `media` | `false`: GIF ve videolar ilk karelerinde durağan kalır |
| `note` | Kararın gerekçesi (`otomatik:` ile başlıyorsa ajan yazmıştır ve her çalıştırmada yenilenir) |

## Süreler

Ölçümler bir Windows dizüstü bilgisayarda (PowerPoint 365):

- PowerPoint katman çizimi: slayt başına 0,5–11 saniye (sayaçlı slaytlar her rakamın 0–9 çeşitlerini de çizdiği
  için en uzunudur).
- Önizleme (4 slayt, 960×540): yaklaşık 1 dakika.
- `examples/demo.pptx` tam çıktısı (4 slayt, toplam 34 saniye video, 1080p 60 fps, hareket bulanıklığıyla):
  yaklaşık 7 dakika. `--motion-blur 1` hareket anlarında 4 kat daha az kare çeker.

## Çıktı PPTX

- Orijinal sunumun kopyasıdır; videolar canlandırılan her slaytın en üst katmanına tam ekran yerleşir.
- Video slayt açılınca **otomatik başlar, döngü yoktur.** Döngü isterseniz PowerPoint'te videoyu seçip
  Oynatma > "Durdurulana kadar döngü"yü işaretleyin.
- Her klibin ilk karesi boştur: yalnızca slaydın arka planı görünür, içerik sonradan gelir. Poster de bu karedir;
  PowerPoint oynatma başlayana kadar posteri gösterir, böylece slayt dolu görünüp sonra boşalmaz. Video bitince
  son karede (tamamlanmış slaytta) kalır. Düzenleme görünümünde, PDF'te ve baskıda açılış karesi görünür.
- Orijinal şekiller videonun altında, düzenlenebilir hâlde kalır; konuşmacı notları korunur.
- Slaytların eski giriş animasyonları kaldırılır (video artık onları içerir), slayt geçişleri korunur.

## Sınırlar ve yol haritası

- Render için Windows ve masaüstü PowerPoint gerekir; macOS ve Linux'ta yalnızca `analyze` çalışır.
- Tablo hücrelerindeki sayılar saymaz (tablo satır satır açılır); tek başına duran sayılar odometreyle döner.
- Grafikler maskeyle açılır; serilerin tek tek gelmesi için grafiklerin veriden yeniden çizilmesi planlanıyor.
- Bugünkü motorda grafikler ve tablolar tek katman olarak maskeyle açılır, kamera hareketi ve slaytlar arası geçiş
  hâlâ kodda durur. Bunlar yeni kurallara aykırıdır ve `check` tarafından yakalanır; grafiklerin seri/eleman,
  tabloların satır/hücre katmanlarına ayrılması ve kameranın kaldırılması motorda yazılma aşamasındadır.
- Harf harf 3B dönüş ve ses tasarımı henüz yok.
- SmartArt ve gömülü Excel nesneleri tek parça açılır.
- Otomatik başlatma PowerPoint 2016+ içindir; Google Slides ve Keynote gömülü videoyu otomatik oynatmaz.
- Koreografi kataloğunun ve `moves` havuzlarının bir kısmı hareket motorunda yazılma aşamasındadır; motor tanımadığı
  bir hareketi yok sayar. `check` aynı biçimde açılan slaytları ve kamera hareketini yine yakalar.
- Planlananlar: PowerPoint'teki mevcut animasyon sırasını okuma, tıklama başına parça video, PDF girdisi.

---

## English summary

SlideReady animates an existing PowerPoint deck **without changing its layout**, with motion that is very hard to
build by hand: titles assemble from thousands of particles sampled from their own pixels, numbers roll like odometers
digit by digit, slides flow into each other like one continuous film, a depth camera pulls back through parallax
layers, light sweeps across panels, all with real motion blur. The user's own PowerPoint (Windows, COM) renders every
layer, so the last frame of each video equals the original slide. The agent decides the motion per slide on its own
(`style: "auto"` in `plan.json`) and explains its choices instead of asking up front. Videos are embedded back into a
copy of the deck (autoplay, no loop, first frame as poster). Run `scripts\setup.ps1`, then
`bin\slideready preview deck.pptx` and `bin\slideready export deck.pptx`. Works as a Claude Code skill (`SKILL.md`)
and with Codex (`AGENTS.md`). MIT licensed.
