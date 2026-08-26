#!/usr/bin/env node

// Resume-safe Baidu-first translator for the active LongMemEval workpack.
// Phase "baidu" fills every remaining placeholder and records suspicious drafts.
// Phase "verify" sends only recorded anomalies to DeepSeek and replaces them.
// Phase "all" runs both phases in sequence. Original source data is never edited.

const fs = require('fs');
const os = require('os');
const path = require('path');
const crypto = require('crypto');

const WORKPACK = path.resolve(__dirname, '../../datasets/zh_derived/longmemeval_zh/v0.1/translation_workpack');
const SELECTION = path.join(WORKPACK, 'active_20_selection.json');
const ANOMALY_PATH = path.join(WORKPACK, 'baidu_translation_anomalies.json');
const RUN_REPORT_PATH = path.join(WORKPACK, 'baidu_first_translation_run_report.json');
const PLACEHOLDER = '[待翻译：请只替换本行，保留上下边界标记]';

const PHASE = (process.env.TRANSLATION_PHASE || 'all').toLowerCase();
const CONCURRENCY = Math.max(1, Number(process.env.TRANSLATION_CONCURRENCY || 6));
const BAIDU_CHUNK_MAX_CHARS = Number(process.env.BAIDU_CHUNK_MAX_CHARS || 1800);
const BAIDU_REQUEST_DELAY_MS = Math.max(0, Number(process.env.BAIDU_REQUEST_DELAY_MS || 0));
const BAIDU_URL = (process.env.BAIDU_BASE_URL || 'https://fanyi-api.baidu.com/ait/api/aiTextTranslate').replace(/\/$/, '');
const BAIDU_MODEL_TYPE = process.env.BAIDU_MODEL_TYPE || 'llm';
const BAIDU_KEY = process.env.BAIDU_API_KEY;
const BAIDU_APP_ID = process.env.BAIDU_APP_ID || process.env.BAIDU_APPID;
const DEEPSEEK_BASE_URL = (process.env.DEEPSEEK_BASE_URL || 'https://api.deepseek.com').replace(/\/$/, '');
const DEEPSEEK_MODEL = process.env.DEEPSEEK_MODEL || 'deepseek-v4-flash';
const DEEPSEEK_KEY = process.env.DEEPSEEK_API_KEY;

if (!['baidu', 'verify', 'all'].includes(PHASE)) throw new Error(`Unknown TRANSLATION_PHASE: ${PHASE}`);
if ((PHASE === 'baidu' || PHASE === 'all') && (!BAIDU_KEY || !BAIDU_APP_ID)) {
  throw new Error('BAIDU_API_KEY and BAIDU_APP_ID are required for the Baidu phase');
}
if ((PHASE === 'verify' || PHASE === 'all') && !DEEPSEEK_KEY) {
  throw new Error('DEEPSEEK_API_KEY is required for the verification phase');
}

function readJson(filePath, fallback) {
  try { return JSON.parse(fs.readFileSync(filePath, 'utf8')); }
  catch (error) { if (error.code === 'ENOENT') return fallback; throw error; }
}

function writeJson(filePath, value) {
  const temp = `${filePath}.${process.pid}.tmp`;
  fs.writeFileSync(temp, JSON.stringify(value, null, 2) + '\n', 'utf8');
  fs.renameSync(temp, filePath);
}

function sha256(value) {
  return crypto.createHash('sha256').update(value, 'utf8').digest('hex');
}

function listMarkdownFiles(dir) {
  const files = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) files.push(...listMarkdownFiles(full));
    else if (entry.isFile() && entry.name.endsWith('.md')) files.push(full);
  }
  return files.sort();
}

function extractRecords(filePath, caseId) {
  const text = fs.readFileSync(filePath, 'utf8');
  const re = /<!-- SOURCE_(QUESTION|ANSWER|TURN_\d+)_BEGIN -->\r?\n([\s\S]*?)\r?\n<!-- SOURCE_\1_END -->\r?\n\r?\n### Chinese translation — EDIT HERE\r?\n\r?\n<!-- ZH_\1_BEGIN -->\r?\n([\s\S]*?)\r?\n<!-- ZH_\1_END -->/g;
  const records = [];
  let match;
  while ((match = re.exec(text)) !== null) {
    if (!match[3].includes(PLACEHOLDER)) continue;
    records.push({
      id: `${caseId}/${path.relative(WORKPACK, filePath).replaceAll('\\', '/')}::${match[1]}`,
      case_id: caseId,
      file: path.relative(WORKPACK, filePath).replaceAll('\\', '/'),
      block_type: match[1],
      source: match[2],
      placeholder: match[3],
      start: match.index,
      end: re.lastIndex,
      full: match[0],
    });
  }
  return records;
}

