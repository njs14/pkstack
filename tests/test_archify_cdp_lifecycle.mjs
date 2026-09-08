import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { EventEmitter } from 'node:events';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { PassThrough, Writable } from 'node:stream';
import test from 'node:test';
import { ChromeVisualBrowser } from '../powers/pkstack/skills/archify/upstream/bin/visual-check.mjs';

async function bounded(promise) {
  let timer;
  try {
    return await Promise.race([
      promise,
      new Promise((_, reject) => {
        timer = setTimeout(() => reject(new Error('Known terminal failure remained pending')), 2000);
      }),
    ]);
  } finally {
    clearTimeout(timer);
  }
}

function protocolChild() {
  const child = new EventEmitter();
  child.exitCode = null;
  child.signalCode = null;
  child.stderr = new PassThrough();
  const read = new PassThrough();
  child.commands = [];
  const write = new Writable({
    write(chunk, _encoding, done) {
      const request = JSON.parse(chunk.toString().replace(/\0$/, ''));
      child.commands.push(request.method);
      if (request.method !== 'Test.silent') {
        const results = {
          'Target.getTargets': { targetInfos: [{ type: 'page', targetId: 'page' }] },
          'Target.attachToTarget': { sessionId: 'session' },
        };
        const response = request.method === 'Test.error'
          ? { id: request.id, error: { message: 'ordinary request rejection' } }
          : { id: request.id, result: results[request.method] || {} };
        queueMicrotask(() => read.write(`${JSON.stringify(response)}\0`));
      }
      done();
    },
  });
  child.stdio = [null, null, child.stderr, write, read];
  child.kill = (signal) => {
    child.signalCode = signal;
    queueMicrotask(() => {
      child.emit('exit', null, signal);
      child.emit('close', null, signal);
    });
    return true;
  };
  return child;
}

test('read EOF rejects startup while the real child is still alive', async () => {
  const browser = new ChromeVisualBrowser(process.execPath, {
    spawnImpl: (command, _args, options) => spawn(command, ['-e', `
      const fs = require('node:fs');
      process.stderr.write('injected read EOF\\n');
      fs.closeSync(4);
      setInterval(() => {}, 1000);
    `], options),
  });
  try {
    await assert.rejects(bounded(browser.sessionPromise), /Chrome DevTools read pipe failed/);
    assert.equal(browser.child.exitCode, null);
    assert.equal(browser.child.signalCode, null);
  } finally {
    await browser.close();
    assert.equal(fs.existsSync(browser.profileRoot), false);
  }
});

