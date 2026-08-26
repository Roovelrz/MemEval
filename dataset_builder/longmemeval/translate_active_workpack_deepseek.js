#!/usr/bin/env node

// Resume-safe LongMemEval translator using an OpenAI-compatible DeepSeek API.
// The API key is read only from DEEPSEEK_API_KEY and is never written to disk.

const fs = require('fs');
const path = require('path');

const WORKPACK = path.resolve(
  __dirname,
  '../../datasets/zh_derived/longmemeval_zh/v0.1/translation_workpack',
);
const SELECTION = path.join(WORKPACK, 'active_20_selection.json');
const REPORT = path.join(WORKPACK, 'translation_deepseek_run_report.json');
const PLACEHOLDER = '[待翻译：请只替换本行，保留上下边界标记]';
const RETRANSLATE_ALL = process.env.DEEPSEEK_RETRANSLATE_ALL === '1';
const REPAIR_EMPTY = process.env.DEEPSEEK_REPAIR_EMPTY === '1';
const API_KEY = process.env.DEEPSEEK_API_KEY;
const BASE_URL = (process.env.DEEPSEEK_BASE_URL || 'https://api.deepseek.com').replace(/\/$/, '');
const MODEL = process.env.DEEPSEEK_MODEL || 'deepseek-chat';
const CONCURRENCY = Number(process.env.TRANSLATION_CONCURRENCY || 4);

if (!API_KEY) throw new Error('DEEPSEEK_API_KEY is required');

const SYSTEM_PROMPT = `你是 LongMemEval 记忆评测数据的专业英译中译者。
输入是若干个带有 id 和 source 的 JSON block。请只返回合法 JSON 数组，每项格式为 {"id":"原 id","translation":"完整简体中文译文"}，不要 Markdown 代码围栏、解释或额外字段。
逐项完整翻译，不摘要、不删减、不补充事实、不纠正原文错误。保持原文的信息显式程度、歧义、重复、否定、时间关系、数字、日期、金额、单位、URL、路径、代码、品牌、人名、地名和 Markdown 列表结构。Question 保持第一人称；assistant 回复保持原有语气和粒度。专有名词可以保留英文或使用常见中文译名，但同一 block 内保持一致。`;

function extractRecords(text) {
  const records = [];
  const sourceRe = /<!-- SOURCE_([A-Z0-9_]+)_BEGIN -->([\s\S]*?)<!-- SOURCE_\1_END -->/g;
  let match;
  while ((match = sourceRe.exec(text)) !== null) {
    const type = match[1];
    const source = match[2].replace(/^\r?\n/, '').replace(/\r?\n$/, '');
    const zhRe = new RegExp(`<!-- ZH_${type}_BEGIN -->([\\s\\S]*?)<!-- ZH_${type}_END -->`);
    const zhMatch = zhRe.exec(text.slice(sourceRe.lastIndex));
    if (!zhMatch) continue;
    const zhStart = sourceRe.lastIndex + zhMatch.index;
    const zhFull = zhMatch[0];
    const current = zhMatch[1];
    if (!RETRANSLATE_ALL && !current.includes(PLACEHOLDER) && !(REPAIR_EMPTY && !current.trim())) continue;
    records.push({
      id: type,
      source,
      placeholder: current,
      start: zhStart,
      end: zhStart + zhFull.length,
      full: zhFull,
    });
  }
  return records;
}

function parseModelJson(content) {
  let value = content.trim();
  if (value.startsWith('```')) {
    value = value.replace(/^```(?:json)?\s*/i, '').replace(/\s*```$/, '').trim();
  }
  try {
    return JSON.parse(value);
  } catch (_) {
    const start = value.indexOf('[');
    const end = value.lastIndexOf(']');
    if (start >= 0 && end > start) return JSON.parse(value.slice(start, end + 1));
    const objectStart = value.indexOf('{');
    const objectEnd = value.lastIndexOf('}');
    if (objectStart >= 0 && objectEnd > objectStart) return JSON.parse(value.slice(objectStart, objectEnd + 1));
    throw new Error('model did not return parseable JSON');
  }
}

