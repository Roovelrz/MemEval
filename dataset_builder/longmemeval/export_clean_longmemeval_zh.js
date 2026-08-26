#!/usr/bin/env node
/*
 * Export the human-editable LongMemEval translation workpack into a clean,
 * source-free dataset for evaluation. The workpack is never modified.
 */
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const REPO_ROOT = path.resolve(__dirname, '../..');
const WORKPACK = path.join(REPO_ROOT, 'datasets/zh_derived/longmemeval_zh/v0.1/translation_workpack');
const SOURCE_PATH = path.join(REPO_ROOT, '..', 'LongMemEval/data/longmemeval_s_cleaned.json');
const OUT_DIR = path.join(REPO_ROOT, 'datasets/zh_derived/longmemeval_zh/LongMemEval-ZH-20-v0.1');
const SELECTION_PATH = path.join(WORKPACK, 'active_20_selection.json');

function read(file) { return fs.readFileSync(file, 'utf8'); }
function writeJson(file, value) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, JSON.stringify(value, null, 2) + '\n', 'utf8');
}
function sha256(file) {
  return crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
}
function trimBlock(value) {
  // Translation files intentionally use a blank line around marker contents.
  // Remove only that framing whitespace, not internal formatting/newlines.
  return value.replace(/^\s*\n?/, '').replace(/\n?\s*$/, '');
}
function marker(text, name) {
  const re = new RegExp(`<!-- ${name}_BEGIN -->([^]*?)<!-- ${name}_END -->`);
  const m = text.match(re);
  if (!m) throw new Error(`missing marker ${name}`);
  return trimBlock(m[1]);
}
function frontmatter(text, label = 'document') {
  const m = text.match(/^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/);
  if (!m) throw new Error(`missing frontmatter: ${label}`);
  const result = {};
  for (const line of m[1].split(/\r?\n/)) {
    const item = line.match(/^([A-Za-z0-9_]+):\s*(.*)$/);
    if (!item) continue;
    const key = item[1];
    let value = item[2].trim();
    if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
      value = value.slice(1, -1);
    } else if (value.startsWith('[') && value.endsWith(']')) {
      try { value = JSON.parse(value); } catch (_) { value = value.slice(1, -1).split(',').map(v => v.trim()); }
    } else if (/^(true|false)$/.test(value)) {
      value = value === 'true';
    } else if (/^-?\d+$/.test(value)) {
      value = Number(value);
    }
    result[key] = value;
  }
  return result;
}
function listMarkdownFiles(dir) {
  return fs.readdirSync(dir).filter(x => x.endsWith('.md')).sort().map(x => path.join(dir, x));
}
function parseQuestionAnswer(file) {
  const text = read(file);
  const fm = frontmatter(text, file);
  return {
    question: marker(text, 'ZH_QUESTION'),
    gold_answer: marker(text, 'ZH_ANSWER'),
    _meta: fm,
  };
}
function toHasAnswer(raw) {
  raw = raw.replace(/^"|"$/g, '');
  if (raw === 'true') return true;
  if (raw === 'false') return false;
  if (raw === 'NOT_PRESENT') return 'NOT_PRESENT';
  throw new Error(`unexpected has_answer value: ${raw}`);
}
function parseSession(file) {
  const text = read(file);
  const fm = frontmatter(text, file);
  const turns = [];
  const headers = [...text.matchAll(/^## Turn (\d+) — ([^\r\n]+)$/gm)];
  for (let i = 0; i < headers.length; i += 1) {
    const start = headers[i].index;
    const end = i + 1 < headers.length ? headers[i + 1].index : text.length;
    const section = text.slice(start, end);
    const h = section.match(/^## Turn (\d+) — ([^\r\n]+)$/m);
    const role = (section.match(/^- role: `([^`]+)`/m) || [])[1];
    const answerRaw = (section.match(/^- has_answer: `([^`]+)`/m) || [])[1];
    if (!role || answerRaw === undefined) throw new Error(`missing role/has_answer in ${file} turn ${h && h[1]}`);
    const turnNo = Number(h[1]);
    turns.push({
      turn_index: turnNo,
      role,
      content: marker(section, `ZH_TURN_${String(turnNo).padStart(3, '0')}`),
      has_answer: toHasAnswer(answerRaw),
    });
  }
  if (turns.length !== Number(fm.turn_count)) {
    throw new Error(`${file}: frontmatter turn_count=${fm.turn_count}, parsed=${turns.length}`);
  }
  return {
    session_id: fm.session_id,
    timestamp: fm.timestamp,
    is_evidence_session: fm.is_evidence_session,
    turns,
    _meta: fm,
  };
}
function cleanCase(caseId, caseType, caseDir) {
  const qa = parseQuestionAnswer(path.join(caseDir, 'question_answer.md'));
  const sessions = listMarkdownFiles(path.join(caseDir, 'sessions')).map(parseSession);
  const fm = qa._meta;
  if (fm.question_id !== caseId) throw new Error(`QA question_id mismatch for ${caseId}`);
  for (const session of sessions) {
    if (session._meta.question_id !== caseId) throw new Error(`session question_id mismatch for ${caseId}`);
    delete session._meta;
  }
  delete qa._meta;
  return {
    case_id: caseId,
    question_type: caseType,
    question_date: fm.question_date,
    question: qa.question,
    gold_answer: qa.gold_answer,
    answer_session_ids: fm.answer_session_ids,
    sessions,
  };
}
function main() {
  const selection = JSON.parse(read(SELECTION_PATH));
  const source = JSON.parse(read(SOURCE_PATH));
  const sourceById = new Map(source.map((x, i) => [x.question_id, { ...x, _source_index: i }]));
  const cases = selection.cases.map(item => {
    const dir = path.join(WORKPACK, 'cases', item.question_id);
    if (!fs.existsSync(dir)) throw new Error(`missing selected case directory: ${dir}`);
    return cleanCase(item.question_id, item.question_type, dir);
  });
  const missing = cases.filter(x => !sourceById.has(x.case_id)).map(x => x.case_id);
  if (missing.length) throw new Error(`selected case IDs absent from source: ${missing.join(', ')}`);
  const dataset = {
    schema_version: 'longmemeval_zh_clean_v1',
    dataset_id: 'LongMemEval-ZH-20-v0.1',
    language: 'zh-CN',
    source: 'LongMemEval-S cleaned',
    cases,
  };
  const counts = {
    case_count: cases.length,
    session_count: cases.reduce((n, c) => n + c.sessions.length, 0),
    turn_count: cases.reduce((n, c) => n + c.sessions.reduce((m, s) => m + s.turns.length, 0), 0),
    translated_block_count: cases.reduce((n, c) => n + 2 + c.sessions.reduce((m, s) => m + s.turns.length, 0), 0),
    evidence_session_count: cases.reduce((n, c) => n + c.sessions.filter(s => s.is_evidence_session).length, 0),
  };
  fs.mkdirSync(OUT_DIR, { recursive: true });
  const datasetPath = path.join(OUT_DIR, 'dataset.json');
  writeJson(datasetPath, dataset);
  const manifest = {
    dataset_id: 'LongMemEval-ZH-20-v0.1',
    status: 'candidate_pending_integrity_acceptance',
    build_time_utc: new Date().toISOString(),
    language: 'zh-CN',
    selected_case_ids: cases.map(c => c.case_id),
    selected_question_types: Object.fromEntries(cases.map(c => [c.case_id, c.question_type])),
    counts,
    source_dataset: {
      name: 'LongMemEval-S cleaned',
      path: SOURCE_PATH,
      sha256: sha256(SOURCE_PATH),
      git_commit: (() => { try { return require('child_process').execFileSync('git', ['-C', path.dirname(path.dirname(SOURCE_PATH)), 'rev-parse', 'HEAD'], { encoding: 'utf8' }).trim(); } catch (_) { return null; } })(),
    },
    translation: {
      final_model: 'deepseek-v4-flash',
      workpack: path.relative(REPO_ROOT, WORKPACK),
      provenance: 'DeepSeek final pass for remaining blocks; existing historical translations retained; Baidu is not used in the remaining-translation pipeline.',
    },
    clean_schema: {
      case_fields: ['case_id', 'question_type', 'question_date', 'question', 'gold_answer', 'answer_session_ids', 'sessions'],
      session_fields: ['session_id', 'timestamp', 'is_evidence_session', 'turns'],
      turn_fields: ['turn_index', 'role', 'content', 'has_answer'],
      has_answer_encoding: ['true', 'false', 'NOT_PRESENT'],
      excluded_from_clean: ['English source', 'SOURCE markers', 'ZH markers', 'TODO/status', 'translation instructions', 'workpack frontmatter'],
    },
    files: { dataset: 'dataset.json' },
    dataset_sha256: sha256(datasetPath),
  };
  writeJson(path.join(OUT_DIR, 'manifest.json'), manifest);
  console.log(JSON.stringify({ out_dir: OUT_DIR, counts, dataset_sha256: manifest.dataset_sha256 }, null, 2));
}
main();
