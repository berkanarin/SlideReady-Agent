// SlideReady render: sahneleri (index.html + render(t)) kare kare çeker ve doğrudan ffmpeg'e boru ile verir.
// Kullanım: node render.cjs jobs.json   — jobs: [{dir, out, fps, width, height, crf, at?}]
//   at: verilirse video yerine yalnızca o anların PNG karelerini <dir>/still-<t>.png olarak yazar.
const fs = require('fs'), path = require('path'), { spawn } = require('child_process');
let chromium;
try { ({ chromium } = require('playwright')); } catch (e) {
  console.error('playwright bulunamadı: `npm install` (repo kökünde) çalıştırın.'); process.exit(2);
}
const jobs = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const conc = Math.max(1, +(process.env.SLIDEREADY_JOBS || 3));

async function run(browser, j) {
  const page = await browser.newPage({ viewport: { width: j.width, height: j.height } });
  await page.goto('file://' + path.resolve(j.dir, 'index.html'));
  await page.evaluate(() => Promise.all([document.fonts.ready, window.SR_READY]));
  const dur = await page.evaluate(() => DUR);
  if (j.at) {
    for (const t of j.at) {
      await page.evaluate(t => render(t), Math.min(t, dur));
      await page.screenshot({ path: path.join(j.dir, `still-${t}.png`) });
    }
    await page.close(); return { dir: j.dir, stills: j.at.length };
  }
  const n = Math.round(dur * j.fps);
  // Hareket bulanıklığı: her kare, 180° obtüratörle (kare süresinin yarısı) alınmış mb alt karenin ortalamasıdır.
  // Alt kareler yalnızca sahne hareket ederken çekilir; durağan anlarda aynı görüntü tekrarlanır (maliyetsiz).
  const mb = Math.max(1, j.mb || 1);
  const vf = mb > 1 ? ['-vf', `tmix=frames=${mb},select='eq(mod(n\\,${mb})\\,${mb - 1})',setpts=N/(${j.fps}*TB)`] : [];
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(j.fps * mb), '-i', '-',
    ...vf, '-r', String(j.fps), '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', String(j.crf || 18),
    '-preset', j.preset || 'medium', '-movflags', '+faststart', j.out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const done = new Promise((ok, bad) => ff.on('close', c => c === 0 ? ok() : bad(new Error('ffmpeg ' + c))));
  const put = async buf => { if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r)); };
  for (let i = 0; i < n; i++) {
    const t = i / j.fps;
    const moving = mb > 1 && await page.evaluate(t => !window.SR_MOVING || window.SR_MOVING(t), t);
    if (!moving) {
      await page.evaluate(t => render(t), t);
      const buf = await page.screenshot({ type: 'jpeg', quality: 95 });
      for (let s = 0; s < mb; s++) await put(buf);
      continue;
    }
    for (let s = mb - 1; s >= 0; s--) {         // t'ye biten yarım kare aralığı: t - (dt/2)·s/(mb-1)
      await page.evaluate(t => render(t), Math.max(0, t - (0.5 / j.fps) * s / (mb - 1)));
      await put(await page.screenshot({ type: 'jpeg', quality: 95 }));
    }
  }
  ff.stdin.end(); await done; await page.close();
  return { out: j.out, frames: n, duration: dur };
}

(async () => {
  // katman PNG'leri WebGL dokusu olarak okunabilsin (file:// sayfaları aynı köken sayılır)
  const browser = await chromium.launch({ args: ['--allow-file-access-from-files', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  const queue = [...jobs], results = [];
  await Promise.all(Array.from({ length: Math.min(conc, jobs.length) }, async () => {
    while (queue.length) { const j = queue.shift(); results.push(await run(browser, j)); console.error('✓ ' + (j.out || j.dir)); }
  }));
  await browser.close();
  console.log(JSON.stringify(results));
})().catch(e => { console.error(e); process.exit(1); });
