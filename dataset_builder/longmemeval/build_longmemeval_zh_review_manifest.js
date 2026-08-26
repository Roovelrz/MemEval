#!/usr/bin/env node
/* Build a separate source-vs-Chinese review artifact. It is not eval input. */
const fs = require('fs');
const path = require('path');

const REPO_ROOT = path.resolve(__dirname, '../..');
const OUT_DIR = path.join(REPO_ROOT, 'datasets/zh_derived/longmemeval_zh/LongMemEval-ZH-20-v0.1');
const data = JSON.parse(fs.readFileSync(path.join(OUT_DIR, 'dataset.json'), 'utf8'));
const sourcePath = path.join(REPO_ROOT, '..', 'LongMemEval/data/longmemeval_s_cleaned.json');
const source = JSON.parse(fs.readFileSync(sourcePath, 'utf8'));
const sourceById = new Map(source.map(x => [x.question_id, x]));

function numberTokens(text) {
  return (text.match(/\b\d+(?:[.,:/-]\d+)*%?/g) || []).map(x => x.replace(/[,]/g, ''));
}
function counts(items) {
  const m = new Map();
  for (const x of items) m.set(x, (m.get(x) || 0) + 1);
  return Object.fromEntries([...m.entries()].sort());
}
function negationRisk(sourceText, zhText) {
  const sourceNeg = /\b(no|not|never|cannot|can't|don't|doesn't|didn't|won't|without|neither|nor|unable|avoid|unless|only|except)\b/i.test(sourceText);
  const zhNeg = /不|没|无|未|从不|不能|无法|不要|避免|除非|仅|只有|除了/.test(zhText);
  return sourceNeg && !zhNeg;
}
function semanticFlags(sourceText, zhText) {
  const sourceNumbers = counts(numberTokens(sourceText));
  const zhNumbers = counts(numberTokens(zhText));
  const missingNumbers = Object.keys(sourceNumbers).filter(x => (zhNumbers[x] || 0) < sourceNumbers[x]);
  return {
    missing_numeric_tokens: missingNumbers,
    numeric_token_mismatch: missingNumbers.length > 0,
    possible_negation_mismatch: negationRisk(sourceText, zhText),
  };
}
function seededRandom(seed) {
  let state = seed >>> 0;
  return () => { state = (1664525 * state + 1013904223) >>> 0; return state / 0x100000000; };
}
function key(caseId, sessionId) { return `${caseId}/${sessionId}`; }

function main() {
  const evidence = [];
  const distractors = [];
  const allDistractors = [];
  for (const c of data.cases) {
    const o = sourceById.get(c.case_id);
    const sourceSessions = new Map(o.haystack_session_ids.map((id, i) => [id, o.haystack_sessions[i]]));
    for (const s of c.sessions) {
      const sourceTurns = sourceSessions.get(s.session_id) || [];
      const turns = s.turns.map((t, i) => ({
        turn_index: i,
        role: t.role,
        source: sourceTurns[i] ? sourceTurns[i].content : '',
        chinese: t.content,
        flags: semanticFlags(sourceTurns[i] ? sourceTurns[i].content : '', t.content),
      }));
      const item = {
        case_id: c.case_id,
        question_type: c.question_type,
        session_id: s.session_id,
        timestamp: s.timestamp,
        is_evidence_session: s.is_evidence_session,
        manual_review_status: 'pending_manual_review',
        turns,
      };
      if (s.is_evidence_session) evidence.push(item);
      else allDistractors.push(item);
    }
  }
  const random = seededRandom(20260825);
  allDistractors.sort(() => random() - 0.5);
  distractors.push(...allDistractors.slice(0, 30));
  const review = {
    schema_version: 'longmemeval_zh_semantic_review_v1',
    dataset_id: data.dataset_id,
    generated_at_utc: new Date().toISOString(),
    purpose: 'Separate reviewer artifact; contains English source and must never be passed to Eval as dataset input.',
    sampling: { all_evidence_sessions: evidence.length, random_distractor_sessions: distractors.length, distractor_seed: 20260825 },
    review_instructions: [
      'Review every evidence session below and mark manual_review_status=passed or needs_fix in a reviewer copy.',
      'Review the 30 deterministic distractor sessions and focus on numbers, names, places, dates, and negation.',
      'Automated flags are leads, not proof; a missing flag does not establish semantic correctness.',
    ],
    automated_summary: {
      evidence_sessions_with_numeric_flags: evidence.filter(s => s.turns.some(t => t.flags.numeric_token_mismatch)).length,
      evidence_sessions_with_negation_flags: evidence.filter(s => s.turns.some(t => t.flags.possible_negation_mismatch)).length,
      distractor_sessions_with_numeric_flags: distractors.filter(s => s.turns.some(t => t.flags.numeric_token_mismatch)).length,
      distractor_sessions_with_negation_flags: distractors.filter(s => s.turns.some(t => t.flags.possible_negation_mismatch)).length,
    },
    evidence_sessions: evidence,
    distractor_sessions: distractors,
  };
  fs.writeFileSync(path.join(OUT_DIR, 'semantic_review_manifest.json'), JSON.stringify(review, null, 2) + '\n', 'utf8');
  console.log(JSON.stringify({
    output: path.join(OUT_DIR, 'semantic_review_manifest.json'),
    sampling: review.sampling,
    automated_summary: review.automated_summary,
  }, null, 2));
}
main();
