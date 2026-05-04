#!/usr/bin/env python3
from pathlib import Path
import csv, json, hashlib, re, datetime, shutil

project_dir = Path(__file__).resolve().parents[1]
target = (project_dir / '..' / '34ae3677f1c681f2ab27e86c496ca7d9').resolve()
bundle = project_dir / 'audit_bundle'
logs = project_dir / 'logs'

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def read_json(path: Path):
    return json.loads(path.read_text())

def read_csv(path: Path):
    with path.open(newline='') as f:
        return list(csv.DictReader(f))

def f(row, key):
    return float(row[key])

def b(row, key):
    return str(row[key]).strip().lower() in {'true','1','yes'}

# Canonical target artifacts from its decision file.
decision = read_json(target / '.omx/project_decision.json')
router_rows = read_csv(target / 'results/router_integrated_parent_keep_bt32/metrics.csv')
decoder_rows = read_csv(target / 'results/decoder_layer_prefill_parent_keep/metrics.csv')
tiny_rows = read_csv(target / 'results/smoke_router_integrated/metrics.csv')
live_rows = read_csv(bundle / 'live_smoke_router_integrated/metrics.csv')

router_min_module = min(f(r, 'module_speedup_vs_dense_forward') for r in router_rows)
router_min_builder = min(f(r, 'builder_speedup_vs_torch') for r in router_rows)
decoder_min_layer = min(f(r, 'layer_speedup') for r in decoder_rows)
decoder_min_mlp = min(f(r, 'mlp_speedup') for r in decoder_rows)
router_correct = all(b(r, 'builder_correct') and b(r, 'mlp_correct') and b(r, 'counted_mlp_correct') and b(r, 'module_boundary_correct') and not b(r, 'branch_killed') for r in router_rows)
decoder_correct = all(b(r, 'correct') and not b(r, 'branch_killed') for r in decoder_rows)
tiny_calibrates_overhead = all(b(r, 'branch_killed') for r in tiny_rows) and max(f(r, 'module_speedup_vs_dense_forward') for r in tiny_rows) < 1.0
live_correct = all(b(r, 'builder_correct') and b(r, 'mlp_correct') and b(r, 'counted_mlp_correct') and b(r, 'module_boundary_correct') for r in live_rows)
live_small_shape_killed = all(b(r, 'branch_killed') for r in live_rows)
live_builder_speed = min(f(r, 'builder_speedup_vs_torch') for r in live_rows)

env_log = (logs / 'audit_environment.log').read_text(errors='replace')
live_log = (logs / 'live_smoke_router_integrated.log').read_text(errors='replace')
mem_match = re.search(r'MemAvailable:\s+(\d+) kB', env_log)
rss_match = re.search(r'Maximum resident set size \(kbytes\):\s+(\d+)', live_log)

criteria = [
    {
        'id': 'C1_positive_featured_candidate',
        'pass': decision.get('decision') == 'positive_result' and decision.get('disposition') == 'viable_for_next_stage' and decision.get('needs_review') is False,
        'evidence': {'decision': decision.get('decision'), 'disposition': decision.get('disposition'), 'needs_review': decision.get('needs_review'), 'confidence': decision.get('confidence')},
    },
    {
        'id': 'C2_required_artifact_set_present',
        'pass': all((target / p).exists() for p in decision['evidence_artifacts']) and (target / 'run_notes.md').stat().st_size > 1000,
        'evidence': {'required_count': len(decision['evidence_artifacts']), 'missing': [p for p in decision['evidence_artifacts'] if not (target / p).exists()], 'run_notes_bytes': (target / 'run_notes.md').stat().st_size},
    },
    {
        'id': 'C3_existing_main_metrics_support_claim',
        'pass': router_correct and router_min_module >= 1.15 and router_min_builder >= 3.0 and decoder_correct and decoder_min_layer >= 1.20,
        'evidence': {'router_min_module_speedup': router_min_module, 'router_min_builder_speedup': router_min_builder, 'decoder_min_layer_speedup': decoder_min_layer, 'decoder_min_mlp_speedup': decoder_min_mlp, 'router_correct_all': router_correct, 'decoder_correct_all': decoder_correct},
    },
    {
        'id': 'C4_small_shape_calibration_is_negative_not_overclaimed',
        'pass': tiny_calibrates_overhead,
        'evidence': {'tiny_rows': len(tiny_rows), 'tiny_max_module_speedup': max(f(r, 'module_speedup_vs_dense_forward') for r in tiny_rows), 'all_tiny_branches_killed': all(b(r, 'branch_killed') for r in tiny_rows)},
    },
    {
        'id': 'C5_fresh_live_smoke_executed',
        'pass': live_correct and live_small_shape_killed and live_builder_speed >= 2.0 and 'Exit status: 0' in live_log,
        'evidence': {'live_rows': len(live_rows), 'live_correct_all': live_correct, 'live_small_shape_killed': live_small_shape_killed, 'live_min_builder_speedup': live_builder_speed, 'exit_status_0': 'Exit status: 0' in live_log},
    },
    {
        'id': 'C6_gb10_memory_posture_recorded',
        'pass': 'NVIDIA GB10' in env_log and 'SwapTotal:             0 kB' in env_log and mem_match and int(mem_match.group(1)) > 100_000_000 and rss_match and int(rss_match.group(1)) < 2_000_000,
        'evidence': {'gb10_seen': 'NVIDIA GB10' in env_log, 'swap_disabled': 'SwapTotal:             0 kB' in env_log, 'mem_available_kb': int(mem_match.group(1)) if mem_match else None, 'live_max_rss_kb': int(rss_match.group(1)) if rss_match else None},
    },
]

