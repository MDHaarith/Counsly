#!/usr/bin/env node

import { existsSync, readFileSync } from 'node:fs';
import { resolve, dirname, basename } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { createInterface } from 'node:readline/promises';
import { stdin as input, stdout as output } from 'node:process';

type KeyStats = {
  website?: string | null;
  approved_intake_total?: number | null;
  num_branches?: number | null;
  placement_record_pct?: number | null;
  nba_accredited_ratio?: number | null;
  autonomous?: boolean;
  trend_direction?: string | null;
  scraped?: boolean;
  naac_grade?: string | null;
  nirf_rank?: number | null;
  placement_pct_web?: number | null;
  avg_ctc_lpa?: number | null;
  faculty_count?: number | null;
  research_count?: number | null;
};

type RankingEntry = {
  rank: number;
  college_code: string;
  college_name: string;
  district: string;
  composite_score: number;
  dimension_scores: Record<string, number>;
  key_stats: KeyStats;
};

type RankingPayload = {
  metadata: {
    algorithm_version?: string;
    generation_date?: string;
    total_colleges_ranked?: number;
    dimension_weights?: Record<string, number>;
    methodology?: Record<string, string>;
  };
  rankings: {
    overall: RankingEntry[];
    by_community: Record<string, RankingEntry[]>;
    by_branch: Record<string, RankingEntry[]>;
    by_district: Record<string, RankingEntry[]>;
  };
};

type JsonValue = Record<string, unknown>;

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const REPO_ROOT = resolve(__dirname, '..');
const ALLOTEMENT_ROOT = resolve(REPO_ROOT, 'Allotement');

const PATHS = {
  rankingJson: resolve(ALLOTEMENT_ROOT, 'data', 'rankings', 'college_rankings.json'),
  rankingCsv: resolve(ALLOTEMENT_ROOT, 'data', 'rankings', 'college_rankings.csv'),
  allotementQa: resolve(REPO_ROOT, 'qa', 'reports', 'allotement_summary.json'),
  collegeInfoQa: resolve(REPO_ROOT, 'qa', 'reports', 'college_info_summary.json'),
  geoQa: resolve(REPO_ROOT, 'qa', 'reports', 'geo_summary.json'),
  grlQa: resolve(REPO_ROOT, 'qa', 'reports', 'grl_summary.json'),
  pipelineManifest: resolve(ALLOTEMENT_ROOT, 'data', 'processed', 'reports', 'training_pipeline_manifest.json'),
  repoReadme: resolve(REPO_ROOT, 'README.md'),
  allotementReadme: resolve(ALLOTEMENT_ROOT, 'README.md'),
  howToUse: resolve(ALLOTEMENT_ROOT, 'HOW_TO_USE.md'),
  dataRequirements: resolve(REPO_ROOT, '03-data-requirements.md'),
};

const COMMANDS = {
  refreshRanking: ['python3', 'scripts/college_ranking.py', '--skip-scrape'],
  runQa: ['python3', 'qa/run_all_reports.py'],
  refreshTraining: ['python3', 'scripts/training_pipeline.py', '--skip-batch'],
};

const rl = createInterface({ input, output });

function clearScreen() {
  output.write('\x1Bc');
}

function header(title: string, subtitle?: string) {
  clearScreen();
  console.log(`=== ${title} ===`);
  if (subtitle) console.log(subtitle);
  console.log('');
}

function truncate(value: string, max: number) {
  if (value.length <= max) return value;
  return `${value.slice(0, Math.max(0, max - 1))}…`;
}

function formatNumber(value?: number | null, digits = 2) {
  if (value == null || Number.isNaN(value)) return '-';
  return value.toFixed(digits);
}

function formatPercent(value?: number | null) {
  if (value == null || Number.isNaN(value)) return '-';
  return `${value.toFixed(1)}%`;
}

function formatInt(value?: number | null) {
  if (value == null || Number.isNaN(value)) return '-';
  return Math.round(value).toLocaleString('en-US');
}

