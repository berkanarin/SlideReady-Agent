# SlideReady

Bu repo bir Claude skill'idir: **[SKILL.md](SKILL.md)** iş akışını tanımlar ve her PPTX işinde onu izle.
Ajan talimatlarının özeti ve geliştirme notları [AGENTS.md](AGENTS.md) dosyasındadır.

- Kullanıcı "kur" / "repoyu anla" derse: `bin/slideready doctor`, eksik varsa `bash scripts/setup.sh`.
- Kullanıcı bir PPTX verirse: SKILL.md'deki sırayla `analyze` → Yönetmen (`.claude/agents/slideready-director.md`)
  → `preview` → `check` → onay → `export` → `check`.
- Kontrol için `.claude/agents/slideready-reviewer.md` alt ajanı kullanılır; "TESLİM ETME" diyen sonuç gösterilmez.
- Kullanıcı "bir şey üretme" derse render başlatma.
