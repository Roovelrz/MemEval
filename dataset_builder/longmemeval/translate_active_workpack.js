#!/usr/bin/env node

// Resume-safe first-pass translator for the activated LongMemEval workpack.
// It edits only ZH_* blocks whose content is still the exact placeholder.

const fs = require('fs');
const path = require('path');
const { execFile } = require('child_process');

const WORKPACK = path.resolve(
  __dirname,
  '../../datasets/zh_derived/longmemeval_zh/v0.1/translation_workpack',
);
const SELECTION = path.join(WORKPACK, 'active_20_selection.json');
const PLACEHOLDER = '[待翻译：请只替换本行，保留上下边界标记]';
const CURL = process.env.CURL_EXE || 'curl.exe';
const BASE_URL = 'https://oneshot-free.www.deepl.com/v1/translate';
const MAX_BATCH_CHARS = 1200;
const CONCURRENCY = Number(process.env.TRANSLATION_CONCURRENCY || 5);
const DELAY_MS = Number(process.env.TRANSLATION_DELAY_MS || 80);
const REPORT = path.join(WORKPACK, 'translation_run_report.json');

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function extractRecords(text) {
  const records = [];
  const sourceRe = /<!-- SOURCE_(QUESTION|ANSWER|TURN_\d+)_BEGIN -->\r?\n([\s\S]*?)\r?\n<!-- SOURCE_\1_END -->\r?\n\r?\n### Chinese translation — EDIT HERE\r?\n\r?\n<!-- ZH_\1_BEGIN -->\r?\n([\s\S]*?)\r?\n<!-- ZH_\1_END -->/g;
  let match;
  while ((match = sourceRe.exec(text)) !== null) {
    if (!match[3].includes(PLACEHOLDER)) continue;
    records.push({
      key: match[1],
      source: match[2].trim(),
      placeholder: match[3],
      start: match.index,
      end: sourceRe.lastIndex,
      full: match[0],
    });
  }
  return records;
}

function splitSource(source, maxChars = 1000) {
  if (source.length <= maxChars) return [source];
  const chunks = [];
  let rest = source;
  while (rest.length > maxChars) {
    let cut = rest.lastIndexOf('\n', maxChars);
    if (cut < Math.floor(maxChars * 0.55)) {
      const sentence = rest.slice(0, maxChars).search(/[.!?。！？]\s[^.!?。！？]*$/);
      cut = sentence > 0 ? sentence + 1 : maxChars;
    }
    chunks.push(rest.slice(0, cut).trim());
    rest = rest.slice(cut).trim();
  }
  if (rest) chunks.push(rest);
  return chunks;
}

function splitBatches(records) {
  const batches = [];
  let current = [];
  let size = 0;
  for (const record of records) {
    for (const chunk of splitSource(record.source)) {
      const unit = { record, chunks: [chunk] };
      const extra = chunk.length + 32;
      if (current.length && size + extra > MAX_BATCH_CHARS) {
        batches.push(current);
        current = [];
        size = 0;
      }
      current.push(unit);
      size += extra;
    }
  }
  if (current.length) batches.push(current);
  return batches;
}

function curlTranslate(query) {
  return new Promise((resolve, reject) => {
    const instanceId = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
    const sessionId = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
    const body = JSON.stringify({
      text: [query],
      target_lang: 'zh-Hans',
      source_lang: 'en',
      usage_type: 'translate',
      app_information: {
        os: 'iOS',
        os_version: '26.0',
        app_version: '26.42',
        app_build: '5443737',
        instance_id: instanceId,
      },
    });
    execFile(
      CURL,
      [
        '-k', '-sS', '--retry', '5', '--retry-all-errors', '--max-time', '90',
        '-X', 'POST', BASE_URL,
        '-H', 'Authorization: None',
        '-H', 'Content-Type: application/json',
        '-H', 'x-app-os-version: 26.0',
        '-H', `x-app-instance-id: ${instanceId}`,
        '-H', `x-app-session-id: ${sessionId}`,
        '-H', 'User-Agent: DeepL/26.42 CFNetwork/3826.600.41 Darwin/25.0.0',
        '--data', body,
      ],
      { windowsHide: true, maxBuffer: 8 * 1024 * 1024 },
      (error, stdout, stderr) => {
        if (error) {
          reject(new Error(`${error.message}; ${stderr.trim()}`));
          return;
        }
        try {
          const data = JSON.parse(stdout);
          const translated = data.translations?.[0]?.text || '';
          if (!translated) throw new Error('empty translation response');
          resolve(translated);
        } catch (parseError) {
          reject(new Error(`invalid translation response: ${parseError.message}`));
        }
      },
    );
  });
}

