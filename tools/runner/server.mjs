#!/usr/bin/env node
/**
 * 醫學論文評析工作台 — local runner
 *
 * A small HTTP server that owns `claude -p` child processes, appends their
 * stream-json output to a run log, and streams it to the browser over SSE.
 * The server holds the process, not the page, so closing the browser tab
 * leaves a run going; quitting this terminal does not.
 *
 * No dependencies: Node 18+ standard library only.
 *
 *   node tools/runner/server.mjs [--port 4178] [--data .runner-data] [--open]
 */
import http from 'node:http';
import fs from 'node:fs';
import fsp from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import { spawn, execFile } from 'node:child_process';
import { randomUUID } from 'node:crypto';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const argv = process.argv.slice(2);
const arg = (name, def) => {
  const i = argv.indexOf(`--${name}`);
  return i >= 0 && argv[i + 1] && !argv[i + 1].startsWith('--') ? argv[i + 1] : def;
};
const PORT = Number(arg('port', process.env.RUNNER_PORT || 4178));
const DATA = path.resolve(arg('data', process.env.RUNNER_DATA || path.join(HERE, '.runner-data')));
const OPEN = argv.includes('--open');
const PUBLIC = path.join(HERE, 'public');
const RUNS = path.join(DATA, 'runs');
const STATE_FILE = path.join(DATA, 'projects.json');

/* ── persistence ─────────────────────────────────────────────────────── */

fs.mkdirSync(RUNS, { recursive: true });

function loadProjects() {
  try { return JSON.parse(fs.readFileSync(STATE_FILE, 'utf8')); } catch { return []; }
}
function saveProjects(list) {
  fs.writeFileSync(STATE_FILE, JSON.stringify(list, null, 2));
}
let projects = loadProjects();

/** Everything about a run that is not the log itself. Written beside the log
 *  so that a restarted server can still describe runs it did not start. */
function metaPath(runId) { return path.join(RUNS, runId + '.meta.json'); }
function logPath(runId) { return path.join(RUNS, runId + '.jsonl'); }

function readMeta(runId) {
  try { return JSON.parse(fs.readFileSync(metaPath(runId), 'utf8')); } catch { return null; }
}
function writeMeta(m) { fs.writeFileSync(metaPath(m.id), JSON.stringify(m, null, 2)); }

function listRuns(projectId) {
  let ids;
  try { ids = fs.readdirSync(RUNS).filter(f => f.endsWith('.meta.json')).map(f => f.slice(0, -10)); }
  catch { return []; }
  return ids.map(readMeta).filter(Boolean)
    .filter(m => !projectId || m.projectId === projectId)
    .sort((a, b) => (b.startedAt || 0) - (a.startedAt || 0));
}

/* ── live runs ───────────────────────────────────────────────────────── */

/** runId -> {child, meta, buf:string[], clients:Set<res>, partial:string} */
const live = new Map();

function broadcast(runId, payload) {
  const r = live.get(runId);
  if (!r) return;
  const frame = `data: ${JSON.stringify(payload)}\n\n`;
  for (const res of r.clients) { try { res.write(frame); } catch {} }
}

function finish(runId, patch) {
  const r = live.get(runId);
  if (!r) return;
  Object.assign(r.meta, patch, { endedAt: Date.now() });
  writeMeta(r.meta);
  broadcast(runId, { t: 'end', meta: r.meta });
  for (const res of r.clients) { try { res.end(); } catch {} }
  live.delete(runId);
}