function extractFilledRecords(filePath, caseId) {
  const text = fs.readFileSync(filePath, 'utf8');
  const re = /<!-- SOURCE_(QUESTION|ANSWER|TURN_\d+)_BEGIN -->\r?\n([\s\S]*?)\r?\n<!-- SOURCE_\1_END -->\r?\n\r?\n### Chinese translation — EDIT HERE\r?\n\r?\n<!-- ZH_\1_BEGIN -->\r?\n([\s\S]*?)\r?\n<!-- ZH_\1_END -->/g;
  const records = [];
  let match;
  while ((match = re.exec(text)) !== null) {
    if (match[3].includes(PLACEHOLDER)) continue;
    records.push({
      id: `${caseId}/${path.relative(WORKPACK, filePath).replaceAll('\\', '/')}::${match[1]}`,
      case_id: caseId,
      file: path.relative(WORKPACK, filePath).replaceAll('\\', '/'),
      block_type: match[1],
      source: match[2],
      translation: match[3],
    });
  }
  return records;
}

function splitForBaidu(source) {
  if (source.length <= BAIDU_CHUNK_MAX_CHARS) return [source];
  const units = source.split(/(?<=\n)\s*\n+/);
  const chunks = [];
  let current = '';
  const append = (part) => {
    if (!part) return;
    if (part.length > BAIDU_CHUNK_MAX_CHARS) {
      if (current) { chunks.push(current); current = ''; }
      for (let i = 0; i < part.length; i += BAIDU_CHUNK_MAX_CHARS) chunks.push(part.slice(i, i + BAIDU_CHUNK_MAX_CHARS));
      return;
    }
    if (current && current.length + part.length + 2 > BAIDU_CHUNK_MAX_CHARS) {
      chunks.push(current);
      current = '';
    }
    current += (current ? '\n\n' : '') + part;
  };
  for (const unit of units) {
    if (unit.length <= BAIDU_CHUNK_MAX_CHARS) append(unit);
    else {
      const sentences = unit.split(/(?<=[.!?。！？])\s+/);
      for (const sentence of sentences) append(sentence);
    }
  }
  if (current) chunks.push(current);
  return chunks.length ? chunks : [source];
}

function sleep(ms) { return new Promise((resolve) => setTimeout(resolve, ms)); }

async function postJson(url, headers, body, label) {
  let lastError;
  for (let attempt = 0; attempt < 4; attempt += 1) {
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: { ...headers, 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
        signal: AbortSignal.timeout(120000),
      });
      const raw = await response.text();
      let parsed;
      try { parsed = JSON.parse(raw); } catch (_) { throw new Error(`${label}: HTTP ${response.status}, non-JSON response`); }
      if (response.ok && !parsed.error && !parsed.error_code) return parsed;
      const message = parsed.error?.message || parsed.error_msg || parsed.msg || raw.slice(0, 300);
      const retryable = response.status === 429 || response.status >= 500 || parsed.error_code === '54003';
      lastError = new Error(`${label}: HTTP ${response.status}: ${message}`);
      if (!retryable) throw lastError;
    } catch (error) {
      lastError = error;
      if (attempt === 3) break;
    }
    await sleep(1000 * (attempt + 1));
  }
  throw lastError || new Error(`${label}: request failed`);
}

async function translateBaiduChunk(chunk) {
  if (BAIDU_REQUEST_DELAY_MS) await sleep(BAIDU_REQUEST_DELAY_MS);
  const response = await postJson(BAIDU_URL, { Authorization: `Bearer ${BAIDU_KEY}` }, {
    appid: BAIDU_APP_ID,
    q: chunk,
    from: 'en',
    to: 'zh',
    model_type: BAIDU_MODEL_TYPE,
  }, 'Baidu');
  const translated = Array.isArray(response.trans_result)
    ? response.trans_result.map((item) => String(item.dst || '').trim()).filter(Boolean)
    : [];
  if (!translated.length) throw new Error('Baidu: response did not contain translated text');
  return translated.join('\n').trim();
}

