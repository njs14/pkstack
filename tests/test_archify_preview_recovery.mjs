import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { EventEmitter } from 'node:events';
import fs from 'node:fs';
import path from 'node:path';
import { setTimeout } from 'node:timers/promises';
import { fileURLToPath } from 'node:url';
import { startPreview } from '../powers/pkstack/skills/archify/upstream/bin/preview.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const directory = path.resolve(process.argv[2]);
const input = path.join(directory, 'source.json');
const output = path.join(directory, 'preview.html');
const specification = JSON.parse(fs.readFileSync(path.join(here, '../powers/pkstack/skills/archify/upstream/examples/web-app.architecture.json'), 'utf8'));
fs.mkdirSync(directory, { recursive: true });
fs.writeFileSync(input, JSON.stringify(specification));

const originalWatch = fs.watch;
const watcher = new EventEmitter();
let watcherCloseCount = 0;
watcher.close = () => { watcherCloseCount += 1; };
fs.watch = () => watcher;
let preview;

async function waitForRevision(revision) {
  const deadline = Date.now() + 10000;
  while (Date.now() < deadline) {
    const state = preview.state();
    if (state.status === 'verified' && state.revision === revision) return state;
    assert.notEqual(state.status, 'needs-fix', JSON.stringify(state));
    await setTimeout(25);
  }
  assert.fail(`Preview did not verify revision ${revision}: ${JSON.stringify(preview.state())}`);
}

try {
  preview = await startPreview({ type: 'architecture', input, output, open: false, pollMs: 40, debounceMs: 20 });
  const initial = await waitForRevision(1);
  assert.doesNotThrow(() => watcher.emit('error', Object.assign(new Error('watch limit reached'), { code: 'EMFILE' })));
  assert.equal(watcherCloseCount, 1);

  specification.meta.title = 'Recovered using polling after watcher failure';
  fs.writeFileSync(input, JSON.stringify(specification));
  const recovered = await waitForRevision(2);
  const artifact = await (await fetch(new URL('/artifact.html', preview.url))).text();
  assert.match(artifact, /Recovered using polling after watcher failure/);
  assert.equal(createHash('sha256').update(artifact).digest('hex'), recovered.lastVerified.sha256);
  await preview.stop();
  assert.equal(watcherCloseCount, 1, 'Shutdown must not close the failed watcher again');
  await assert.rejects(fetch(preview.url));
  console.log(JSON.stringify({
    initialRevision: initial.revision,
    recoveredRevision: recovered.revision,
    initialArtifact: initial.lastVerified.sha256,
    recoveredArtifact: recovered.lastVerified.sha256,
    watcherCloseCount,
  }));
} finally {
  fs.watch = originalWatch;
  await preview?.stop();
}
