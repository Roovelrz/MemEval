#!/usr/bin/env node

// Small, non-mutating benchmark for the active LongMemEval translation workpack.
// It reads only unresolved source blocks and writes results to a separate benchmark
// directory. API keys are read from environment variables and never persisted.

const fs = require('fs');
const path = require('path');
const { performance } = require('perf_hooks');

const WORKPACK = path.resolve(__dirname, '../../datasets/zh_derived/longmemeval_zh/v0.1/translation_workpack');
const SELECTION = path.join(WORKPACK, 'active_20_selection.json');
const OUTPUT_DIR = path.join(WORKPACK, '..', 'translation_benchmark');
const OUTPUT = path.join(OUTPUT_DIR, 'baidu_deepseek_ab_latest.json');
const PLACEHOLDER = '[待翻译：请只替换本行，保留上下边界标记]';
const SAMPLE_SIZE = Number(process.env.TRANSLATION_BENCHMARK_SIZE || 20);
const CONCURRENCY = Math.max(1, Number(process.env.TRANSLATION_BENCHMARK_CONCURRENCY || 4));
const MAX_SOURCE_CHARS = Number(process.env.TRANSLATION_BENCHMARK_MAX_CHARS || 5500);

const BAIDU_KEY = process.env.BAIDU_API_KEY;
const BAIDU_APP_ID = process.env.BAIDU_APP_ID || process.env.BAIDU_APPID;
const BAIDU_URL = (process.env.BAIDU_BASE_URL || 'https://fanyi-api.baidu.com/ait/api/aiTextTranslate').replace(/\/$/, '');
const BAIDU_MODEL_TYPE = process.env.BAIDU_MODEL_TYPE || 'llm';
const BAIDU_CHUNKED = process.env.BAIDU_CHUNKED === '1';
const BAIDU_CHUNK_MAX_CHARS = Number(process.env.BAIDU_CHUNK_MAX_CHARS || 1800);
const DEEPSEEK_KEY = process.env.DEEPSEEK_API_KEY;
const DEEPSEEK_BASE_URL = (process.env.DEEPSEEK_BASE_URL || 'https://api.deepseek.com').replace(/\/$/, '');
const DEEPSEEK_MODEL = process.env.DEEPSEEK_MODEL || 'deepseek-v4-flash';

if (!BAIDU_KEY || !BAIDU_APP_ID || !DEEPSEEK_KEY) {
  throw new Error('BAIDU_API_KEY, BAIDU_APP_ID and DEEPSEEK_API_KEY are required');
}

function listMarkdownFiles(dir) {
  const output = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) output.push(...listMarkdownFiles(full));
    else if (entry.isFile() && entry.name.endsWith('.md')) output.push(full);
  }
  return output;
}

function extractBlocks(filePath, caseId) {
  const text = fs.readFileSync(filePath, 'utf8');
  const re = /<!-- SOURCE_(QUESTION|ANSWER|TURN_\d+)_BEGIN -->\r?\n([\s\S]*?)\r?\n<!-- SOURCE_\1_END -->\r?\n\r?\n### Chinese translation — EDIT HERE\r?\n\r?\n<!-- ZH_\1_BEGIN -->\r?\n([\s\S]*?)\r?\n<!-- ZH_\1_END -->/g;
  const blocks = [];
  let match;
  while ((match = re.exec(text)) !== null) {
    if (!match[3].includes(PLACEHOLDER)) continue;
    if (!match[2].trim() || match[2].length > MAX_SOURCE_CHARS) continue;
    blocks.push({
      id: `${caseId}/${path.relative(WORKPACK, filePath).replaceAll('\\', '/')}:${match[1]}`,
      case_id: caseId,
      file: path.relative(WORKPACK, filePath).replaceAll('\\', '/'),
      block_type: match[1],
      source: match[2],
    });
  }
  return blocks;
}

function chooseSample() {
  const selection = JSON.parse(fs.readFileSync(SELECTION, 'utf8'));
  const byCase = new Map();
  for (const item of selection.cases) {
    const caseDir = path.join(WORKPACK, 'cases', item.question_id);
    const blocks = [];
    for (const file of listMarkdownFiles(caseDir).sort()) blocks.push(...extractBlocks(file, item.question_id));
    byCase.set(item.question_id, blocks);
  }
  const caseIds = [...byCase.keys()].sort();
  const chosen = [];
  let cursor = 0;
  while (chosen.length < SAMPLE_SIZE) {
    let added = false;
    for (const caseId of caseIds) {
      const blocks = byCase.get(caseId);
      if (cursor < blocks.length && chosen.length < SAMPLE_SIZE) {
        chosen.push(blocks[cursor]);
        added = true;
      }
    }
    if (!added) break;
    cursor += 1;
  }
  return chosen;
}

