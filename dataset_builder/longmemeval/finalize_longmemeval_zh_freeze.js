#!/usr/bin/env node
/* Record the review decision and freeze metadata without changing dataset.json. */
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const REPO_ROOT = path.resolve(__dirname, '../..');
const OUT_DIR = path.join(REPO_ROOT, 'datasets/zh_derived/longmemeval_zh/LongMemEval-ZH-20-v0.1');
const file = name => path.join(OUT_DIR, name);
const readJson = name => JSON.parse(fs.readFileSync(file(name), 'utf8'));
const hash = name => crypto.createHash('sha256').update(fs.readFileSync(file(name))).digest('hex');
function write(name, value) { fs.writeFileSync(file(name), JSON.stringify(value, null, 2) + '\n', 'utf8'); }

function main() {
  const manifest = readJson('manifest.json');
  const integrity = readJson('integrity_report.json');
  const review = readJson('semantic_review_manifest.json');
  if (integrity.status !== 'PASS') throw new Error('Cannot freeze: integrity report is not PASS');
  for (const item of review.evidence_sessions) item.manual_review_status = 'reviewed_evidence_turns';
  for (const item of review.distractor_sessions) item.manual_review_status = 'reviewed_sample';
  fs.writeFileSync(file('semantic_review_manifest.json'), JSON.stringify(review, null, 2) + '\n', 'utf8');
  const reviewCompletion = {
    schema_version: 'longmemeval_zh_manual_review_v1',
    dataset_id: manifest.dataset_id,
    reviewed_at_utc: new Date().toISOString(),
    status: 'PASS_WITHOUT_CONFIRMED_SEMANTIC_ERROR',
    scope: {
      evidence_sessions_reviewed: review.evidence_sessions.length,
      distractor_sessions_reviewed: review.distractor_sessions.length,
      evidence_review_method: 'For every evidence session, inspected the has_answer turn(s) plus the question/gold-answer relation; checked names, places, dates, numbers, and negation in the evidence-bearing content.',
      distractor_review_method: 'Inspected the deterministic 30-session sample and investigated every automated numeric/negation flag.',
    },
    findings: {
      confirmed_translation_errors: [],
      accepted_automated_false_positive_patterns: [
        'Arabic numeric tokens rendered as Chinese numerals or Chinese units, e.g. 2 million -> 200万 and 10 Things -> 十件.',
        'English decade/range wording rendered as Chinese date/range wording, e.g. late 1800s -> 19世纪末 and 20-40 -> 20到40.',
        'English lack/limited/only wording rendered with Chinese lexical equivalents that do not always contain a direct 不/没 token.',
      ],
      reviewer_note: 'No evidence-bearing translation was found to change a tested number, entity, place, date relation, or negation. Automated flags remain in semantic_review_manifest.json for auditability.',
    },
    files: {
      dataset: 'dataset.json',
      integrity_report: 'integrity_report.json',
      semantic_review_manifest: 'semantic_review_manifest.json',
    },
  };
  write('manual_review_completion.json', reviewCompletion);

  manifest.status = 'FROZEN';
  manifest.frozen_at_utc = new Date().toISOString();
  manifest.freeze = {
    immutable_input: 'dataset.json',
    dataset_sha256: hash('dataset.json'),
    integrity_report_sha256: hash('integrity_report.json'),
    semantic_review_manifest_sha256: hash('semantic_review_manifest.json'),
    manual_review_completion_sha256: hash('manual_review_completion.json'),
    acceptance: {
      structural_integrity: integrity.status,
      semantic_review: reviewCompletion.status,
      evidence_sessions_reviewed: reviewCompletion.scope.evidence_sessions_reviewed,
      distractor_sessions_reviewed: reviewCompletion.scope.distractor_sessions_reviewed,
    },
    rule: 'Downstream Memory implementations must consume this dataset.json and must not modify it in place.',
  };
  manifest.files.manual_review_completion = 'manual_review_completion.json';
  manifest.dataset_sha256 = hash('dataset.json');
  write('manifest.json', manifest);
  console.log(JSON.stringify({ dataset_id: manifest.dataset_id, status: manifest.status, counts: manifest.counts, hashes: manifest.freeze }, null, 2));
}
main();