strict_pass = all(c['pass'] for c in criteria)

# Copy lightweight canonical docs and metrics into the bundle for one-stop auditability.
(bundle / 'selected_artifact').mkdir(exist_ok=True)
for rel in ['README.md','run_notes.md','.omx/project_decision.json','results/router_integrated_parent_keep_bt32/metrics.csv','results/decoder_layer_prefill_parent_keep/metrics.csv','results/smoke_router_integrated/metrics.csv']:
    src = target / rel
    dst = bundle / 'selected_artifact' / rel.replace('/', '__')
    shutil.copy2(src, dst)

hashes = {}
for rel in decision['evidence_artifacts']:
    p = target / rel
    if p.exists() and p.is_file():
        hashes[rel] = {'sha256': sha256(p), 'bytes': p.stat().st_size}
for rel in ['logs/audit_environment.log','logs/live_smoke_router_integrated.log','audit_bundle/live_smoke_router_integrated/metrics.csv','audit_bundle/live_smoke_router_integrated/aggregate_summary.json']:
    p = project_dir / rel
    if p.exists():
        hashes[rel] = {'sha256': sha256(p), 'bytes': p.stat().st_size}

audit = {
    'audit_id': 'strict-pass-featured-enoch-artifact-audit-bundle',
    'created_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'origin_project_id': '355e3677f1c681ba98eff8e9e863a114',
    'selected_artifact': {
        'project_id': decision['project_id'],
        'project_name': decision['project_name'],
        'path': str(target),
        'selection_rationale': 'Highest-scoring locally inspectable positive Enoch artifact in the corpus scan: executable code, GB10 logs, CSV/JSON metrics, run notes, and a positive non-review decision.',
    },
    'strict_pass': strict_pass,
    'criteria': criteria,
    'metric_summary': {
        'router_min_module_speedup': router_min_module,
        'router_min_builder_speedup': router_min_builder,
        'decoder_min_layer_speedup': decoder_min_layer,
        'decoder_min_mlp_speedup': decoder_min_mlp,
        'live_smoke_min_builder_speedup': live_builder_speed,
    },
    'bundle_files': sorted(str(p.relative_to(project_dir)) for p in bundle.rglob('*') if p.is_file()),
    'evidence_hashes': hashes,
}
(bundle / 'strict_audit.json').write_text(json.dumps(audit, indent=2, sort_keys=True) + '\n')
(bundle / 'manifest.json').write_text(json.dumps({'files': audit['bundle_files'], 'strict_pass': strict_pass, 'selected_project_id': decision['project_id'], 'created_at': audit['created_at']}, indent=2, sort_keys=True) + '\n')
print(json.dumps({'strict_pass': strict_pass, 'selected': decision['project_name'], 'criteria': [(c['id'], c['pass']) for c in criteria]}, indent=2))