function startRun({ project, service, prompt, model, permissionMode }) {
  const stamp = new Date().toISOString().replace(/[-:T]/g, '').slice(0, 14);
  const runId = `run-${stamp}-${service.key}`;
  const sessionId = randomUUID();

  const args = [
    '-p', prompt,
    '--output-format', 'stream-json',
    '--verbose',
    '--session-id', sessionId,
    '--permission-mode', permissionMode,
  ];
  if (model) args.push('--model', model);

  const meta = {
    id: runId, projectId: project.id, projectName: project.name,
    service: service.key, serviceName: service.name,
    cwd: project.dir, sessionId, model: model || '(default)', permissionMode,
    startedAt: Date.now(), endedAt: null, status: 'running', exitCode: null,
    cost: null, turns: null, error: null,
  };
  writeMeta(meta);

  const out = fs.createWriteStream(logPath(runId), { flags: 'a' });
  let child;
  try {
    child = spawn('claude', args, {
      cwd: project.dir,
      env: { ...process.env, CLAUDE_CODE_ENTRYPOINT: 'journal-review-runner' },
      stdio: ['ignore', 'pipe', 'pipe'],
    });
  } catch (e) {
    meta.status = 'failed'; meta.error = String(e && e.message || e); meta.endedAt = Date.now();
    writeMeta(meta);
    return meta;
  }

  const rec = { child, meta, buf: [], clients: new Set(), partial: '' };
  live.set(runId, rec);

  const emit = line => {
    if (!line) return;
    out.write(line + '\n');
    rec.buf.push(line);
    broadcast(runId, { t: 'line', line });
    // keep the in-memory replay buffer bounded; the file keeps everything
    if (rec.buf.length > 4000) rec.buf.splice(0, rec.buf.length - 4000);
  };

  child.stdout.setEncoding('utf8');
  child.stdout.on('data', chunk => {
    rec.partial += chunk;
    const parts = rec.partial.split('\n');
    rec.partial = parts.pop();
    for (const p of parts) emit(p);
  });

  child.stderr.setEncoding('utf8');
  child.stderr.on('data', chunk => {
    for (const l of String(chunk).split('\n')) {
      if (l.trim()) emit(JSON.stringify({ type: 'runner_stderr', text: l }));
    }
  });

  child.on('error', e => {
    emit(JSON.stringify({ type: 'runner_error', text: String(e && e.message || e) }));
    finish(runId, { status: 'failed', error: String(e && e.message || e) });
  });

  child.on('close', code => {
    if (rec.partial.trim()) emit(rec.partial);
    rec.partial = '';
    out.end();
    // pull cost/turns out of the final result line if it is there
    let cost = null, turns = null;
    for (let i = rec.buf.length - 1; i >= 0 && i > rec.buf.length - 12; i--) {
      try {
        const o = JSON.parse(rec.buf[i]);
        if (o && (o.type === 'result' || o.total_cost_usd != null)) {
          cost = o.total_cost_usd ?? null; turns = o.num_turns ?? null; break;
        }
      } catch {}
    }
    finish(runId, {
      status: rec.meta.status === 'stopping' ? 'stopped' : (code === 0 ? 'done' : 'failed'),
      exitCode: code, cost, turns,
    });
  });

  return meta;
}

/* ── http ────────────────────────────────────────────────────────────── */

const MIME = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8', '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml', '.png': 'image/png', '.ico': 'image/x-icon' };

const json = (res, code, body) => {
  const s = JSON.stringify(body);
  res.writeHead(code, { 'content-type': 'application/json; charset=utf-8',
    'content-length': Buffer.byteLength(s), 'cache-control': 'no-store' });
  res.end(s);
};

function body(req) {
  return new Promise((resolve, reject) => {
    let b = ''; let n = 0;
    req.on('data', c => { n += c.length; if (n > 2e6) { reject(new Error('body too large')); req.destroy(); } b += c; });
    req.on('end', () => { try { resolve(b ? JSON.parse(b) : {}); } catch (e) { reject(e); } });
    req.on('error', reject);
  });
}

async function serveStatic(req, res, pathname) {
  const rel = pathname === '/' ? 'index.html' : pathname.replace(/^\/+/, '');
  const file = path.join(PUBLIC, rel);
  if (!file.startsWith(PUBLIC)) { res.writeHead(403).end('forbidden'); return; }
  try {
    const data = await fsp.readFile(file);
    res.writeHead(200, { 'content-type': MIME[path.extname(file)] || 'application/octet-stream',
      'cache-control': 'no-store' });
    res.end(data);
  } catch {
    res.writeHead(404, { 'content-type': 'text/plain; charset=utf-8' }).end('not found');
  }
}

/* ── environment probe ───────────────────────────────────────────────── */