test('real child exit rejects startup before inherited pipes close', async () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'archify-cdp-holder-'));
  const holderRecord = path.join(root, 'holder.json');
  const holderTerminated = path.join(root, 'terminated');
  const holderCode = `
    const fs = require('node:fs');
    process.on('SIGTERM', () => {
      fs.writeFileSync(process.env.HOLDER_TERMINATED, 'SIGTERM');
      process.exit(0);
    });
    process.send('ready');
    setInterval(() => {}, 1000);
  `;
  let pipeEnded = false;
  let childClosed = false;
  const browser = new ChromeVisualBrowser(process.execPath, {
    spawnImpl: (command, _args, options) => {
      const child = spawn(command, ['-e', `
        const fs = require('node:fs');
        const { spawn } = require('node:child_process');
        const holder = spawn(process.execPath, ['-e', ${JSON.stringify(holderCode)}], {
          stdio: ['ignore', 'ignore', 2, 3, 4, 'ipc'],
        });
        holder.once('message', () => {
          fs.writeFileSync(process.env.HOLDER_RECORD, JSON.stringify({ pid: holder.pid }));
          process.stderr.write('injected fatal exit 42\\n');
          process.exit(42);
        });
      `], { ...options, env: { ...process.env, HOLDER_RECORD: holderRecord, HOLDER_TERMINATED: holderTerminated } });
      child.stdio[4].on('end', () => { pipeEnded = true; });
      child.on('close', () => { childClosed = true; });
      return child;
    },
  });
  try {
    await assert.rejects(bounded(browser.sessionPromise), /Chrome DevTools process exit failed.*exit code 42/s);
    assert.equal(browser.child.exitCode, 42);
    assert.equal(pipeEnded, false);
    assert.equal(childClosed, false);
  } finally {
    await browser.close();
    if (fs.existsSync(holderRecord)) {
      const { pid } = JSON.parse(fs.readFileSync(holderRecord, 'utf8'));
      process.kill(pid, 'SIGTERM');
      await bounded(new Promise((resolve) => {
        if (childClosed) resolve();
        else browser.child.once('close', resolve);
      }));
      assert.equal(fs.readFileSync(holderTerminated, 'utf8'), 'SIGTERM');
    }
    assert.equal(fs.existsSync(browser.profileRoot), false);
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test('valid startup, event, and request responses survive normal close', async () => {
  const child = protocolChild();
  const browser = new ChromeVisualBrowser('injected-chrome', { spawnImpl: () => child });
  try {
    assert.equal(await bounded(browser.sessionPromise), 'session');
    assert.deepEqual(child.commands, ['Target.getTargets', 'Target.attachToTarget', 'Page.enable', 'Runtime.enable']);
    const event = browser.cdp.waitFor('Test.event', 'session');
    child.stdio[4].write(`${JSON.stringify({ method: 'Test.event', sessionId: 'session', params: { ok: true } })}\0`);
    assert.deepEqual(await bounded(event), { ok: true });
    await assert.rejects(browser.cdp.send('Test.error'), /ordinary request rejection/);
    assert.deepEqual(await browser.cdp.send('Test.ping'), {});
  } finally {
    await browser.close();
    await browser.close();
    assert.equal(fs.existsSync(browser.profileRoot), false);
  }
});

test('terminal failure preserves the first error and rejects future work', async () => {
  const child = protocolChild();
  const browser = new ChromeVisualBrowser('injected-chrome', { spawnImpl: () => child });
  try {
    await browser.sessionPromise;
    const pending = browser.cdp.send('Test.silent').catch((error) => error);
    const waiting = browser.cdp.waitFor('Test.event', 'session').catch((error) => error);
    child.stdio[4].emit('error', new Error('first transport failure'));
    const first = await bounded(pending);
    assert.match(first.message, /first transport failure/);
    assert.equal(await bounded(waiting), first);
    child.stdio[4].emit('end');
    child.stdio[4].emit('close');
    child.emit('exit', 42, null);
    const commandCount = child.commands.length;
    await assert.rejects(bounded(browser.cdp.send('Test.ping')), (error) => error === first);
    await assert.rejects(bounded(browser.cdp.waitFor('Test.event', 'session')), (error) => error === first);
    assert.equal(child.commands.length, commandCount);
    assert.equal(browser.cdp.pending.size, 0);
    assert.equal(browser.cdp.waiters.length, 0);
  } finally {
    await browser.close();
  }
});

test('request timeout includes process diagnostics without closing healthy transport', async () => {
  const child = protocolChild();
  const browser = new ChromeVisualBrowser('injected-chrome', { spawnImpl: () => child });
  try {
    await browser.sessionPromise;
    child.stderr.write('injected Chrome diagnostic\n');
    await assert.rejects(browser.cdp.send('Test.silent', {}, undefined, 30), (error) => {
      assert.match(error.message, /Test.silent: timed out after 30ms/);
      assert.match(error.message, /Chrome process: still running/);
      assert.match(error.message, /injected Chrome diagnostic/);
      return true;
    });
    assert.deepEqual(await browser.cdp.send('Test.ping'), {});
    await browser.close();
    await assert.rejects(bounded(browser.cdp.send('Test.ping')), /visual-check finished/);
    await assert.rejects(bounded(browser.cdp.waitFor('Test.event', 'session')), /visual-check finished/);
  } finally {
    await browser.close();
  }
});