function isAlreadyChinese(source) {
  const cjk = (source.match(/\p{Script=Han}/gu) || []).length;
  const latin = (source.match(/[A-Za-z]/g) || []).length;
  return cjk >= 2 && cjk >= latin;
}

async function callDeepSeekPlain(record) {
  const body = JSON.stringify({
    model: MODEL,
    messages: [
      { role: 'system', content: '将输入完整翻译为简体中文。不得摘要、删减或补充事实。只返回合法 JSON：{"translation":"完整译文"}。' },
      { role: 'user', content: record.source },
    ],
    temperature: 0.1,
    thinking: { type: 'disabled' },
    max_tokens: Math.min(16000, Math.max(512, Math.ceil(record.source.length * 1.5))),
  });
  let lastError;
  for (let attempt = 0; attempt < 4; attempt += 1) {
    try {
      const response = await fetch(`${BASE_URL}/chat/completions`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${API_KEY}`, 'Content-Type': 'application/json' },
        body,
        signal: AbortSignal.timeout(300000),
      });
      const payload = JSON.parse(await response.text());
      if (!response.ok || payload.error) throw new Error(payload.error?.message || `HTTP ${response.status}`);
      const content = payload.choices?.[0]?.message?.content;
      if (!content) throw new Error('DeepSeek plain response has no content');
      const parsed = parseModelJson(content);
      const translation = typeof parsed === 'string' ? parsed : parsed.translation;
      if (!translation || !String(translation).trim()) throw new Error('DeepSeek plain response was empty');
      return String(translation).trim();
    } catch (error) {
      lastError = error;
      if (attempt < 3) await new Promise((resolve) => setTimeout(resolve, 1000 * (attempt + 1)));
    }
  }
  throw new Error(`DeepSeek plain request failed: ${lastError?.message || 'unknown error'}`);
}

async function callDeepSeek(records) {
  const totalChars = records.reduce((n, record) => n + record.source.length, 0);
  const userPrompt = JSON.stringify(records.map(({ id, source }) => ({ id, source })));
  const body = JSON.stringify({
    model: MODEL,
    messages: [
      { role: 'system', content: SYSTEM_PROMPT },
      { role: 'user', content: `请翻译下面的 JSON blocks，并按要求只返回 JSON 数组：\n${userPrompt}` },
    ],
    temperature: 0.1,
    thinking: { type: 'disabled' },
    max_tokens: Math.min(16000, Math.max(2000, Math.ceil(totalChars * 1.2))),
  });
  let lastError;
  for (let attempt = 0; attempt < 4; attempt += 1) {
    try {
      const response = await fetch(`${BASE_URL}/chat/completions`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${API_KEY}`, 'Content-Type': 'application/json' },
        body,
        signal: AbortSignal.timeout(300000),
      });
      const raw = await response.text();
      const payload = JSON.parse(raw);
      if (!response.ok || payload.error) throw new Error(payload.error?.message || `HTTP ${response.status}`);
      const content = payload.choices?.[0]?.message?.content;
      if (!content) throw new Error('DeepSeek response has no message content');
      const parsed = parseModelJson(content);
      const list = Array.isArray(parsed)
        ? parsed
        : Object.entries(parsed).map(([id, translation]) => ({ id, translation }));
      const normalizeId = (id) => String(id).trim().toUpperCase();
      const byId = new Map(list.map((item) => [normalizeId(item.id), String(item.translation || '')]));
      const missing = records.filter((record) => !byId.has(normalizeId(record.id)) || !byId.get(normalizeId(record.id)).trim());
      if (missing.length && list.length === records.length) {
        // Some responses preserve array order but mangle id casing or whitespace.
        const fallback = list.map((item) => String(item.translation || '').trim());
        if (fallback.some((item) => !item)) {
          if (records.length === 1) return [await callDeepSeekPlain(records[0])];
          throw new Error(`DeepSeek response contained an empty translation; preview=${content.slice(0, 300)}`);
        }
        return fallback;
      }
      if (missing.length) throw new Error(`missing translations for ${missing.map((item) => item.id).join(', ')}`);
      return records.map((record) => byId.get(normalizeId(record.id)).trim());
    } catch (error) {
      lastError = error;
      if (attempt < 3) await new Promise((resolve) => setTimeout(resolve, 1000 * (attempt + 1)));
    }
  }
  throw new Error(`DeepSeek request failed: ${lastError?.message || 'unknown error'}`);
}

