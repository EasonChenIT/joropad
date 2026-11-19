// usage: node shot.js <dir served at http://127.0.0.1:PORT/> <port> <out.png>
const { chromium } = require('playwright');
(async () => {
  const [port, out] = process.argv.slice(2);
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  const p = await b.newPage({ viewport: { width: 1600, height: 1000 } });
  p.on('console', m => { if (m.type() === 'error') console.error('page:', m.text()); });
  await p.goto(`http://127.0.0.1:${port}/viewer.html`);
  await p.waitForFunction('window.done === true', null, { timeout: 180000 });
  const el = await p.$('canvas');
  await el.screenshot({ path: out });
  await b.close();
})();