function safeReadJson(path: string): JsonValue | null {
  if (!existsSync(path)) return null;
  const raw = readFileSync(path, 'utf8');
  const normalized = raw
    .replace(/\bNaN\b/g, 'null')
    .replace(/\bInfinity\b/g, 'null')
    .replace(/\b-Infinity\b/g, 'null');
  return JSON.parse(normalized) as JsonValue;
}

function safeReadText(path: string): string | null {
  if (!existsSync(path)) return null;
  return readFileSync(path, 'utf8');
}

function loadRankingPayload(path = PATHS.rankingJson): RankingPayload | null {
  const payload = safeReadJson(path);
  return payload as RankingPayload | null;
}

function table(entries: RankingEntry[], limit = 20) {
  console.log('Rk  Code  Score  District         College');
  console.log('--  ----  -----  ----------------  ----------------------------------------');
  for (const entry of entries.slice(0, limit)) {
    const rank = String(entry.rank).padStart(3);
    const code = entry.college_code.padStart(4);
    const score = entry.composite_score.toFixed(2).padStart(6);
    const district = truncate(entry.district || '-', 16).padEnd(16);
    const college = truncate(entry.college_name, 72);
    console.log(`${rank}  ${code}  ${score}  ${district}  ${college}`);
  }
}

async function pause(message = 'Press Enter to continue') {
  await rl.question(`${message} `);
}

async function chooseFromList(title: string, values: string[], subtitle?: string) {
  header(title, subtitle);
  values.forEach((value, index) => console.log(`${String(index + 1).padStart(2)}. ${value}`));
  console.log(' 0. Back');
  console.log('');
  const answer = (await rl.question('Selection: ')).trim();
  if (!answer || answer === '0') return null;
  const index = Number(answer);
  if (!Number.isInteger(index) || index < 1 || index > values.length) return null;
  return values[index - 1];
}

function uniqueSortedKeys(record: Record<string, RankingEntry[]>) {
  return Object.keys(record).sort((a, b) => a.localeCompare(b));
}

function runCommand(command: string[], cwd: string) {
  header('Running command', `${cwd}\n$ ${command.join(' ')}`);
  const result = spawnSync(command[0], command.slice(1), {
    cwd,
    stdio: 'inherit',
  });
  console.log('');
  if (result.status !== 0) console.log(`Command failed with exit code ${result.status ?? 1}.`);
  else console.log('Command completed successfully.');
}

function dashboardStats() {
  const ranking = loadRankingPayload();
  const allotement = safeReadJson(PATHS.allotementQa) as any;
  const college = safeReadJson(PATHS.collegeInfoQa) as any;
  const geo = safeReadJson(PATHS.geoQa) as any;
  const grl = safeReadJson(PATHS.grlQa) as any;
  const manifest = safeReadJson(PATHS.pipelineManifest) as any;

  return {
    ranking,
    allotement,
    college,
    geo,
    grl,
    manifest,
  };
}

async function showDashboard() {
  const stats = dashboardStats();
  const ranking = stats.ranking;
  const training = stats.allotement?.training;
  const rankings = stats.allotement?.rankings;
  const filteredCollege = stats.college?.filtered;
  const geoActive = stats.geo?.active_clean_output;
  const grl = stats.grl;
  const manifest = stats.manifest;

  header('Data Extractor Dashboard', basename(REPO_ROOT));
  console.log('Core datasets');
  console.log(`- Training-ready allotment rows: ${formatInt(training?.row_count)}`);
  console.log(`- Ranked colleges: ${formatInt(ranking?.metadata?.total_colleges_ranked ?? ranking?.rankings?.overall?.length)}`);
  console.log(`- Filtered college info count: ${formatInt(filteredCollege?.count)}`);
  console.log(`- General rank list rows: ${formatInt(grl?.row_count)}`);
  console.log(`- Active geo resolved count: ${formatInt(geoActive?.count)}`);
  console.log('');
  console.log('Quality signals');
  console.log(`- Ranking rows missing district: ${formatInt(rankings?.missing_district_rows)} (${formatPercent(rankings?.missing_district_pct)})`);
  console.log(`- Invalid community rows: ${formatInt(training?.invalid_community_rows)}`);
  console.log(`- Non-numeric rank rows: ${formatInt(training?.non_numeric_rank_rows)}`);
  console.log(`- Geo unresolved count: ${formatInt(stats.geo?.active_unresolved?.count)}`);
  console.log('');
  console.log('Pipeline');
  console.log(`- Training kept rows: ${formatInt(manifest?.training_kept_rows)}`);
  console.log(`- Training removed rows: ${formatInt(manifest?.training_removed_rows)}`);
  console.log(`- Batch skipped: ${String(manifest?.batch_skipped ?? '-')}`);
  console.log('');
  if (ranking?.rankings?.overall?.length) {
    console.log('Top 10 overall');
    console.log('');
    table(ranking.rankings.overall, 10);
    console.log('');
  }
  await pause();
}

