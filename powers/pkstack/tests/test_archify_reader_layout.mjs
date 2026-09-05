import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { ChromeVisualBrowser, findChrome, VISUAL_CHECK_VIEWPORTS } from '../skills/archify/upstream/bin/visual-check.mjs';

const tests = path.dirname(fileURLToPath(import.meta.url));
const runtime = path.resolve(tests, '../skills/archify/upstream');
const output = path.resolve(process.argv[2]);
const source = path.join(tests, 'fixtures/archify-account-request.sequence.json');
const chrome = findChrome();
if (!chrome) {
  console.log('Chrome unavailable; set ARCHIFY_CHROME to run the Archify browser regression.');
  process.exit(77);
}
fs.mkdirSync(output, { recursive: true });
const artifact = path.join(output, 'account.html');
const digest = (file) => createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const sourceHash = digest(source);
const observations = [];

function deliver(input, target) {
  const result = spawnSync(process.execPath, [path.join(runtime, 'bin/archify.mjs'),
    'deliver', 'sequence', input, target, '--quality', 'showcase', '--json'], { encoding: 'utf8' });
  assert.equal(result.status, 0, result.stdout + result.stderr);
  assert.equal(JSON.parse(result.stdout).validation.warnings, 0);
}
deliver(source, artifact);
const artifactHash = digest(artifact);
const browser = new ChromeVisualBrowser(chrome);
const session = await browser.sessionPromise;
async function evaluate(expression) {
  const response = await browser.cdp.send('Runtime.evaluate', {
    expression, awaitPromise: true, returnByValue: true,
  }, session, 30000);
  assert.equal(response.exceptionDetails, undefined, JSON.stringify(response.exceptionDetails));
  return response.result.value;
}
async function inspect(artifactPath, width, height, theme, name) {
  const metrics = await browser.inspect({ artifactPath, width, height, theme,
    screenshotPath: path.join(output, `${name}-${width}x${height}-${theme}.png`) });
  observations.push({ name, width, height, theme, ...metrics });
  assert.ok(metrics.scrollWidth <= width, JSON.stringify(metrics));
  const toolbar = await evaluate(`Array.from(document.querySelectorAll('.toolbar > button, .toolbar > div > button'))
    .filter(function (button) { return button.getBoundingClientRect().width > 0; })
    .map(function (button) { var r = button.getBoundingClientRect();
      return { id: button.id, left: r.left, right: r.right, top: r.top, bottom: r.bottom }; })`);
  for (const button of toolbar) {
    assert.ok(button.left >= 0 && button.right <= width && button.top >= 0 && button.bottom <= height,
      JSON.stringify({ width, height, button }));
  }
  if (width >= 1024) {
    assert.ok(metrics.scrollHeight <= height, JSON.stringify(metrics));
    assert.ok(metrics.minimumProjectedNodeTextPx >= 6, JSON.stringify(metrics));
    assert.ok(metrics.dockStageIntersectionArea <= 0.5, JSON.stringify(metrics));
    assert.ok(metrics.dockStageGap >= metrics.viewerChromeRequiredGap - 1, JSON.stringify(metrics));
  }
  return metrics;
}
async function download(format, directory) {
  fs.mkdirSync(directory, { recursive: true });
  await browser.cdp.send('Browser.setDownloadBehavior', { behavior: 'allow', downloadPath: directory });
  const receipt = await evaluate(`(async function () {
    document.querySelector('#btn-export').click();
    if (!Archify.exportMenu.isOpen()) throw new Error('Export menu did not open');
    var item = document.querySelector('#export-menu [data-format="${format}"]');
    if (!item || item.disabled) throw new Error('Export item unavailable: ${format}');
    item.click();
    for (var attempt = 0; attempt < 300; attempt += 1) {
      if (document.documentElement.hasAttribute('data-last-export-error')) {
        throw new Error(document.documentElement.getAttribute('data-last-export-error'));
      }
      if (document.documentElement.getAttribute('data-last-export-format') === '${format}') {
        return { format: '${format}', bytes: Number(document.documentElement.getAttribute('data-last-export-bytes')),
          canonical: document.documentElement.getAttribute('data-last-export-canonical') };
      }
      await new Promise(function (resolve) { setTimeout(resolve, 50); });
    }
    throw new Error('Export timed out: ${format}');
  })()`);
  assert.equal(receipt.canonical, 'true');
  assert.ok(receipt.bytes > 100);
  for (let attempt = 0; attempt < 100; attempt += 1) {
    const files = fs.readdirSync(directory).filter((file) => !file.endsWith('.crdownload'));
    if (files.length === 1 && fs.statSync(path.join(directory, files[0])).size === receipt.bytes) {
      return { ...receipt, file: path.join(directory, files[0]), sha256: digest(path.join(directory, files[0])) };
    }
    await new Promise((resolve) => setTimeout(resolve, 50));
  }
  throw new Error(`Download did not complete: ${format}`);
}

