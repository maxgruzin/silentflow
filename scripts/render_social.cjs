// Optional design tool: regenerate the static social card with the site's own assets.
// Uses the same development-only Playwright installation as test_player.cjs.
const { chromium } = require('../artifacts/browser/node_modules/playwright');
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const asset = (name, mime) => `data:${mime};base64,${fs.readFileSync(path.join(root, 'static', name)).toString('base64')}`;

(async () => {
  const browser = await chromium.launch({ channel: process.env.SF_TEST_BROWSER || 'msedge' });
  try {
    const page = await browser.newPage({ viewport: { width: 1200, height: 630 }, deviceScaleFactor: 1 });
    await page.setContent(`<!doctype html><html lang="en"><meta charset="utf-8"><style>
      @font-face{font-family:Archivo;src:url('${asset('fonts/archivo/archivo-latin.woff2', 'font/woff2')}');font-weight:100 900}
      *{box-sizing:border-box}body{margin:0;background:#131313;color:#f4f4f4;font-family:Archivo,sans-serif}
      main{position:relative;width:1200px;height:630px;overflow:hidden;padding:86px 80px;display:flex;flex-direction:column;justify-content:center}
      .circle{position:absolute;width:580px;height:580px;right:-100px;top:0;border-radius:50%;background:#343a42;border:1px solid #56616e;box-shadow:0 0 0 65px #40485433,0 0 0 130px #40485422}
      .circle.second{width:390px;height:390px;right:230px;top:320px;background:#353535bb;border-color:#62626255;box-shadow:0 0 0 55px #65656511}
      img{position:absolute;width:230px;height:230px;right:105px;top:175px;object-fit:contain}
      h1,p{position:relative;margin:0;max-width:680px}h1{font-size:90px;font-weight:900;letter-spacing:-4px;line-height:1.08}
      .genres{font-size:26px;line-height:1.5;margin-top:30px;color:#d3d7dd}
      .note{font-size:23px;margin-top:10px;color:#aeb4bd}.url{position:absolute;bottom:54px;font-size:19px;color:#aeb4bd;letter-spacing:1px}
    </style><main><div class="circle"></div><div class="circle second"></div><img src="${asset('images/sf/logo.png', 'image/png')}" alt="">
      <h1>Silent Flow</h1><p class="genres">Ambient · Experimental · Jazz</p><p class="note">Independent sounds. Freely shared.</p><p class="url">silentflow.org</p></main></html>`);
    await page.evaluate(async () => {
      await document.fonts.ready;
      await Promise.all([...document.images].map(image => image.decode()));
    });
    const output = path.join(root, 'static/images/social-default.png');
    await page.screenshot({ path: output });
    console.log(`Generated ${output} (${fs.statSync(output).size} bytes)`);
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