async function translateBatch(batch, batchNumber) {
  const token = `<KEEP_${process.pid}_${batchNumber}>`;
  const segments = batch.flatMap((unit) => unit.chunks);
  const query = segments.join(`\n\n${token}\n\n`);
  let translated;
  try {
    translated = await curlTranslate(query);
  } catch (error) {
    // A single oversized or malformed batch should not stop a resumable run.
    if (batch.length === 1 && batch[0].chunks.length === 1) throw error;
    const outputs = [];
    for (let i = 0; i < batch.length; i += 1) {
      outputs.push(...await translateBatch([batch[i]], `${batchNumber}s${i}`));
    }
    return outputs;
  }

  const parts = translated.split(token);
  if (parts.length !== segments.length) {
    if (batch.length === 1 && batch[0].chunks.length === 1) return [translated.trim()];
    const outputs = [];
    for (let i = 0; i < batch.length; i += 1) {
      outputs.push(...await translateBatch([batch[i]], `${batchNumber}s${i}`));
    }
    return outputs;
  }
  const outputs = [];
  let cursor = 0;
  for (const unit of batch) {
    outputs.push(parts.slice(cursor, cursor + unit.chunks.length).map((part) => part.trim()).join('\n\n'));
    cursor += unit.chunks.length;
  }
  return outputs;
}

function replaceRecords(text, records, translations) {
  let output = text;
  for (let i = records.length - 1; i >= 0; i -= 1) {
    const record = records[i];
    const replacement = record.full.replace(record.placeholder, translations[i] || PLACEHOLDER);
    output = output.slice(0, record.start) + replacement + output.slice(record.end);
  }
  return output;
}

async function translateFile(filePath, stats) {
  const original = fs.readFileSync(filePath, 'utf8');
  const records = extractRecords(original);
  if (!records.length) return;
  const batches = splitBatches(records);
  const translationsByRecord = records.map(() => []);
  const recordIndexes = new Map(records.map((record, index) => [record, index]));
  for (const batch of batches) {
    const result = await translateBatch(batch, stats.batches);
    stats.batches += 1;
    for (let i = 0; i < batch.length; i += 1) {
      translationsByRecord[recordIndexes.get(batch[i].record)].push(result[i] || '');
    }
    await sleep(DELAY_MS);
  }
  const translations = translationsByRecord.map((parts) => parts.join('\n\n'));
  const updated = replaceRecords(original, records, translations);
  fs.writeFileSync(filePath, updated, 'utf8');
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
  const stats = { started_at: new Date().toISOString(), files: 0, blocks: 0, batches: 0, errors: [] };
  let cursor = 0;
  async function worker() {
    while (true) {
      const index = cursor;
      cursor += 1;
      if (index >= files.length) return;
      try {
        await translateFile(files[index], stats);
        if (stats.files % 10 === 0 && stats.files > 0) {
          console.log(`translated_files=${stats.files} translated_blocks=${stats.blocks} next=${index + 1}/${files.length}`);
        }
      } catch (error) {
        stats.errors.push({ file: files[index], error: String(error) });
        console.error(`ERROR ${files[index]}: ${error}`);
      }
    }
  }
  await Promise.all(Array.from({ length: CONCURRENCY }, () => worker()));
  stats.finished_at = new Date().toISOString();
  stats.files_seen = files.length;
  fs.writeFileSync(REPORT, JSON.stringify(stats, null, 2) + '\n', 'utf8');
  console.log(JSON.stringify(stats, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