async function translateBaidu(source) {
  const chunks = splitForBaidu(source);
  const translations = [];
  for (const chunk of chunks) translations.push(await translateBaiduChunk(chunk));
  return translations.join('\n\n').trim();
}

function countParagraphs(value) { return value.split(/\n\s*\n+/).filter((item) => item.trim()).length; }
function countListItems(value) { return (value.match(/^\s*(?:[-*+] |\d+[.)] )/gm) || []).length; }
function countMatches(value, pattern) { return (value.match(pattern) || []).length; }

function detectAnomalies(source, translation) {
  const reasons = [];
  const ratio = translation.length / Math.max(1, source.length);
  if ((source.length >= 400 && ratio < 0.15) || (source.length >= 120 && translation.length < 25)) reasons.push('possible_truncation_or_low_length_ratio');
  const sourceLists = countListItems(source);
  const translationLists = countListItems(translation);
  if (sourceLists >= 2 && translationLists < sourceLists) reasons.push('list_format_count_dropped');
  if (countParagraphs(source) >= 4 && countParagraphs(translation) < 2) reasons.push('paragraph_structure_dropped');
  if (countMatches(source, /```/g) > countMatches(translation, /```/g)) reasons.push('code_fence_count_dropped');
  if (countMatches(source, /`[^`]+`/g) > countMatches(translation, /`[^`]+`/g)) reasons.push('inline_code_count_dropped');
  if (countMatches(source, /https?:\/\/\S+/g) > countMatches(translation, /https?:\/\/\S+/g)) reasons.push('url_count_dropped');
  if (source.length >= 120 && translation.trim() === source.trim()) reasons.push('source_returned_unchanged');
  return { reasons, ratio: Number(ratio.toFixed(4)) };
}

function replaceSuccessfulRecords(original, records, translations) {
  let output = original;
  const replacements = records
    .map((record, index) => ({ record, translation: translations[index] }))
    .filter((item) => item.translation);
  for (const { record, translation } of replacements.sort((a, b) => b.record.start - a.record.start)) {
    const replacement = record.full.replace(record.placeholder, translation);
    output = output.slice(0, record.start) + replacement + output.slice(record.end);
  }
  return output;
}

function selectedFiles() {
  const selection = readJson(SELECTION, { cases: [] });
  const files = [];
  for (const item of selection.cases) {
    const caseDir = path.join(WORKPACK, 'cases', item.question_id);
    for (const file of listMarkdownFiles(caseDir)) files.push({ file, caseId: item.question_id });
  }
  return files;
}

async function mapConcurrent(items, worker) {
  const results = new Array(items.length);
  let cursor = 0;
  async function run() {
    while (true) {
      const index = cursor++;
      if (index >= items.length) return;
      try { results[index] = await worker(items[index], index); }
      catch (error) { results[index] = { error: String(error.message || error) }; }
    }
  }
  await Promise.all(Array.from({ length: Math.min(CONCURRENCY, Math.max(1, items.length)) }, run));
  return results;
}

async function baiduFile(fileInfo) {
  const original = fs.readFileSync(fileInfo.file, 'utf8');
  const records = extractRecords(fileInfo.file, fileInfo.caseId);
  if (!records.length) return { file: fileInfo.file, blocks: 0, successes: 0, anomalies: [], errors: [] };
  const translations = new Array(records.length);
  const anomalies = [];
  const errors = [];
  for (let i = 0; i < records.length; i += 1) {
    const record = records[i];
    try {
      const translation = await translateBaidu(record.source);
      translations[i] = translation;
      const check = detectAnomalies(record.source, translation);
      if (check.reasons.length) anomalies.push({
        id: record.id,
        case_id: record.case_id,
        file: record.file,
        block_type: record.block_type,
        source_sha256: sha256(record.source),
        source: record.source,
        baidu_translation: translation,
        reasons: check.reasons,
        length_ratio: check.ratio,
        status: 'pending',
        detected_at: new Date().toISOString(),
      });
    } catch (error) {
      errors.push({
        id: record.id,
        case_id: record.case_id,
        file: record.file,
        block_type: record.block_type,
        source_sha256: sha256(record.source),
        source: record.source,
        baidu_translation: null,
        reasons: ['baidu_api_error'],
        status: 'baidu_error',
        error: String(error.message || error),
        detected_at: new Date().toISOString(),
      });
    }
  }
  const updated = replaceSuccessfulRecords(original, records, translations);
  if (updated !== original) fs.writeFileSync(fileInfo.file, updated, 'utf8');
  return { file: fileInfo.file, blocks: records.length, successes: translations.filter(Boolean).length, anomalies, errors };
}