async function postJson(url, headers, body) {
  const response = await fetch(url, {
    method: 'POST',
    headers: { ...headers, 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(120000),
  });
  const raw = await response.text();
  let parsed;
  try { parsed = JSON.parse(raw); } catch (_) { throw new Error(`HTTP ${response.status}: non-JSON response`); }
  if (!response.ok || parsed.error) {
    throw new Error(`HTTP ${response.status}: ${parsed.error?.message || parsed.error_msg || parsed.msg || raw.slice(0, 300)}`);
  }
  return parsed;
}

async function translateBaiduChunk(source) {
  const response = await postJson(BAIDU_URL, { Authorization: `Bearer ${BAIDU_KEY}` }, {
    appid: BAIDU_APP_ID,
    q: source,
    from: 'en',
    to: 'zh',
    model_type: BAIDU_MODEL_TYPE,
  });
  const translations = Array.isArray(response.trans_result)
    ? response.trans_result.map((item) => String(item.dst || '').trim()).filter(Boolean)
    : [];
  if (!translations.length) throw new Error('Baidu response did not contain translated text');
  return translations.join('\n').trim();
}

function splitForBaidu(source) {
  if (!BAIDU_CHUNKED || source.length <= BAIDU_CHUNK_MAX_CHARS) return [source];
  const paragraphs = source.split(/(?<=\n)\s*\n+/);
  const chunks = [];
  let current = '';
  for (const paragraph of paragraphs) {
    const parts = paragraph.length <= BAIDU_CHUNK_MAX_CHARS
      ? [paragraph]
      : paragraph.split(/(?<=[.!?])\s+/);
    for (const part of parts) {
      if (!part) continue;
      if (current && current.length + part.length + 2 > BAIDU_CHUNK_MAX_CHARS) {
        chunks.push(current);
        current = '';
      }
      current += (current ? '\n\n' : '') + part;
    }
  }
  if (current) chunks.push(current);
  return chunks.length ? chunks : [source];
}

async function translateBaidu(source) {
  const chunks = splitForBaidu(source);
  const translations = [];
  for (const chunk of chunks) translations.push(await translateBaiduChunk(chunk));
  return translations.join('\n\n').trim();
}

const TRANSLATE_PROMPT = `你是 LongMemEval 记忆评测数据的专业英译中译者。完整翻译输入文本为简体中文，不摘要、不删减、不补充事实、不纠正原文错误。保留数字、日期、金额、单位、URL、路径、代码、品牌、人名、地名、重复、否定、时间关系和 Markdown 结构。只返回译文，不要解释。`;

async function translateDeepSeek(source) {
  const response = await postJson(`${DEEPSEEK_BASE_URL}/chat/completions`, { Authorization: `Bearer ${DEEPSEEK_KEY}` }, {
    model: DEEPSEEK_MODEL,
    messages: [
      { role: 'system', content: TRANSLATE_PROMPT },
      { role: 'user', content: source },
    ],
    temperature: 0.1,
    thinking: { type: 'disabled' },
    max_tokens: Math.min(12000, Math.max(512, Math.ceil(source.length * 1.5))),
  });
  const translation = response.choices?.[0]?.message?.content;
  if (!translation) throw new Error('DeepSeek response did not contain message.content');
  return translation.trim().replace(/^```(?:text|markdown)?\s*/i, '').replace(/\s*```$/i, '').trim();
}

async function verifyWithDeepSeek(source, candidate) {
  const response = await postJson(`${DEEPSEEK_BASE_URL}/chat/completions`, { Authorization: `Bearer ${DEEPSEEK_KEY}` }, {
    model: DEEPSEEK_MODEL,
    messages: [
      { role: 'system', content: `你是严格的英译中翻译修复器。逐句、逐项、逐段检查候选译文。若候选译文存在任何漏译、截断、错译或事实丢失，必须从原文重新翻译并输出完整全文；不能只返回候选译文，也不能只给修改意见。不得摘要、删减或补充事实。只返回合法 JSON：{"translation":"完整最终译文","changed":true或false,"note":"不超过一句话"}。` },
      { role: 'user', content: `原文：\n${source}\n\n候选译文：\n${candidate}` },
    ],
    temperature: 0.1,
    thinking: { type: 'disabled' },
    max_tokens: Math.min(12000, Math.max(768, Math.ceil(source.length * 1.6))),
  });
  const content = response.choices?.[0]?.message?.content?.trim();
  if (!content) throw new Error('DeepSeek verifier response did not contain message.content');
  const normalized = content.replace(/^```json\s*/i, '').replace(/\s*```$/i, '').trim();
  let parsed;
  try { parsed = JSON.parse(normalized); } catch (_) {
    const start = normalized.indexOf('{');
    const end = normalized.lastIndexOf('}');
    if (start < 0 || end <= start) throw new Error('DeepSeek verifier returned invalid JSON');
    parsed = JSON.parse(normalized.slice(start, end + 1));
  }
  if (!parsed.translation) throw new Error('DeepSeek verifier JSON has no translation');
  return { translation: String(parsed.translation).trim(), changed: Boolean(parsed.changed), note: String(parsed.note || '').trim() };
}

async function mapConcurrent(items, worker) {
  const results = new Array(items.length);
  let cursor = 0;
  async function run() {
    while (true) {
      const index = cursor++;
      if (index >= items.length) return;
      try { results[index] = { ok: true, value: await worker(items[index], index) }; }
      catch (error) { results[index] = { ok: false, error: String(error.message || error) }; }
    }
  }
  await Promise.all(Array.from({ length: Math.min(CONCURRENCY, items.length) }, run));
  return results;
}

async function timed(label, items, worker) {
  const started = performance.now();
  const results = await mapConcurrent(items, worker);
  return { label, elapsed_ms: Math.round(performance.now() - started), results };
}

async function main() {
  const sample = chooseSample();
  if (!sample.length) throw new Error('No unresolved blocks within the benchmark size limit');
  const baidu = await timed(BAIDU_CHUNKED ? 'baidu_llm_chunked' : `baidu_${BAIDU_MODEL_TYPE}`, sample, (item) => translateBaidu(item.source));
  const deepseek = await timed('deepseek_direct', sample, (item) => translateDeepSeek(item.source));
  const hybridInputs = sample.map((item, index) => ({ item, baidu: baidu.results[index] }));
  const hybrid = await timed('baidu_then_deepseek_verify', hybridInputs, ({ item, baidu: result }) => {
    if (!result.ok) throw new Error(`Baidu prerequisite failed: ${result.error}`);
    return verifyWithDeepSeek(item.source, result.value);
  });

  const rows = sample.map((item, index) => ({
    ...item,
    baidu: baidu.results[index],
    deepseek_direct: deepseek.results[index],
    hybrid: hybrid.results[index],
  }));
  const summary = {
    generated_at: new Date().toISOString(),
    sample_size: sample.length,
    max_source_chars: MAX_SOURCE_CHARS,
    concurrency: CONCURRENCY,
    baidu_model_type: BAIDU_MODEL_TYPE,
    baidu_chunked: BAIDU_CHUNKED,
    baidu_chunk_max_chars: BAIDU_CHUNK_MAX_CHARS,
    deepseek_model: DEEPSEEK_MODEL,
    variants: [
      { label: baidu.label, elapsed_ms: baidu.elapsed_ms, ok: baidu.results.filter((x) => x.ok).length },
      { label: deepseek.label, elapsed_ms: deepseek.elapsed_ms, ok: deepseek.results.filter((x) => x.ok).length },
      { label: hybrid.label, elapsed_ms: hybrid.elapsed_ms, ok: hybrid.results.filter((x) => x.ok).length, changed: hybrid.results.filter((x) => x.ok && x.value.changed).length },
    ],
    rows,
  };
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  fs.writeFileSync(OUTPUT, JSON.stringify(summary, null, 2) + '\n', 'utf8');
  console.log(JSON.stringify({ output: OUTPUT, variants: summary.variants, sample_ids: sample.map((x) => x.id) }, null, 2));
}

main().catch((error) => { console.error(error); process.exitCode = 1; });
