import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import vm from 'node:vm';
import { pathToFileURL } from 'node:url';
import { createRequire } from 'node:module';
import { createHash } from 'node:crypto';

const root = process.cwd();
const scratch = fs.mkdtempSync(path.join(os.tmpdir(), 'pkstack-policy-probe-'));
const bundle = process.argv[2];
if (!bundle) throw new Error('Pass the installed Kiro 2.21.2 dist/server/acp-server.js path');
const original = fs.readFileSync(bundle, 'utf8');
if (createHash('sha256').update(original).digest('hex') !== '7e102d154413a7b92ed1abae0ab32d5761debfefdff4d626075e20d63f9da0cb') throw new Error('Unsupported bundle; review extraction boundaries for this Kiro version');
const cut = original.indexOf(';var XZi={rules:', original.indexOf('var ISt=class'));
if (cut < 0) throw new Error('Unsupported installed bundle boundary');
// Load the unchanged native policy implementation, not the ACP server entrypoint.
// No model, network, hook execution, credentials, or hazardous shell invocation.
const source = original.slice(0, cut + 1) + '\nexport { ISt as PolicySession, Z6t as filterTools, iU as profilePolicy, ete as ReadTool, oDe as WriteTool };';
const nativeRequire = createRequire(pathToFileURL(bundle));
const mod = new vm.SourceTextModule(source, {
  identifier: bundle,
  initializeImportMeta(meta) { meta.url = pathToFileURL(bundle).href; },
  importModuleDynamically: spec => import(nativeRequire.resolve(spec)),
});
await mod.link(async spec => {
  const external = await import(nativeRequire.resolve(spec));
  const names = Object.keys(external);
  const linked = new vm.SyntheticModule(names, function() {
    for (const name of names) this.setExport(name, external[name]);
  });
  return linked;
});
await mod.evaluate();
const { PolicySession, filterTools, profilePolicy, ReadTool, WriteTool } = mod.namespace;
const userDir = path.join(scratch, 'user');
const workspace = path.join(scratch, 'workspace');
fs.mkdirSync(path.join(userDir, '.kiro', 'settings'), { recursive: true });
fs.mkdirSync(workspace, { recursive: true });
const external = path.join(scratch, 'external');
fs.mkdirSync(external, { recursive: true });
if (!fs.existsSync(path.join(workspace, 'escape'))) fs.symlinkSync(external, path.join(workspace, 'escape'));
fs.copyFileSync(path.join(root, 'powers/pkstack/examples/permissions.yaml'), path.join(userDir, '.kiro/settings/permissions.yaml'));
const realPolicy = path.join(os.homedir(), '.kiro/settings/permissions.yaml');
const hash = p => createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const realBefore = fs.existsSync(realPolicy) ? hash(realPolicy) : null;
const profiles = [['Default', null], ...['pkstack', 'pkstack-architect', 'pkstack-reviewer', 'pkstack-verifier'].map(name => [name, JSON.parse(fs.readFileSync(path.join(root, 'powers/pkstack/templates/project/.kiro/agents', name+'.json'), 'utf8'))])];
const results = [];
for (const [name, profile] of profiles) {
  const session = new PolicySession({ homeDir: userDir, workspaceRoots: [workspace], workspaceTrusted: true, agentPermissions: profile?.permissions, agentPermissionsFromWorkspace: true, agentPermissionsWorkspaceRoot: workspace });
  if (session.hasFatalParseError()) throw new Error(JSON.stringify(session.getLoadErrors()));
  await session.engine.ignoreEvaluatorsReady;
  const checks = [];
  for (const [command, expected] of [
    ['pwd', 'allow'], ['rm -rf build', 'allow'], ['git status --short && git restore src/app.py', 'allow'],
    ['uv sync --frozen; .pkstack/bin/projectctl doctor --output json', 'allow'],
    ['true && rm -rf /', 'deny'], ['printf safe; /bin/rm -rf "$HOME"', 'deny'],
    ['echo safe | cat; sudo /sbin/mkfs.ext4 /dev/sda', 'deny'],
    ['dd if=image of=/dev/null', 'allow'], ['dd if=image of=/dev/disk9', 'deny'],
  ]) {
    const observed = await session.engine.evaluateShell(command);
    checks.push({ command, expected, effect: observed.effect, scope: observed.scope, subCommands: observed.analysis.subCommands });
    if (observed.effect !== expected) throw new Error(JSON.stringify({ name, ...checks.at(-1) }));
  }
  const files = ['src/app.py', 'uv.lock', '.pkstack/state/goal.json'].map(file => ({ file, effect: session.engine.evaluateFilesystem('fs_write', path.join(workspace, file), workspace).effect }));
  if (files.some(x => x.effect !== 'allow')) throw new Error(JSON.stringify(files));
  const protectedFiles = ['.kiroignore', 'escape/target.txt'].map(file => ({ file, effect: session.engine.evaluateFilesystem('fs_write', path.join(workspace, file), workspace).effect }));
  if (protectedFiles.some(x => x.effect !== 'deny')) throw new Error(JSON.stringify(protectedFiles));
  const mcp = session.engine.evaluateRequest({ capability: 'mcp', resource: 'example/tool' }).effect;
  if (mcp === 'allow') throw new Error('Builtin unexpectedly allows MCP');
  const nativeRead = new ReadTool({});
  const nativeWrite = new WriteTool({});
  const tools = [nativeRead, nativeWrite, { id: 'run_command', tags: ['shell', '@builtin'] }, { id: 'remote_example', tags: ['@mcp'] }];
  const visible = profile ? filterTools(tools, profilePolicy(profile)).map(x => x.id) : tools.filter(x => x.id !== 'remote_example').map(x => x.id);
  if (profile && (visible.includes(nativeWrite.id) !== (name === 'pkstack') || visible.includes('run_command') !== (name === 'pkstack') || visible.includes('remote_example'))) throw new Error(JSON.stringify({name, visible}));
  results.push({ profile: name, loadErrors: session.getLoadErrors(), userRules: session.getRules().filter(x => x.scope === 'user').length, checks, files, protectedFiles, mcp, visible });
  session.dispose();
}
if ((fs.existsSync(realPolicy) ? hash(realPolicy) : null) !== realBefore) throw new Error('User policy changed');
const receipt = { version: '2.21.2', bundleSha256: hash(bundle), presetSha256: hash(path.join(root, 'powers/pkstack/examples/permissions.yaml')), mode: 'native PolicySession and tool filtering; no model session or shell execution', realPolicyUnchanged: true, results };
fs.writeFileSync(path.join(scratch, 'receipt.json'), JSON.stringify(receipt, null, 2)+'\n');
process.stdout.write(JSON.stringify(receipt, null, 2)+'\n');
process.exit(0);
