# SlideReady Agent

**PowerPoint sunumunu bozmadan canlandırır.** Her slayt kendi şekilleriyle katman katman açılır ve PowerPoint'in kendi
efektleriyle yapılamayan bir hareket diliyle oynar: kamera başlığın üstünden geri çekilirken arka plan, paneller ve
içerik farklı derinlikte kayar; öğeler bulanıktan netleşir; başlık kelime kelime, metin satır satır açılır; panellerin
üstünden ışık geçer; sayılar sayıp yerine oturunca parlar; grafikler dönerek ya da büyüyerek, tablolar satır satır gelir. Videonun son karesi orijinal slaytın ta kendisidir.
Çıktı yine **PPTX**'tir: her slaytta kendi videosu, otomatik başlar, döngü yoktur.

![SlideReady örnek çıktı](docs/demo.gif)

*Yukarıdaki animasyon, repodaki kurgusal `examples/demo.pptx` dosyasından hiçbir elle ayar yapılmadan üretildi.*

Claude (Claude Code skill'i) ve Codex (AGENTS.md) ile ajan olarak çalışır; tek başına komut satırı aracı olarak da
kullanılabilir.

## Kullanıcı olarak üç adım

Repoyu Claude Code ya da Codex'te açın ve şunları yazın:

1. **"Repoyu kur."** Ajan gerekli araçları kontrol eder ve eksikleri kurar.
2. **"Şu PPTX'i işle."** (dosyayı ekleyin) Ajan sunumu çözümler, hangi slaytların nasıl canlanacağını özetler ve
   en zengin 1–2 slaytın hızlı önizlemesini gösterir.
3. **"Tamam, çıktı al."** Ajan bütün slaytları render eder ve `SUNUM-SlideReady.pptx` dosyasını verir.

Değişiklik isterseniz tek cümle yeterli: "3. slayt daha yavaş olsun", "logoyu hareket ettirme", "kapak sabit kalsın".

## Neyi nasıl canlandırır

| Öğe | Hareket |
|---|---|
| Başlık | Yukarı kayarak belirir |
| Panel / kutu | Hafifçe büyüyerek gelir; içindekiler ardından sırayla açılır |
| Sayı (₺12,4M, %38, 1.250, 9 gün) | 0'dan sayar; ön ek, son ek ve Türkçe sayı biçimi korunur |
| Pasta / halka grafik | Saat 12'den saat yönünde açılır |
| Sütun grafik | Eksenden yukarı büyür |
| Çubuk ve çizgi grafik | Soldan sağa açılır |
| Tablo | Satır satır açılır, sayı hücreleri sayar |
| İkon, ok, dekor | Küçük bir sıçramayla gelir |
| Metin | Hafifçe yükselerek belirir |
| Gruplar | İçindeki şekiller okuma sırasıyla gelir |
| GIF ve video (slaytta, düzende ya da asıl slaytta) | Kendi kareleriyle oynar; arka plan videosu verilerle tek bütündür |
| Resim olarak konmuş metin/şekil (ekran görüntüsü) | Düz zeminliyse blok blok, okuma sırasıyla açılır |

Okunabilirlik kuralları: metin hiçbir zaman hareketli bir görselin üstünden geçmez, her slaytın sonunda en az
2 saniye durağan okuma payı vardır (metin arttıkça uzar), arka plan yalnızca çok hafif yakınlaşır.

## Nasıl çalışır

```
PPTX ──python-pptx──▶ şekil envanteri (tür, metin, grafik verisi, tablo, şekil kimliği)
  │                                    │  aynı şekil kimliği
  └──PowerPoint (COM)──▶ arka plan + şekil başına saydam katman (gölge, parlama dahil)
                                       ▼
                     koreografi (plan.json ile ayarlanır)
                                       ▼
             HTML sahnesi, render(t) ──Playwright──▶ kareler ──ffmpeg──▶ MP4
                                       ▼
                 orijinal PPTX + slayt başına video (otomatik, döngüsüz)
```

- Model koordinat üretmez; yerleşim her zaman dosyadan gelir. Ajanın tek ayar kolu `plan.json`'dur.
- Görüntüyü kullanıcının kendi PowerPoint'i çizer: fontlar, efektler ve arka plan görselleri PowerPoint'te nasıl
  görünüyorsa öyledir. Her şekil yalnızca kendisi görünürken bir kez beyaz, bir kez siyah zeminde dışa aktarılır; iki
  karenin farkından tam saydamlık çıkar. Katmanlar üst üste konunca PowerPoint'in kendi slayt görüntüsüyle karşılaştırılır
  (`layers/NNN/layers.json` → `fidelity`); hareketin son karesi PowerPoint'in çizdiğiyle aynıdır.
- Sayaçlar için PowerPoint sayının ara değerlerini de çizer (metin geçici olarak değiştirilir; dosya kaydedilmez).
- Her şey yerelde çalışır; sunum hiçbir servise gönderilmez.

## Kurulum

Gerekenler: Windows ve masaüstü Microsoft PowerPoint, Python 3.9+ (pywin32 ile), ffmpeg, Node.js 18+ ve Playwright
Chromium. PowerPoint olmayan bir makinede `analyze` çalışır, `preview`/`export` çalışmaz.

```bash
git clone https://github.com/berkanarin/SlideReady-Agent.git
cd SlideReady-Agent
bash scripts/setup.sh          # Windows: powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
bin/slideready doctor          # her şey ✓ olmalı
```

Elle kurmak isterseniz: `pip install -r requirements.txt`, `npm install`, `npx playwright install chromium`, ayrıca
ffmpeg (`winget install Gyan.FFmpeg`).

### Claude'a skill olarak eklemek

- **Claude Code:** repoyu açmanız yeterli (`CLAUDE.md` ve `SKILL.md` otomatik okunur). Her projede kullanmak için
  repoyu `~/.claude/skills/slideready/` olarak klonlayın.
- **Codex:** repoyu açın; `AGENTS.md` otomatik okunur.

## Komut satırı

```bash
bin/slideready analyze  sunum.pptx                 # çözümleme + sunum.slideready/plan.json
bin/slideready preview  sunum.pptx                 # en zengin 2 slayt, 960×540, birkaç saniye
bin/slideready preview  sunum.pptx --slides 3,7    # belirli slaytlar
bin/slideready export   sunum.pptx                 # tüm slaytlar, 1080p 60 fps → sunum-SlideReady.pptx
bin/slideready export   sunum.pptx --quality 720   # daha küçük dosya
```

`plan.json` slayt başına şu alanları içerir:

| Alan | Anlamı |
|---|---|
| `animate` | `false`: slayt sabit kalır, video eklenmez |
| `style` | `sinematik` (varsayılan: kamera, derinlik, odak çekme, kelime/satır metin, ışık süzmesi), `sakin`, `enerjik` |
| `tempo` | 1.0 normal, 0.8 sakin, 1.2 hızlı (tarzın kendi temposuyla çarpılır) |
| `hold` | Son hareketten sonraki okuma payı (sn, en az 2) |
| `static` | Hareket etmemesi gereken şekil adları (logo, dipnot…) |

Örnek: `examples/demo.pptx` üzerinde önizleme yaklaşık 15 saniye, 4 slaytlık 1080p60 çıktı yaklaşık 75 saniye sürdü.

## Çıktı PPTX

- Orijinal sunumun kopyasıdır; videolar canlandırılan her slaytın en üst katmanına tam ekran yerleşir.
- Video slayt açılınca **otomatik başlar, döngü yoktur.** Döngü isterseniz PowerPoint'te videoyu seçip
  Oynatma > "Durdurulana kadar döngü"yü işaretleyin.
- Poster karesi videonun ilk karesidir: PowerPoint oynatma başlayana kadar posteri gösterir, böylece slayt dolu görünüp
  sonra boşalmaz. Video bitince son karede (tamamlanmış slaytta) kalır. Düzenleme görünümünde, PDF'te ve baskıda
  açılış karesi görünür.
- Orijinal şekiller videonun altında, düzenlenebilir hâlde kalır; konuşmacı notları korunur.
- Slaytların eski giriş animasyonları kaldırılır (video artık onları içerir), slayt geçişleri korunur.

## Sınırlar ve yol haritası

- Grafikler şu an maskeyle açılır; serilerin tek tek gelmesi için grafiklerin veriden yeniden çizilmesi planlanıyor.
- Sistemde olmayan fontlar benzeriyle değiştirilir (`analyze` uyarır).
- SmartArt ve gömülü Excel nesneleri tek parça açılır.
- Otomatik başlatma PowerPoint 2016+ içindir; Google Slides ve Keynote gömülü videoyu otomatik oynatmaz.
- Planlananlar: PowerPoint'teki mevcut animasyon sırasını okuma, tıklama başına parça video, PDF girdisi,
  hareket ön ayarları.

---

## English summary

SlideReady animates an existing PowerPoint deck **without changing its layout**. Each slide's own shapes are
revealed layer by layer (counters for numbers, chart and table reveals), the last frame equals the original slide,
and the videos are embedded back into a copy of the deck (autoplay, no loop, last frame as poster).
Run `bash scripts/setup.sh`, then `bin/slideready preview deck.pptx` and `bin/slideready export deck.pptx`.
Works as a Claude Code skill (`SKILL.md`) and with Codex (`AGENTS.md`). MIT licensed.