const run1 = (cmd, args) => new Promise(resolve => {
  execFile(cmd, args, { timeout: 8000 }, (err, stdout) =>
    resolve(err ? null : String(stdout).trim().split('\n')[0].slice(0, 80)));
});
/** Presence only — for tools like pdftoppm that print the version to stderr
 *  and exit non-zero, where run1() would wrongly report them missing. */
const has = cmd => new Promise(resolve => {
  execFile(process.platform === 'win32' ? 'where' : 'which', [cmd], { timeout: 8000 },
    err => resolve(!err));
});

let envCache = null, envAt = 0;
async function probeEnv() {
  if (envCache && Date.now() - envAt < 60_000) return envCache;
  const py = v => run1('python3', ['-c', `import ${v}; print(getattr(${v},"__version__",""))`]);
  const [claude, node, docx, pptx, xl, soffice, pdftoppm] = await Promise.all([
    run1('claude', ['--version']),
    Promise.resolve(process.version),
    py('docx'), py('pptx'), py('openpyxl'),
    run1('soffice', ['--version']).then(v => v || run1('libreoffice', ['--version'])),
    has('pdftoppm'),
  ]);
  envCache = [
    { n: 'Claude Code', ok: !!claude, note: claude || '找不到 claude 指令' },
    { n: 'Node', ok: true, note: node },
    { n: 'python-docx', ok: docx !== null, note: docx || 'pip install python-docx' },
    { n: 'python-pptx', ok: pptx !== null, note: pptx || 'pip install python-pptx' },
    { n: 'openpyxl', ok: xl !== null, note: xl || 'pip install openpyxl' },
    { n: 'LibreOffice', ok: !!soffice, note: soffice || '圖檔 pptx 無法轉成圖片預覽' },
    { n: 'pdftoppm', ok: !!pdftoppm, note: pdftoppm ? '已安裝' : '需要 poppler-utils（圖檔預覽）' },
  ];
  envAt = Date.now();
  return envCache;
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, 'http://localhost');
  const p = url.pathname;

  try {
    if (p === '/api/state' && req.method === 'GET') {
      return json(res, 200, {
        projects,
        running: [...live.values()].map(r => r.meta),
        runs: listRuns(url.searchParams.get('project') || null).slice(0, 60),
        cwdHint: process.cwd(),
        now: Date.now(),
      });
    }

    if (p === '/api/projects' && req.method === 'POST') {
      const b = await body(req);
      const dir = path.resolve(String(b.dir || '').replace(/^~/, os.homedir()));
      if (!fs.existsSync(dir) || !fs.statSync(dir).isDirectory())
        return json(res, 400, { error: `找不到資料夾：${dir}` });
      const proj = {
        id: 'p-' + randomUUID().slice(0, 8),
        name: String(b.name || path.basename(dir)).slice(0, 80),
        dir, journal: String(b.journal || '').slice(0, 120),
        type: String(b.type || 'Original article').slice(0, 60),
        model: String(b.model || '').slice(0, 60),
        permissionMode: ['acceptEdits', 'auto', 'dontAsk', 'bypassPermissions', 'plan', 'manual']
          .includes(b.permissionMode) ? b.permissionMode : 'acceptEdits',
        createdAt: Date.now(),
      };
      projects.push(proj); saveProjects(projects);
      return json(res, 200, { project: proj });
    }

    if (p === '/api/projects' && req.method === 'PATCH') {
      const b = await body(req);
      const proj = projects.find(x => x.id === b.id);
      if (!proj) return json(res, 404, { error: 'no such project' });
      for (const k of ['name', 'journal', 'type', 'model', 'permissionMode'])
        if (b[k] != null) proj[k] = String(b[k]).slice(0, 120);
      saveProjects(projects);
      return json(res, 200, { project: proj });
    }

    if (p === '/api/projects' && req.method === 'DELETE') {
      const b = await body(req);
      projects = projects.filter(x => x.id !== b.id); saveProjects(projects);
      return json(res, 200, { ok: true });
    }

    if (p === '/api/run' && req.method === 'POST') {
      const b = await body(req);
      const project = projects.find(x => x.id === b.projectId);
      if (!project) return json(res, 404, { error: 'no such project' });
      if ([...live.values()].some(r => r.meta.projectId === project.id))
        return json(res, 409, { error: '這個專案已經有一個流程在跑，請先等它結束或按停止。' });
      if (!b.prompt || !String(b.prompt).trim())
        return json(res, 400, { error: 'prompt is empty' });
      const meta = startRun({
        project,
        service: { key: String(b.serviceKey || 'x').replace(/[^a-z0-9]/gi, '').slice(0, 12) || 'x',
                   name: String(b.serviceName || '') },
        prompt: String(b.prompt),
        model: b.model || project.model || '',
        permissionMode: b.permissionMode || project.permissionMode || 'acceptEdits',
      });
      return json(res, 200, { run: meta });
    }

    if (p === '/api/stop' && req.method === 'POST') {
      const b = await body(req);
      const r = live.get(b.runId);
      if (!r) return json(res, 404, { error: 'not running' });
      r.meta.status = 'stopping'; writeMeta(r.meta);
      broadcast(b.runId, { t: 'status', status: 'stopping' });
      try { r.child.kill('SIGTERM'); } catch {}
      setTimeout(() => { try { r.child.kill('SIGKILL'); } catch {} }, 8000);
      return json(res, 200, { ok: true });
    }

    if (p === '/api/env' && req.method === 'GET')
      return json(res, 200, { env: await probeEnv() });

    if (p === '/api/runs' && req.method === 'GET')
      return json(res, 200, { runs: listRuns(url.searchParams.get('project') || null) });

    if (p === '/api/log' && req.method === 'GET') {
      const id = url.searchParams.get('run') || '';
      if (!/^run-[0-9A-Za-z._-]+$/.test(id)) return json(res, 400, { error: 'bad run id' });
      let text = '';
      try { text = await fsp.readFile(logPath(id), 'utf8'); } catch {}
      return json(res, 200, { meta: readMeta(id), lines: text ? text.split('\n').filter(Boolean) : [] });
    }

    if (p === '/api/stream' && req.method === 'GET') {
      const id = url.searchParams.get('run') || '';
      const r = live.get(id);
      res.writeHead(200, { 'content-type': 'text/event-stream; charset=utf-8',
        'cache-control': 'no-cache, no-transform', connection: 'keep-alive',
        'x-accel-buffering': 'no' });
      res.write('retry: 2000\n\n');
      if (!r) {
        // already finished: replay from disk, then close
        let text = ''; try { text = await fsp.readFile(logPath(id), 'utf8'); } catch {}
        for (const line of text.split('\n')) if (line) res.write(`data: ${JSON.stringify({ t: 'line', line })}\n\n`);
        res.write(`data: ${JSON.stringify({ t: 'end', meta: readMeta(id) })}\n\n`);
        return res.end();
      }
      for (const line of r.buf) res.write(`data: ${JSON.stringify({ t: 'line', line })}\n\n`);
      r.clients.add(res);
      const hb = setInterval(() => { try { res.write(': hb\n\n'); } catch {} }, 15000);
      req.on('close', () => { clearInterval(hb); r.clients.delete(res); });
      return;
    }

    if (p.startsWith('/api/')) return json(res, 404, { error: 'no such endpoint' });
    return serveStatic(req, res, p);
  } catch (e) {
    return json(res, 500, { error: String(e && e.message || e) });
  }
});

server.listen(PORT, '127.0.0.1', () => {
  const url = `http://localhost:${PORT}`;
  console.log(`\n  醫學論文評析工作台 — local runner`);
  console.log(`  ${url}`);
  console.log(`  資料夾：${DATA}`);
  console.log(`  專案數：${projects.length}\n`);
  console.log(`  流程由這個伺服器持有，關掉瀏覽器分頁不會中斷；`);
  console.log(`  但關掉這個終端機會一併結束所有執行中的流程。\n`);
  if (OPEN) {
    const cmd = process.platform === 'darwin' ? 'open' : process.platform === 'win32' ? 'start' : 'xdg-open';
    execFile(cmd, [url], () => {});
  }
});

function shutdown() {
  for (const [, r] of live) { try { r.child.kill('SIGTERM'); } catch {} }
  setTimeout(() => process.exit(0), 300);
}
process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);
