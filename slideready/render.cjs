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
  await page.evaluate(() => document.fonts.ready);
  const dur = await page.evaluate(() => DUR);
  if (j.at) {
    for (const t of j.at) {
      await page.evaluate(t => render(t), Math.min(t, dur));
      await page.screenshot({ path: path.join(j.dir, `still-${t}.png`) });
    }
    await page.close(); return { dir: j.dir, stills: j.at.length };
  }
  const n = Math.round(dur * j.fps);
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(j.fps), '-i', '-',
    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', String(j.crf || 18), '-preset', j.preset || 'medium',
    '-movflags', '+faststart', j.out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const done = new Promise((ok, bad) => ff.on('close', c => c === 0 ? ok() : bad(new Error('ffmpeg ' + c))));
  for (let i = 0; i < n; i++) {
    await page.evaluate(t => render(t), i / j.fps);
    const buf = await page.screenshot({ type: 'jpeg', quality: 95 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
  }
  ff.stdin.end(); await done; await page.close();
  return { out: j.out, frames: n, duration: dur };
}

(async () => {
  const browser = await chromium.launch();
  const queue = [...jobs], results = [];
  await Promise.all(Array.from({ length: Math.min(conc, jobs.length) }, async () => {
    while (queue.length) { const j = queue.shift(); results.push(await run(browser, j)); console.error('✓ ' + (j.out || j.dir)); }
  }));
  await browser.close();
  console.log(JSON.stringify(results));
})().catch(e => { console.error(e); process.exit(1); });