async function showCollegeDetail(entry: RankingEntry) {
  header(`College ${entry.college_code}`, entry.college_name);
  console.log(`Rank            : ${entry.rank}`);
  console.log(`Composite score : ${formatNumber(entry.composite_score)}`);
  console.log(`District        : ${entry.district || '-'}`);
  console.log('');
  console.log('Dimension scores');
  for (const [name, value] of Object.entries(entry.dimension_scores)) {
    console.log(`- ${name}: ${formatNumber(value)}`);
  }
  console.log('');
  console.log('Key stats');
  console.log(`- Website: ${entry.key_stats.website || '-'}`);
  console.log(`- Approved intake total: ${entry.key_stats.approved_intake_total ?? '-'}`);
  console.log(`- Branches: ${entry.key_stats.num_branches ?? '-'}`);
  console.log(`- Placement record %: ${formatPercent(entry.key_stats.placement_record_pct)}`);
  console.log(`- NBA accredited ratio: ${formatNumber(entry.key_stats.nba_accredited_ratio)}`);
  console.log(`- Autonomous: ${entry.key_stats.autonomous ? 'yes' : 'no'}`);
  console.log(`- Trend direction: ${entry.key_stats.trend_direction ?? '-'}`);
  console.log(`- Scraped signals present: ${entry.key_stats.scraped ? 'yes' : 'no'}`);
  console.log(`- NAAC grade: ${entry.key_stats.naac_grade || '-'}`);
  console.log(`- NIRF rank: ${entry.key_stats.nirf_rank ?? '-'}`);
  console.log(`- Placement % web: ${formatPercent(entry.key_stats.placement_pct_web)}`);
  console.log(`- Avg CTC LPA: ${formatNumber(entry.key_stats.avg_ctc_lpa)}`);
  console.log(`- Faculty count: ${entry.key_stats.faculty_count ?? '-'}`);
  console.log(`- Research count: ${entry.key_stats.research_count ?? '-'}`);
  console.log('');
  await pause();
}

async function showRankingList(title: string, entries: RankingEntry[]) {
  header(title, `Showing top ${Math.min(25, entries.length)} of ${entries.length}`);
  table(entries, 25);
  console.log('');
  console.log('Type a college code to inspect it, or press Enter to go back.');
  const answer = (await rl.question('Code: ')).trim();
  if (!answer) return;
  const match = entries.find((entry) => entry.college_code === answer);
  if (match) await showCollegeDetail(match);
}

async function browseBucket(title: string, buckets: Record<string, RankingEntry[]>) {
  const keys = uniqueSortedKeys(buckets);
  const chosen = await chooseFromList(title, keys, `Choose one item, or type 0 to go back. Total: ${keys.length}`);
  if (!chosen) return;
  await showRankingList(`${title}: ${chosen}`, buckets[chosen] ?? []);
}

async function searchRanking(payload: RankingPayload) {
  header('Search ranking');
  const query = (await rl.question('Search by code or name: ')).trim().toLowerCase();
  if (!query) return;
  const matches = payload.rankings.overall.filter((entry) =>
    entry.college_code.toLowerCase().includes(query) || entry.college_name.toLowerCase().includes(query)
  );
  if (!matches.length) {
    console.log('No matches found.');
    console.log('');
    await pause();
    return;
  }
  await showRankingList(`Search results for "${query}"`, matches);
}

