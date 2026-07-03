#!/usr/bin/env node
// check-docs-signoff.cjs — 校验 docs/ 下 plan/todos 文件的签名块
// 用法: node scripts/check-docs-signoff.cjs [--strict] [--fix] [--selftest]

'use strict';

const fs = require('fs');
const path = require('path');

const DOCS_DIR = path.resolve(__dirname, '..', 'docs');
const SIGNOFF_RE = /^<!--\s*docs-signoff:\s*author="([^"]+)"\s+kind="(llm|tool|human)"\s+doc="(plan|todos)"\s+ts="(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)"\s*-->/;
const FILENAME_RE = /(plan|todos|计划)/i;
const MAX_FUTURE_MINUTES = 5;

function listTargetFiles(dir) {
  const results = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (entry.name.startsWith('.')) continue;
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) continue;
    if (!entry.name.endsWith('.md')) continue;
    if (entry.name.endsWith('.bak')) continue;
    if (!FILENAME_RE.test(entry.name)) continue;
    results.push(full);
  }
  return results;
}

function validateFile(filepath) {
  const rel = path.relative(DOCS_DIR, filepath);
  const content = fs.readFileSync(filepath, 'utf8');
  const firstLine = content.split(/\r?\n/, 1)[0] || '';

  const m = firstLine.match(SIGNOFF_RE);
  if (!m) {
    return { file: rel, ok: false, reason: '第一行不是合法签名块', firstLine: firstLine.slice(0, 80) };
  }
  const [, author, kind, doc, ts] = m;
  if (!author.trim()) {
    return { file: rel, ok: false, reason: 'author 为空' };
  }
  // 校验时间戳不超过当前时间 +5 分钟
  const tsDate = new Date(ts);
  if (isNaN(tsDate.getTime())) {
    return { file: rel, ok: false, reason: `ts 不是合法时间: ${ts}` };
  }
  const now = new Date();
  const futureLimit = new Date(now.getTime() + MAX_FUTURE_MINUTES * 60 * 1000);
  if (tsDate > futureLimit) {
    return { file: rel, ok: false, reason: `ts 超过当前时间+${MAX_FUTURE_MINUTES}min（防伪造未来）: ${ts}` };
  }
  return { file: rel, ok: true, author, kind, doc, ts };
}

function selftest() {
  const cases = [
    ['<!-- docs-signoff: author="Test" kind="llm" doc="plan" ts="2026-06-18T00:00:00Z" -->', true],
    ['<!-- docs-signoff: author="" kind="llm" doc="plan" ts="2026-06-18T00:00:00Z" -->', false],
    ['<!-- docs-signoff: author="Test" kind="robot" doc="plan" ts="2026-06-18T00:00:00Z" -->', false],
    ['# Some Title', false],
    ['', false],
  ];
  let pass = 0;
  for (const [line, expect] of cases) {
    const m = line.match(SIGNOFF_RE);
    const got = !!m && m[1].trim().length > 0;
    if (got === expect) { pass++; }
    else { console.error(`  FAIL: "${line.slice(0,50)}" => got=${got}, expect=${expect}`); }
  }
  console.log(`selftest: ${pass}/${cases.length} passed`);
  return pass === cases.length;
}

function main() {
  const args = process.argv.slice(2);
  const strict = args.includes('--strict');
  const fix = args.includes('--fix');
  const selftestMode = args.includes('--selftest');

  if (selftestMode) {
    process.exit(selftest() ? 0 : 1);
  }

  if (!fs.existsSync(DOCS_DIR)) {
    console.error(`docs/ not found at ${DOCS_DIR}`);
    process.exit(1);
  }

  const files = listTargetFiles(DOCS_DIR);
  if (!files.length) {
    console.log('No plan/todos files found in docs/');
    process.exit(0);
  }

  let errors = 0;
  let warnings = 0;

  for (const filepath of files) {
    const result = validateFile(filepath);
    if (result.ok) {
      console.log(`  OK   ${result.file}  (${result.author}, ${result.ts})`);
    } else {
      if (result.reason.includes('第一行不是合法签名块') && !strict) {
        console.log(`  WARN ${result.file}  — ${result.reason}`);
        warnings++;
      } else {
        console.error(`  FAIL ${result.file}  — ${result.reason}`);
        if (result.firstLine) console.error(`       first: ${result.firstLine}`);
        errors++;
      }
    }
  }

  console.log(`\n${files.length} files: ${files.length - errors - warnings} OK, ${warnings} WARN, ${errors} FAIL`);
  if (strict && warnings > 0) {
    console.error('--strict: WARN counted as FAIL');
    errors += warnings;
  }
  process.exit(errors > 0 ? 1 : 0);
}

main();