function replaceRecords(text, records, translations) {
  let output = text;
  for (let i = records.length - 1; i >= 0; i -= 1) {
    const record = records[i];
    const replacement = record.placeholder
      ? record.full.replace(record.placeholder, translations[i])
      : record.full.replace(
        /(<!-- ZH_[A-Z0-9_]+_BEGIN -->)[\s\S]*?(<!-- ZH_[A-Z0-9_]+_END -->)/,
        `$1\n${translations[i]}\n$2`,
      );
    output = output.slice(0, record.start) + replacement + output.slice(record.end);
  }
  return output;
}

async function translateFile(filePath, stats) {
  const original = fs.readFileSync(filePath, 'utf8');
  const records = extractRecords(original);
  if (!records.length) return;
  if (REPAIR_EMPTY) {
    const translations = [];
    for (const record of records) {
      const sourceWithoutInvisible = record.source.replace(/[\s\u200b\ufeff]/g, '');
      if (!sourceWithoutInvisible || isAlreadyChinese(record.source)) translations.push(record.source);
      else translations.push(...await callDeepSeek([record]));
    }
    fs.writeFileSync(filePath, replaceRecords(original, records, translations), 'utf8');
    stats.files += 1;
    stats.blocks += records.length;
    return;
  }
  // A normal session is comfortably within context. Split unusually large files
  // into record groups so the output JSON remains reliable.
  const groups = [];
  let group = [];
  let chars = 0;
  for (const record of records) {
    if (REPAIR_EMPTY) {
      groups.push([record]);
      continue;
    }
    if (group.length && chars + record.source.length > 12000) {
      groups.push(group);
      group = [];
      chars = 0;
    }
    group.push(record);
    chars += record.source.length;
  }
  if (group.length) groups.push(group);

  const translations = [];
  for (const current of groups) {
    if (REPAIR_EMPTY && current.length === 1 && isAlreadyChinese(current[0].source)) {
      // Some LongMemEval source turns are already Chinese. Preserve them as-is
      // instead of asking an English-to-Chinese model to emit a blank result.
      translations.push(current[0].source);
    } else {
      translations.push(...await callDeepSeek(current));
    }
  }
  fs.writeFileSync(filePath, replaceRecords(original, records, translations), 'utf8');
  stats.files += 1;
  stats.blocks += records.length;
}

async function main() {
  const selection = JSON.parse(fs.readFileSync(SELECTION, 'utf8'));
  const files = [];
  for (const item of selection.cases) {
    const caseDir = path.join(WORKPACK, 'cases', item.question_id);
    for (const name of fs.readdirSync(caseDir, { recursive: true })) {
      if (typeof name === 'string' && name.endsWith('.md')) files.push(path.join(caseDir, name));
    }
  }
  files.sort();
  const stats = { started_at: new Date().toISOString(), model: MODEL, retranslate_all: RETRANSLATE_ALL, repair_empty: REPAIR_EMPTY, files: 0, blocks: 0, errors: [], files_seen: files.length };
  let cursor = 0;
  async function worker() {
    while (true) {
      const index = cursor;
      cursor += 1;
      if (index >= files.length) return;
      try {
        await translateFile(files[index], stats);
        if (stats.files % 10 === 0 && stats.files > 0) console.log(`translated_files=${stats.files} translated_blocks=${stats.blocks} next=${index + 1}/${files.length}`);
      } catch (error) {
        stats.errors.push({ file: files[index], error: String(error) });
        console.error(`ERROR ${files[index]}: ${error}`);
      }
    }
  }
  await Promise.all(Array.from({ length: CONCURRENCY }, () => worker()));
  stats.finished_at = new Date().toISOString();
  fs.writeFileSync(REPORT, JSON.stringify(stats, null, 2) + '\n', 'utf8');
  console.log(JSON.stringify(stats, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