async function runBaiduPhase() {
  const files = selectedFiles();
  const registry = readJson(ANOMALY_PATH, { schema_version: '0.1', records: [] });
  const existing = new Map(registry.records.map((item) => [item.id, item]));
  const stats = { phase: 'baidu', started_at: new Date().toISOString(), files_seen: files.length, files_changed: 0, blocks_seen: 0, blocks_translated: 0, anomalies_new: 0, errors: 0 };
  let completed = 0;
  const consumeResult = (result) => {
    if (!result || result.error) { stats.errors += 1; return; }
    stats.blocks_seen += result.blocks;
    stats.blocks_translated += result.successes;
    if (result.successes) stats.files_changed += 1;
    stats.errors += result.errors.length;
    for (const error of result.errors) {
      if (!existing.has(error.id)) existing.set(error.id, error);
      else existing.set(error.id, { ...existing.get(error.id), ...error });
    }
    for (const anomaly of result.anomalies) {
      if (!existing.has(anomaly.id)) { stats.anomalies_new += 1; existing.set(anomaly.id, anomaly); }
      else existing.set(anomaly.id, { ...existing.get(anomaly.id), ...anomaly, status: existing.get(anomaly.id).status === 'verified' ? 'verified' : 'pending' });
    }
    registry.records = [...existing.values()].sort((a, b) => a.id.localeCompare(b.id));
    registry.updated_at = new Date().toISOString();
    writeJson(ANOMALY_PATH, registry);
  };
  const results = await mapConcurrent(files, async (fileInfo) => {
    const result = await baiduFile(fileInfo);
    completed += 1;
    consumeResult(result);
    if (completed % 10 === 0) console.log(`baidu_files=${completed}/${files.length} translated=${stats.blocks_translated} anomalies=${existing.size}`);
    return result;
  });
  // Results have already been consumed as each file finished. This final loop
  // only covers an unexpected worker-level failure that returned no result.
  for (const result of results) if (!result) stats.errors += 1;

  // The previous run may have filled some files before it was interrupted,
  // before the anomaly registry was persisted. Audit filled blocks once so
  // those drafts are not silently lost from the verification queue.
  let audited = 0;
  for (const fileInfo of files) {
    for (const record of extractFilledRecords(fileInfo.file, fileInfo.caseId)) {
      const check = detectAnomalies(record.source, record.translation);
      if (!check.reasons.length || existing.has(record.id)) continue;
      existing.set(record.id, {
        id: record.id,
        case_id: record.case_id,
        file: record.file,
        block_type: record.block_type,
        source_sha256: sha256(record.source),
        source: record.source,
        baidu_translation: record.translation,
        reasons: [...check.reasons, 'recovered_from_interrupted_baidu_run'],
        length_ratio: check.ratio,
        status: 'pending',
        detected_at: new Date().toISOString(),
      });
      audited += 1;
    }
  }
  stats.anomalies_recovered = audited;
  registry.records = [...existing.values()].sort((a, b) => a.id.localeCompare(b.id));
  registry.updated_at = new Date().toISOString();
  writeJson(ANOMALY_PATH, registry);
  stats.finished_at = new Date().toISOString();
  writeJson(RUN_REPORT_PATH, stats);
  console.log(JSON.stringify({ ...stats, anomaly_report: ANOMALY_PATH }, null, 2));
}

function parseVerifier(content) {
  let value = content.trim().replace(/^```json\s*/i, '').replace(/\s*```$/i, '').trim();
  try { return JSON.parse(value); }
  catch (_) {
    const start = value.indexOf('{');
    const end = value.lastIndexOf('}');
    if (start < 0 || end <= start) throw new Error('DeepSeek verifier returned invalid JSON');
    return JSON.parse(value.slice(start, end + 1));
  }
}

