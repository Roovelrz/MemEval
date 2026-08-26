#!/usr/bin/env node
/* Structural acceptance for the frozen LongMemEval-ZH clean export. */
const fs = require('fs');
const path = require('path');

const REPO_ROOT = path.resolve(__dirname, '../..');
const SOURCE_PATH = path.join(REPO_ROOT, '..', 'LongMemEval/data/longmemeval_s_cleaned.json');
const OUT_DIR = path.join(REPO_ROOT, 'datasets/zh_derived/longmemeval_zh/LongMemEval-ZH-20-v0.1');
const DATASET_PATH = path.join(OUT_DIR, 'dataset.json');
const SELECTION_PATH = path.join(REPO_ROOT, 'datasets/zh_derived/longmemeval_zh/v0.1/translation_workpack/active_20_selection.json');

function readJson(file) { return JSON.parse(fs.readFileSync(file, 'utf8')); }
function same(a, b) { return JSON.stringify(a) === JSON.stringify(b); }
function issue(errors, code, detail) { errors.push({ code, ...detail }); }
function hasForbiddenArtifact(value) {
  if (typeof value !== 'string') return false;
  return /SOURCE_[A-Z_]+|ZH_[A-Z_]+|English source|Chinese translation|DO NOT EDIT|EDIT HERE|translation_status|TODO|待翻译/.test(value);
}
function expectedHasAnswer(turn) {
  return Object.prototype.hasOwnProperty.call(turn, 'has_answer') ? turn.has_answer : 'NOT_PRESENT';
}

