# SlideReady — talimatlar (Codex ve diğer ajanlar)

Bu repo, PowerPoint sunumlarını (PPTX) tasarımı bozmadan canlandıran **SlideReady** aracıdır.
Tam iş akışı, roller, `plan.json` alanları ve kontrol listesi **[SKILL.md](SKILL.md)** dosyasındadır; her işe
başlamadan önce onu oku ve adım adım uygula.

## Kullanıcı ne der, sen ne yaparsın

| Kullanıcı | Sen |
|---|---|
| "Repoyu anla", "kur", "hazırla" | `bin/slideready doctor` → eksik varsa `scripts\setup.ps1` (Windows + PowerPoint gerekir) → tekrar `doctor`. Sonuç: "Hazır, PPTX'ini gönderebilirsin." |
| "Şu PPTX'i işle" | `bin/slideready analyze X.pptx` → gerekirse `X.slideready/plan.json`'u düzenle → `bin/slideready preview X.pptx` → önizleme videolarını ve kısa özeti göster, onay iste |
| "Tamam" / "çıktı al" | `bin/slideready export X.pptx` → `X-SlideReady.pptx` ve kısa rapor |
| "2. slayt yavaş olsun", "logoyu oynatma" | `plan.json`'da `tempo` / `static` / `animate` → ilgili slaytı yeniden `preview --slides N` |

## Değişmez kurallar

- Slaytı yeniden çizme, koordinat uydurma, sahne HTML'ini elle yazma. Ayar yalnızca `plan.json` ile yapılır.
- Başta soru sorma: tarzı, tempoyu ve neyin öne çıkacağını `analyze`'ın kararı (`style: "auto"`) belirler. Önizlemeyle
  birlikte tek kısa paragrafta slayt başına neyi neden seçtiğini söyle; kullanıcı bir cümleyle değiştirir. Yalnızca
  sonucu değiştiren gerçek bir belirsizlikte (ör. yer tutucu metin) sor.
- Önce önizleme (en fazla 1–2 slayt, düşük kalite), sonra onay, sonra tam çıktı.
- Çıktı PPTX'tir; videolar otomatik başlar, döngü yoktur.
- Veriyi değiştirme ya da uydurma; sunum dosyasını dışarı gönderme, her şey yerelde çalışır.
- Kullanıcıyla onun dilinde, kısa konuş; doğrulayamadığın şeyi (ör. gerçek PowerPoint'te oynatma) açıkça söyle.

## Geliştirme

- Kod: `slideready/` (Python CLI) + `slideready/pptrender.py` (PowerPoint COM ile katmanlar) +
  `slideready/render.cjs` (Playwright) + `slideready/scene.html` (hareket dili).
- Test: `python -m unittest discover tests` (PowerPoint gerektiren testler Windows dışında atlanır); uçtan uca:
  `bin/slideready preview examples/demo.pptx`.
- Örnek deste `examples/make_demo.py` ile üretilir; içerik kurgusaldır. Repoya gerçek kurum sunumu, logosu ya da
  verisi eklenmez.