async function verifyOne(item) {
  const response = await postJson(`${DEEPSEEK_BASE_URL}/chat/completions`, { Authorization: `Bearer ${DEEPSEEK_KEY}` }, {
    model: DEEPSEEK_MODEL,
    messages: [
      { role: 'system', content: '你是严格的英译中翻译修复器。检查候选译文是否漏译、截断、错译或破坏格式。只要有问题，就根据原文重新翻译完整全文；不能只返回修改意见或候选片段。不得摘要、删减或补充事实。只返回合法 JSON：{"translation":"完整最终译文","changed":true或false,"note":"不超过一句话"}。' },
      { role: 'user', content: `原文：\n${item.source}\n\n百度候选译文：\n${item.baidu_translation}` },
    ],
    temperature: 0.1,
    thinking: { type: 'disabled' },
    max_tokens: Math.min(16000, Math.max(1024, Math.ceil(item.source.length * 1.6))),
  }, 'DeepSeek');
  const content = response.choices?.[0]?.message?.content;
  if (!content) throw new Error('DeepSeek: response did not contain message.content');
  const result = parseVerifier(content);
  if (!result.translation) throw new Error('DeepSeek: verifier JSON has no translation');
  return { translation: String(result.translation).trim(), changed: Boolean(result.changed), note: String(result.note || '').trim() };
}

function replaceVerified(item, translation) {
  const filePath = path.join(WORKPACK, item.file);
  const original = fs.readFileSync(filePath, 'utf8');
  const re = /<!-- SOURCE_(QUESTION|ANSWER|TURN_\d+)_BEGIN -->\r?\n([\s\S]*?)\r?\n<!-- SOURCE_\1_END -->\r?\n\r?\n### Chinese translation — EDIT HERE\r?\n\r?\n<!-- ZH_\1_BEGIN -->\r?\n([\s\S]*?)\r?\n<!-- ZH_\1_END -->/g;
  let match;
  while ((match = re.exec(original)) !== null) {
    if (match[1] !== item.block_type || sha256(match[2]) !== item.source_sha256) continue;
    const replacement = match[0].replace(match[3], translation);
    const updated = original.slice(0, match.index) + replacement + original.slice(re.lastIndex);
    fs.writeFileSync(filePath, updated, 'utf8');
    return true;
  }
  throw new Error(`could not locate source block for ${item.id}`);
}

async function runVerifyPhase() {
  const registry = readJson(ANOMALY_PATH, { schema_version: '0.1', records: [] });
  const pending = registry.records.filter((item) => item.status !== 'verified' && item.baidu_translation);
  const stats = { phase: 'verify', started_at: new Date().toISOString(), anomalies_seen: pending.length, verified: 0, changed: 0, errors: 0 };
  const results = await mapConcurrent(pending, async (item) => {
    try {
      const result = await verifyOne(item);
      replaceVerified(item, result.translation);
      return { id: item.id, ok: true, result };
    } catch (error) {
      return { id: item.id, ok: false, error: String(error.message || error) };
    }
  });
  const byId = new Map(results.map((item) => [item.id, item]));
  for (const item of registry.records) {
    const result = byId.get(item.id);
    if (!result) continue;
    if (result.ok) {
      item.status = 'verified';
      item.deepseek_translation = result.result.translation;
      item.deepseek_changed = result.result.changed;
      item.deepseek_note = result.result.note;
      item.verified_at = new Date().toISOString();
      stats.verified += 1;
      if (result.result.changed) stats.changed += 1;
    } else {
      item.verify_error = result.error;
      stats.errors += 1;
    }
  }
  registry.updated_at = new Date().toISOString();
  writeJson(ANOMALY_PATH, registry);
  stats.finished_at = new Date().toISOString();
  writeJson(RUN_REPORT_PATH, stats);
  console.log(JSON.stringify({ ...stats, anomaly_report: ANOMALY_PATH }, null, 2));
}

async function main() {
  if (PHASE === 'baidu' || PHASE === 'all') await runBaiduPhase();
  if (PHASE === 'verify' || PHASE === 'all') await runVerifyPhase();
}

main().catch((error) => { console.error(error); process.exitCode = 1; });