function main() {
  const dataset = readJson(DATASET_PATH);
  const source = readJson(SOURCE_PATH);
  const selection = readJson(SELECTION_PATH);
  const sourceById = new Map(source.map(x => [x.question_id, x]));
  const errors = [];
  const warnings = [];
  const selectedIds = selection.cases.map(x => x.question_id);

  if (dataset.dataset_id !== 'LongMemEval-ZH-20-v0.1') issue(errors, 'dataset_id_mismatch', { actual: dataset.dataset_id });
  if (!same(dataset.cases.map(x => x.case_id), selectedIds)) issue(errors, 'case_order_or_selection_mismatch', { expected: selectedIds, actual: dataset.cases.map(x => x.case_id) });
  if (dataset.cases.length !== 20) issue(errors, 'case_count_mismatch', { expected: 20, actual: dataset.cases.length });

  let sessionCount = 0;
  let turnCount = 0;
  let evidenceCount = 0;
  let blockCount = 0;
  for (const cleanCase of dataset.cases) {
    const original = sourceById.get(cleanCase.case_id);
    if (!original) { issue(errors, 'case_missing_in_source', { case_id: cleanCase.case_id }); continue; }
    const selected = selection.cases.find(x => x.question_id === cleanCase.case_id);
    if (cleanCase.question_type !== original.question_type || cleanCase.question_type !== selected.question_type) issue(errors, 'question_type_mismatch', { case_id: cleanCase.case_id, clean: cleanCase.question_type, source: original.question_type });
    if (!cleanCase.question || !cleanCase.question.trim()) issue(errors, 'question_missing', { case_id: cleanCase.case_id });
    if (!cleanCase.gold_answer || !cleanCase.gold_answer.trim()) issue(errors, 'gold_answer_missing', { case_id: cleanCase.case_id });
    if (hasForbiddenArtifact(cleanCase.question) || hasForbiddenArtifact(cleanCase.gold_answer)) issue(errors, 'workpack_artifact_in_case_text', { case_id: cleanCase.case_id });
    if (!same(cleanCase.answer_session_ids, original.answer_session_ids)) issue(errors, 'answer_session_ids_changed', { case_id: cleanCase.case_id, expected: original.answer_session_ids, actual: cleanCase.answer_session_ids });

    const ids = original.haystack_session_ids;
    const dates = original.haystack_dates;
    const sessions = cleanCase.sessions;
    sessionCount += sessions.length;
    blockCount += 2;
    evidenceCount += sessions.filter(x => x.is_evidence_session).length;
    if (sessions.length !== ids.length) issue(errors, 'session_count_changed', { case_id: cleanCase.case_id, expected: ids.length, actual: sessions.length });
    if (sessions.length !== dates.length) issue(errors, 'timestamp_count_changed', { case_id: cleanCase.case_id, expected: dates.length, actual: sessions.length });
    if (sessions.length !== original.haystack_sessions.length) issue(errors, 'conversation_count_changed', { case_id: cleanCase.case_id, expected: original.haystack_sessions.length, actual: sessions.length });

    for (let i = 0; i < Math.max(sessions.length, ids.length); i += 1) {
      const session = sessions[i];
      const expectedId = ids[i];
      if (!session) { issue(errors, 'session_missing', { case_id: cleanCase.case_id, session_index: i, expected: expectedId }); continue; }
      if (session.session_id !== expectedId) issue(errors, 'session_id_changed', { case_id: cleanCase.case_id, session_index: i, expected: expectedId, actual: session.session_id });
      if (session.timestamp !== dates[i]) issue(errors, 'timestamp_changed', { case_id: cleanCase.case_id, session_index: i, expected: dates[i], actual: session.timestamp });
      const expectedEvidence = original.answer_session_ids.includes(expectedId);
      if (session.is_evidence_session !== expectedEvidence) issue(errors, 'evidence_flag_changed', { case_id: cleanCase.case_id, session_id: session.session_id, expected: expectedEvidence, actual: session.is_evidence_session });
      const originalTurns = original.haystack_sessions[i] || [];
      if (session.turns.length !== originalTurns.length) issue(errors, 'turn_count_changed', { case_id: cleanCase.case_id, session_id: session.session_id, expected: originalTurns.length, actual: session.turns.length });
      turnCount += session.turns.length;
      blockCount += session.turns.length;
      for (let j = 0; j < Math.max(session.turns.length, originalTurns.length); j += 1) {
        const turn = session.turns[j];
        const originalTurn = originalTurns[j];
        if (!turn || !originalTurn) continue;
        const expectedAnswer = expectedHasAnswer(originalTurn);
        if (turn.turn_index !== j) issue(errors, 'turn_index_changed', { case_id: cleanCase.case_id, session_id: session.session_id, turn_index: j, actual: turn.turn_index });
        if (turn.role !== originalTurn.role) issue(errors, 'role_changed', { case_id: cleanCase.case_id, session_id: session.session_id, turn_index: j, expected: originalTurn.role, actual: turn.role });
        if (!same(turn.has_answer, expectedAnswer)) issue(errors, 'has_answer_changed', { case_id: cleanCase.case_id, session_id: session.session_id, turn_index: j, expected: expectedAnswer, actual: turn.has_answer });
        if (hasForbiddenArtifact(turn.content)) issue(errors, 'workpack_artifact_in_turn', { case_id: cleanCase.case_id, session_id: session.session_id, turn_index: j });
        if (originalTurn.content && !turn.content) issue(errors, 'nonempty_source_has_empty_translation', { case_id: cleanCase.case_id, session_id: session.session_id, turn_index: j });
      }
    }
  }

  // The clean JSON itself must not retain workpack-only fields or markers.
  const serialized = JSON.stringify(dataset);
  if (/SOURCE_|ZH_|translation_status|TODO|DO NOT EDIT|EDIT HERE|English source|Chinese translation/.test(serialized)) issue(errors, 'forbidden_workpack_artifact_in_dataset', {});
  for (const c of dataset.cases) {
    for (const s of c.sessions) {
      if (Object.prototype.hasOwnProperty.call(s, '_meta')) issue(errors, 'private_meta_field_in_dataset', { case_id: c.case_id, session_id: s.session_id });
      for (const t of s.turns) if (Object.prototype.hasOwnProperty.call(t, '_meta')) issue(errors, 'private_meta_field_in_dataset', { case_id: c.case_id, session_id: s.session_id, turn_index: t.turn_index });
    }
  }
  if (sessionCount !== 964) warnings.push({ code: 'expected_count_reference', field: 'session_count', expected: 964, actual: sessionCount });
  if (turnCount !== 10055) warnings.push({ code: 'expected_count_reference', field: 'turn_count', expected: 10055, actual: turnCount });
  if (blockCount !== 10095) warnings.push({ code: 'expected_count_reference', field: 'translated_block_count', expected: 10095, actual: blockCount });

  const report = {
    schema_version: 'longmemeval_zh_integrity_v1',
    dataset_id: dataset.dataset_id,
    checked_at_utc: new Date().toISOString(),
    status: errors.length ? 'FAIL' : 'PASS',
    counts: { case_count: dataset.cases.length, session_count: sessionCount, turn_count: turnCount, translated_block_count: blockCount, evidence_session_count: evidenceCount },
    checks: {
      session_count_equal_to_source: !errors.some(x => x.code === 'session_count_changed'),
      session_id_equal_to_source: !errors.some(x => x.code === 'session_id_changed'),
      timestamp_equal_to_source: !errors.some(x => x.code === 'timestamp_changed'),
      evidence_flag_equal_to_source: !errors.some(x => x.code === 'evidence_flag_changed'),
      has_answer_equal_to_source: !errors.some(x => x.code === 'has_answer_changed'),
      role_equal_to_source: !errors.some(x => x.code === 'role_changed'),
      question_and_gold_answer_present: !errors.some(x => x.code === 'question_missing' || x.code === 'gold_answer_missing'),
      clean_has_no_workpack_artifacts: !errors.some(x => x.code.includes('artifact') || x.code.includes('private_meta')),
    },
    errors,
    warnings,
  };
  fs.writeFileSync(path.join(OUT_DIR, 'integrity_report.json'), JSON.stringify(report, null, 2) + '\n', 'utf8');
  console.log(JSON.stringify(report, null, 2));
  if (errors.length) process.exitCode = 1;
}
main();