async function rankingExplorer() {
  const payload = loadRankingPayload();
  if (!payload) {
    header('Ranking explorer');
    console.log(`Missing file: ${PATHS.rankingJson}`);
    console.log('');
    await pause();
    return;
  }

  while (true) {
    header('Ranking Explorer', PATHS.rankingJson);
    console.log('1. Overview');
    console.log('2. Top overall colleges');
    console.log('3. Browse by community');
    console.log('4. Browse by branch');
    console.log('5. Browse by district');
    console.log('6. Search college');
    console.log('7. Methodology');
    console.log('0. Back');
    console.log('');

    const choice = (await rl.question('Selection: ')).trim();
    if (choice === '0') return;
    if (choice === '1') {
      header('Ranking Overview');
      console.log(`Algorithm version : ${payload.metadata.algorithm_version ?? '-'}`);
      console.log(`Generated         : ${payload.metadata.generation_date ?? '-'}`);
      console.log(`Colleges ranked   : ${payload.metadata.total_colleges_ranked ?? payload.rankings.overall.length}`);
      console.log(`Communities       : ${Object.keys(payload.rankings.by_community).length}`);
      console.log(`Branches          : ${Object.keys(payload.rankings.by_branch).length}`);
      console.log(`Districts         : ${Object.keys(payload.rankings.by_district).length}`);
      console.log('');
      table(payload.rankings.overall, 10);
      console.log('');
      await pause();
    } else if (choice === '2') await showRankingList('Overall ranking', payload.rankings.overall);
    else if (choice === '3') await browseBucket('Community rankings', payload.rankings.by_community);
    else if (choice === '4') await browseBucket('Branch rankings', payload.rankings.by_branch);
    else if (choice === '5') await browseBucket('District rankings', payload.rankings.by_district);
    else if (choice === '6') await searchRanking(payload);
    else if (choice === '7') {
      header('Ranking methodology');
      const weights = payload.metadata.dimension_weights ?? {};
      const methodology = payload.metadata.methodology ?? {};
      for (const [name, weight] of Object.entries(weights)) {
        console.log(`${name} (${Math.round(weight * 100)}%)`);
        console.log(`  ${methodology[name] ?? ''}`);
        console.log('');
      }
      await pause();
    }
  }
}

async function showAllotementQa() {
  const qa = safeReadJson(PATHS.allotementQa) as any;
  if (!qa) {
    header('Allotement QA');
    console.log(`Missing file: ${PATHS.allotementQa}`);
    console.log('');
    await pause();
    return;
  }

  header('Allotement QA Summary');
  console.log(`Training rows        : ${formatInt(qa.training?.row_count)}`);
  console.log(`Unique colleges      : ${formatInt(qa.training?.unique_colleges)}`);
  console.log(`Unique branches      : ${formatInt(qa.training?.unique_branches)}`);
  console.log(`Ranking rows         : ${formatInt(qa.rankings?.row_count)}`);
  console.log(`Missing district rows: ${formatInt(qa.rankings?.missing_district_rows)} (${formatPercent(qa.rankings?.missing_district_pct)})`);
  console.log(`Score bound issues   : ${formatInt(qa.rankings?.score_bounds_violations)}`);
  console.log('');
  console.log('Year counts');
  for (const [year, count] of Object.entries(qa.training?.year_counts ?? {})) {
    console.log(`- ${year}: ${formatInt(Number(count))}`);
  }
  console.log('');
  console.log('Top branch codes');
  for (const [code, count] of qa.training?.top_10_branch_codes ?? []) {
    console.log(`- ${code}: ${formatInt(Number(count))}`);
  }
  console.log('');
  await pause();
}