try {
  for (const { width, height } of VISUAL_CHECK_VIEWPORTS) {
    for (const theme of ['light', 'dark']) await inspect(artifact, width, height, theme, 'account');
  }
  for (const theme of ['light', 'dark']) {
    await inspect(artifact, 390, 844, theme, 'mobile');
    await inspect(artifact, 720, 900, theme, 'narrow');
  }
  // A valid wide variant exercises the unchanged wide-reader floor and path.
  const wide = JSON.parse(fs.readFileSync(source, 'utf8'));
  wide.meta.viewBox[0] = 1000;
  const wideSource = path.join(output, 'wide.json');
  fs.writeFileSync(wideSource, JSON.stringify(wide));
  const wideArtifact = path.join(output, 'wide.html');
  deliver(wideSource, wideArtifact);
  for (const theme of ['light', 'dark']) {
    const metrics = await inspect(wideArtifact, 1440, 900, theme, 'wide');
    assert.ok(metrics.readerWidth >= 960);
  }

  await inspect(artifact, 1440, 900, 'light', 'interaction');
  const geometry = await evaluate(`(function () {
    function box(node) { var b = node.getBBox(); return { x:b.x, y:b.y, width:b.width, height:b.height }; }
    return { captions: Array.from(document.querySelectorAll('[data-graph-role="segment-label"]')).map(box),
      participants: Array.from(document.querySelectorAll('[data-node-id] > rect.c-mask')).map(box),
      viewBox: document.querySelector('.diagram-container > svg').getAttribute('viewBox') };
  })()`);
  assert.equal(geometry.viewBox, '0 0 760 620');
  assert.equal(geometry.captions.length, 2);
  assert.equal(geometry.participants.length, 5);
  for (const label of geometry.captions) {
    assert.ok(label.y >= 0);
    for (const node of geometry.participants) {
      assert.ok(!(label.x < node.x + node.width && label.x + label.width > node.x
        && label.y < node.y + node.height && label.y + label.height > node.y), JSON.stringify({ label, node }));
    }
  }
  const baselineSvg = await download('svg', path.join(output, 'baseline-svg'));
  const zoomed = await evaluate(`(function () {
    for (var i = 0; i < 3; i += 1) document.querySelector('[data-view="in"]').click();
    var rect = document.querySelector('.diagram-container').getBoundingClientRect();
    return { camera: Archify.view.state(), x: rect.right - 80, y: rect.top + 280 };
  })()`);
  assert.equal(zoomed.camera.scale, 1.75);
  await browser.cdp.send('Input.dispatchMouseEvent', { type: 'mousePressed', x: zoomed.x, y: zoomed.y, button: 'left', clickCount: 1 }, session);
  await browser.cdp.send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: zoomed.x - 60, y: zoomed.y - 40, button: 'left', buttons: 1 }, session);
  await browser.cdp.send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: zoomed.x - 60, y: zoomed.y - 40, button: 'left', clickCount: 1 }, session);
  const panned = await evaluate('Archify.view.state()');
  assert.ok(panned.x !== zoomed.camera.x || panned.y !== zoomed.camera.y, JSON.stringify({ zoomed, panned }));

  const exports = [];
  for (const format of ['svg', 'png', 'jpeg', 'webp', 'share-card', 'webm']) {
    exports.push(await download(format, path.join(output, `export-${format}`)));
  }
  assert.equal(exports.find((item) => item.format === 'svg').sha256, baselineSvg.sha256,
    'Camera state changed the canonical SVG export');
  const svg = fs.readFileSync(baselineSvg.file, 'utf8');
  assert.match(svg, /viewBox="0 0 760 620"/);
  assert.match(svg, /prefers-color-scheme/);
  assert.match(svg, /message delivery \(not implemented here\)/);
  const png = fs.readFileSync(exports.find((item) => item.format === 'png').file);
  assert.equal(png.readUInt32BE(16), 760 * 4);
  assert.equal(png.readUInt32BE(20), 620 * 4);
  const share = fs.readFileSync(exports.find((item) => item.format === 'share-card').file);
  assert.equal(share.readUInt32BE(16), 1200);
  assert.equal(share.readUInt32BE(20), 630);
  const reset = await evaluate(`(function () {
    document.querySelector('[data-view="reset"]').click();
    return Archify.view.state();
  })()`);
  assert.deepEqual({ scale: reset.scale, x: reset.x, y: reset.y }, { scale: 1, x: 0, y: 0 });
  assert.equal(digest(source), sourceHash);
  assert.equal(digest(artifact), artifactHash, 'Browser checks mutated the delivered HTML');
  fs.writeFileSync(path.join(output, 'browser-evidence.json'), JSON.stringify({
    sourceHash, artifactHash, geometry, zoomed: zoomed.camera, panned, reset, observations, exports,
  }, null, 2) + '\n');
  console.log(JSON.stringify({ ok: true, viewports: observations.length, exports: exports.map((item) => item.format), evidence: output }));
} finally {
  await browser.close();
}
