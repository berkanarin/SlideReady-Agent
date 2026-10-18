# SlideReady — talimatlar (Codex ve diğer ajanlar)

Bu repo, PowerPoint sunumlarını (PPTX) tasarımı bozmadan canlandıran **SlideReady** aracıdır.
Tam iş akışı, roller, `plan.json` alanları ve kontrol listesi **[SKILL.md](SKILL.md)** dosyasındadır; her işe
başlamadan önce onu oku ve adım adım uygula.

## Kullanıcı ne der, sen ne yaparsın

| Kullanıcı | Sen |
|---|---|
| "Repoyu anla", "kur", "hazırla" | `bin/slideready doctor` → eksik varsa `scripts\setup.ps1` (Windows + PowerPoint gerekir) → tekrar `doctor`. Sonuç: "Hazır, PPTX'ini gönderebilirsin." |
| "Şu PPTX'i işle" | `bin/slideready analyze X.pptx` → **Yönetmen**: `references/motion.md`'ye göre her slayta tekrarsız `hero` yaz → `bin/slideready preview X.pptx` → `check` temizse önizleme videolarını ve slayt başına koreografi tablosunu göster, onay iste |
| "Tamam" / "çıktı al" | `bin/slideready export X.pptx` → `check` temizse `X-SlideReady.pptx` ve kısa rapor |
| "Bir şey üretme", "dur" | Render başlatma; yalnızca istenen işi yap |
| "2. slayt yavaş olsun", "logoyu oynatma" | `plan.json`'da `tempo` / `static` / `animate` → ilgili slaytı yeniden `preview --slides N` |

## Değişmez kurallar

- **Her klibin ilk karesi boştur:** yalnızca slaytın arka planı görünür, içerik ya da önceki slayttan kalıntı olmaz;
  poster de bu karedir. Teslimden önce her videonun ilk karesini çıkarıp bak.
- **Efektler tekrar etmez:** sunum tek film olarak planlanır; her slaytın kahraman efekti, kamerası, giriş yönü ve
  ritmi farklıdır. "Hepsi aynı" bir çıktı teslim edilmez.
- **Geçişte kare kaçmaz:** boş açılış en az 0,3 sn sürer; kare sayısı süre × fps'e eşittir, eksik ya da donan kare
  olmaz. Slayt sınırlarındaki kareler teslimden önce kontrol edilir.

- Slaytı yeniden çizme, koordinat uydurma, sahne HTML'ini elle yazma. Ayar yalnızca `plan.json` ile yapılır.
- Başta soru sorma: tarzı, tempoyu ve neyin öne çıkacağını `analyze`'ın kararı (`style: "auto"`) belirler. Önizlemeyle
  birlikte tek kısa paragrafta slayt başına neyi neden seçtiğini söyle; kullanıcı bir cümleyle değiştirir. Yalnızca
  sonucu değiştiren gerçek bir belirsizlikte (ör. yer tutucu metin) sor.
- Önce önizleme (en fazla 1–2 slayt, düşük kalite), sonra onay, sonra tam çıktı.
- `bin/slideready check` "TESLİM ETME" diyorsa sonucu kullanıcıya gösterme: düzelt, sorunlu slaytları yeniden render
  et, yeniden denetle.
- Çıktı PPTX'tir; videolar otomatik başlar, döngü yoktur.
- Veriyi değiştirme ya da uydurma; sunum dosyasını dışarı gönderme, her şey yerelde çalışır.
- Kullanıcıyla onun dilinde, kısa konuş; doğrulayamadığın şeyi (ör. gerçek PowerPoint'te oynatma) açıkça söyle.

## Geliştirme

- Kod: `slideready/` (Python CLI) + `slideready/pptrender.py` (PowerPoint COM ile katmanlar) +
  `slideready/render.cjs` (Playwright) + `slideready/scene.html` ve `fx.js` (hareket dili) +
  `slideready/qa.py` (değişmez kuralların ölçümü, `slideready check`).
- Hareket dili ve koreografi kataloğu `references/motion.md`'dedir; motora yeni bir koreografi eklerken adını oradaki
  `hero` adıyla aynı tut.
- Test: `python -m unittest discover tests` (PowerPoint gerektiren testler Windows dışında atlanır); uçtan uca:
  `bin/slideready preview examples/demo.pptx`.
- Örnek deste `examples/make_demo.py` ile üretilir; içerik kurgusaldır. Repoya gerçek kurum sunumu, logosu ya da
  verisi eklenmez.