async function showCollegeInfoQa() {
  const qa = safeReadJson(PATHS.collegeInfoQa) as any;
  if (!qa) {
    header('College Info QA');
    console.log(`Missing file: ${PATHS.collegeInfoQa}`);
    console.log('');
    await pause();
    return;
  }

  header('College Info QA Summary');
  console.log(`Raw colleges       : ${formatInt(qa.raw?.count)}`);
  console.log(`Filtered colleges  : ${formatInt(qa.filtered?.count)}`);
  console.log(`Filtered districts : ${formatInt(qa.filtered?.district_count)}`);
  console.log(`Filtered with courses: ${formatInt(qa.filtered?.colleges_with_courses)} (${formatPercent(qa.filtered?.colleges_with_courses_pct)})`);
  console.log(`Filtered with NBA course: ${formatInt(qa.filtered?.colleges_with_nba_course)} (${formatPercent(qa.filtered?.colleges_with_nba_course_pct)})`);
  console.log('');
  console.log('Filtered autonomy');
  for (const [name, count] of Object.entries(qa.filtered?.autonomy_counts ?? {})) {
    console.log(`- ${name}: ${formatInt(Number(count))}`);
  }
  console.log('');
  console.log('Top filtered districts');
  for (const [district, count] of qa.filtered?.top_15_districts ?? []) {
    console.log(`- ${district}: ${formatInt(Number(count))}`);
  }
  console.log('');
  await pause();
}

async function showGrlQa() {
  const qa = safeReadJson(PATHS.grlQa) as any;
  if (!qa) {
    header('General Rank List QA');
    console.log(`Missing file: ${PATHS.grlQa}`);
    console.log('');
    await pause();
    return;
  }

  header('General Rank List QA Summary');
  console.log(`Rows                    : ${formatInt(qa.row_count)}`);
  console.log(`Blank community rank    : ${formatInt(qa.blank_community_rank_rows)}`);
  console.log(`Blank aggregate mark    : ${formatInt(qa.blank_aggregate_mark_rows)}`);
  console.log('');
  console.log('Year counts');
  for (const [year, count] of Object.entries(qa.year_counts ?? {})) {
    console.log(`- ${year}: ${formatInt(Number(count))}`);
  }
  console.log('');
  console.log('Community counts');
  for (const [community, count] of Object.entries(qa.community_counts ?? {})) {
    console.log(`- ${community}: ${formatInt(Number(count))}`);
  }
  console.log('');
  await pause();
}

async function showGeoQa() {
  const qa = safeReadJson(PATHS.geoQa) as any;
  if (!qa) {
    header('Geo QA');
    console.log(`Missing file: ${PATHS.geoQa}`);
    console.log('');
    await pause();
    return;
  }

  header('Geo QA Summary');
  for (const key of ['legacy_clean_output', 'legacy_unresolved', 'active_clean_output', 'active_unresolved']) {
    const item = qa[key];
    if (!item) continue;
    console.log(`${key}`);
    console.log(`- Exists: ${String(item.exists)}`);
    console.log(`- Count: ${formatInt(item.count)}`);
    console.log(`- With coords: ${formatInt(item.with_coords)} (${formatPercent(item.with_coords_pct)})`);
    const breakdown = Object.entries(item.source_breakdown ?? {});
    if (breakdown.length) {
      console.log(`- Sources:`);
      for (const [name, count] of breakdown) {
        console.log(`  - ${name}: ${formatInt(Number(count))}`);
      }
    }
    console.log('');
  }
  await pause();
}

async function showPipelineManifest() {
  const manifest = safeReadJson(PATHS.pipelineManifest) as any;
  if (!manifest) {
    header('Training pipeline manifest');
    console.log(`Missing file: ${PATHS.pipelineManifest}`);
    console.log('');
    await pause();
    return;
  }

  header('Training Pipeline Manifest');
  console.log(`Batch skipped              : ${String(manifest.batch_skipped)}`);
  console.log(`Batch exit code            : ${manifest.batch_exit_code}`);
  console.log(`Reference cleaned rows     : ${formatInt(manifest.reference_cleaned_rows)}`);
  console.log(`Filtered reference colleges: ${formatInt(manifest.filtered_reference_json_colleges)}`);
  console.log(`Training kept rows         : ${formatInt(manifest.training_kept_rows)}`);
  console.log(`Training removed rows      : ${formatInt(manifest.training_removed_rows)}`);
  console.log('');
  console.log('Training removal counts');
  for (const [name, count] of Object.entries(manifest.training_removal_counts ?? {})) {
    console.log(`- ${name}: ${formatInt(Number(count))}`);
  }
  console.log('');
  console.log('Validation');
  for (const [name, count] of Object.entries(manifest.validation ?? {})) {
    console.log(`- ${name}: ${formatInt(Number(count))}`);
  }
  console.log('');
  await pause();
}

