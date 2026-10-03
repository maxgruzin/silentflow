// Optional browser regression checks; Playwright is a development-only tool.
const assert = require('node:assert/strict');
const {chromium} = require(require.resolve('playwright', {paths: [process.cwd(), `${process.cwd()}/artifacts/browser`]}));
const base = process.env.SF_TEST_URL || 'http://127.0.0.1:8000';
const releasePath = process.env.SF_TEST_RELEASE || '/release/in-vitro-energeia/';

// A short local fixture exercises real browser audio events without repeatedly
// downloading full albums. One separate check below uses the actual MP3.
function wav() {
    const rate = 8000, samples = rate * 30;
    const buffer = Buffer.alloc(44 + samples * 2);
    buffer.write('RIFF'); buffer.writeUInt32LE(buffer.length - 8, 4);
    buffer.write('WAVEfmt ', 8); buffer.writeUInt32LE(16, 16);
    buffer.writeUInt16LE(1, 20); buffer.writeUInt16LE(1, 22);
    buffer.writeUInt32LE(rate, 24); buffer.writeUInt32LE(rate * 2, 28);
    buffer.writeUInt16LE(2, 32); buffer.writeUInt16LE(16, 34);
    buffer.write('data', 36); buffer.writeUInt32LE(samples * 2, 40);
    return buffer;
}

async function playing(page) {
    await page.waitForFunction(() => {
        const audio = document.querySelector('#release-audio');
        return !audio.paused && audio.currentTime > .05;
    });
}
async function selected(page, position) {
    await page.waitForFunction(position => document.querySelector('.player-count').textContent.startsWith(`${position} /`), position);
}
async function endTrack(page) {
    await playing(page);
    await page.locator('audio').evaluate(audio => { audio.currentTime = audio.duration - .15; });
}

(async () => {
    const browser = await chromium.launch({channel: process.env.SF_TEST_BROWSER || 'msedge', headless: true});
    try {
        for (const width of [1440, 390, 320]) {
            const page = await browser.newPage({viewport: {width, height: 900}});
            const errors = [];
            page.on('pageerror', error => errors.push(error.message));
            let requests = 0, failAudio = false;
            await page.route('**/media/track_mp3/**', route => {
                requests++;
                if (failAudio) return route.fulfill({status: 503, body: 'Unavailable'});
                const body = wav();
                const range = route.request().headers().range?.match(/^bytes=(\d+)-(\d*)$/);
                const start = range ? Number(range[1]) : 0;
                const end = range && range[2] ? Math.min(Number(range[2]), body.length - 1) : body.length - 1;
                const headers = {'Accept-Ranges': 'bytes'};
                if (range) headers['Content-Range'] = `bytes ${start}-${end}/${body.length}`;
                return route.fulfill({status: range ? 206 : 200, contentType: 'audio/wav', headers, body: body.subarray(start, end + 1)});
            });
            await page.goto(base + releasePath, {waitUntil: 'networkidle'});
            assert.equal(requests, 0, 'No audio downloads before pressing play');
            assert.equal(await page.locator('audio').count(), 1);
            assert.equal(await page.locator('audio[controls]').count(), 0);
            const tracks = page.locator('.track-toggle');
            const count = await tracks.count();
            assert(count >= 3, 'Choose a release with at least three playable tracks');
            await tracks.first().click();
            await playing(page);
            await selected(page, 1);
            assert.match(await page.locator('.player-remaining').innerText(), /^-00:/);
            const bounds = await page.locator('.music-player').boundingBox();
            assert(Math.abs(bounds.y + bounds.height - 900) < 2, 'Player is fixed to bottom');
            assert(bounds.x >= 0 && bounds.x + bounds.width <= width, 'Player fits viewport');

            await page.locator('.player-toggle').click();
            assert(await page.locator('audio').evaluate(audio => audio.paused));
            assert.equal(await tracks.first().getAttribute('aria-pressed'), 'false');
            const slider = page.locator('.player-seek');
            const sliderBounds = await slider.boundingBox();
            await slider.click({position: {x: sliderBounds.width / 2, y: sliderBounds.height / 2}});
            assert(await page.locator('audio').evaluate(audio => audio.currentTime > 10 && audio.currentTime < 20));
            await slider.press('ArrowRight');
            assert.match(await slider.getAttribute('aria-valuetext'), /of 00:30/);
            await page.locator('.player-next').click();
            await selected(page, 2);
            await playing(page);
            await page.locator('.player-previous').click();
            await selected(page, 1);

            // Real ended events: advance, repeat all, repeat one, and stop.
            await endTrack(page);
            await selected(page, 2);
            await page.locator('.player-repeat').click();
            await tracks.last().click();
            await endTrack(page);
            await selected(page, 1);
            await page.locator('.player-repeat').click();
            await endTrack(page);
            await page.waitForFunction(() => document.querySelector('audio').currentTime < 2 && !document.querySelector('audio').paused);
            await selected(page, 1);
            await page.locator('.player-repeat').click();
            await tracks.last().click();
            await endTrack(page);
            await page.waitForFunction(() => document.querySelector('audio').ended && document.querySelector('audio').paused);
            await selected(page, count);

            await tracks.first().click();
            await page.locator('.player-shuffle').click();
            const seen = new Set([1]);
            for (let index = 1; index < count; index++) {
                await page.locator('.player-next').click();
                const position = Number((await page.locator('.player-count').innerText()).split('/')[0]);
                assert(!seen.has(position), 'Shuffle visits every track before repeating');
                seen.add(position);
            }
            await page.locator('.player-close').click();
            assert(await page.locator('.music-player').isHidden());
            assert(await page.locator('audio').evaluate(audio => audio.paused && !audio.hasAttribute('src')));
            assert(await tracks.first().evaluate(button => button === document.activeElement));

            // Fast switching/closing must not allow a pending play promise to restart audio.
            await page.evaluate(() => {
                const buttons = document.querySelectorAll('.track-toggle');
                buttons[0].click(); buttons[1].click();
                document.querySelector('.player-close').click();
            });
            await page.waitForTimeout(150);
            assert(await page.locator('audio').evaluate(audio => audio.paused));
            failAudio = true;
            await tracks.first().click();
            await page.waitForFunction(() => /could not be loaded/.test(document.querySelector('.player-status').textContent));
            failAudio = false;
            await page.locator('.player-toggle').click();
            await playing(page);
            await page.locator('.player-close').click();
            assert.deepEqual(errors, []);
            console.log(`Player interactions passed at ${width}px`);
            await page.close();
        }
        const real = await browser.newPage();
        await real.goto(base + releasePath);
        await real.locator('.track-toggle').first().click();
        await playing(real);
        await real.locator('.player-toggle').click();
        const realSlider = real.locator('.player-seek');
        const realBounds = await realSlider.boundingBox();
        await realSlider.click({position: {x: realBounds.width / 2, y: realBounds.height / 2}});
        await real.waitForFunction(() => {
            const audio = document.querySelector('audio');
            return audio.currentTime > audio.duration * .4 && audio.currentTime < audio.duration * .6;
        });
        await real.locator('.player-toggle').click();
        await playing(real);
        console.log('Actual catalogue MP3 playback and seeking passed');
        await real.close();
        const noJS = await browser.newPage({javaScriptEnabled: false});
        await noJS.goto(base + releasePath);
        assert(await noJS.locator('.track-row noscript a').first().isVisible());
        await noJS.locator('.site-menu summary').click();
        assert(await noJS.locator('.site-menu nav').isVisible());
        console.log('No-JS audio links and menu passed');
    } finally {
        await browser.close();
    }
})().catch(error => { console.error(error); process.exit(1); });