async function showTextFile(title: string, path: string) {
  const text = safeReadText(path);
  header(title, path);
  if (!text) {
    console.log('Missing file.');
    console.log('');
    await pause();
    return;
  }

  const lines = text.split(/\r?\n/);
  const pageSize = 28;
  let offset = 0;

  while (true) {
    header(title, `${path}\nLines ${offset + 1}-${Math.min(offset + pageSize, lines.length)} of ${lines.length}`);
    console.log(lines.slice(offset, offset + pageSize).join('\n'));
    console.log('');
    const canPrev = offset > 0;
    const canNext = offset + pageSize < lines.length;
    console.log(`${canPrev ? '[p] previous  ' : ''}${canNext ? '[n] next  ' : ''}[q] back`);
    const answer = (await rl.question('Selection: ')).trim().toLowerCase();
    if (answer === 'q' || answer === '') return;
    if (answer === 'n' && canNext) offset += pageSize;
    if (answer === 'p' && canPrev) offset = Math.max(0, offset - pageSize);
  }
}

async function docsBrowser() {
  const options = [
    ['Repo README', PATHS.repoReadme],
    ['Allotement README', PATHS.allotementReadme],
    ['HOW_TO_USE', PATHS.howToUse],
    ['03-data-requirements', PATHS.dataRequirements],
  ] as const;
  const names = options.map(([name]) => name);
  const chosen = await chooseFromList('Docs Browser', names, 'Read the major repo docs from inside the TUI.');
  if (!chosen) return;
  const match = options.find(([name]) => name === chosen);
  if (match) await showTextFile(match[0], match[1]);
}

async function quickActions() {
  while (true) {
    header('Quick Actions');
    console.log('1. Refresh ranking JSON (--skip-scrape)');
    console.log('2. Run QA reports');
    console.log('3. Refresh training outputs (--skip-batch)');
    console.log('0. Back');
    console.log('');
    const choice = (await rl.question('Selection: ')).trim();
    if (choice === '0') return;
    if (choice === '1') {
      runCommand(COMMANDS.refreshRanking, ALLOTEMENT_ROOT);
      await pause();
    } else if (choice === '2') {
      runCommand(COMMANDS.runQa, REPO_ROOT);
      await pause();
    } else if (choice === '3') {
      runCommand(COMMANDS.refreshTraining, ALLOTEMENT_ROOT);
      await pause();
    }
  }
}

async function main() {
  while (true) {
    header('Data Extractor TUI', REPO_ROOT);
    console.log('1. Dashboard');
    console.log('2. Ranking explorer');
    console.log('3. Allotement QA');
    console.log('4. College info QA');
    console.log('5. General rank list QA');
    console.log('6. Geo QA');
    console.log('7. Training pipeline manifest');
    console.log('8. Docs browser');
    console.log('9. Quick actions');
    console.log('0. Exit');
    console.log('');

    const choice = (await rl.question('Selection: ')).trim();
    if (choice === '0') break;
    if (choice === '1') await showDashboard();
    else if (choice === '2') await rankingExplorer();
    else if (choice === '3') await showAllotementQa();
    else if (choice === '4') await showCollegeInfoQa();
    else if (choice === '5') await showGrlQa();
    else if (choice === '6') await showGeoQa();
    else if (choice === '7') await showPipelineManifest();
    else if (choice === '8') await docsBrowser();
    else if (choice === '9') await quickActions();
  }

  await rl.close();
}

main().catch(async (error) => {
  console.error(error instanceof Error ? error.message : String(error));
  try {
    await rl.close();
  } catch {}
  process.exit(1);
});
