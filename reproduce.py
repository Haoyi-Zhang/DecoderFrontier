"""One-worker, bounded generation and independent replay, using only Python stdlib.
Run from the artifact root. Every child has a 600-second deadline. A failed or
missing child leaves the campaign incomplete, never a successful frontier report.
"""
from __future__ import annotations
import csv
import argparse
import json
import os
import resource
import subprocess
import sys
import time
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parent
CHILD_ADDRESS_SPACE_BYTES=3*1024**3
CHILD_TIMEOUT_SECONDS=600

def set_child_limits():
    """Apply the documented per-child address-space bound before exec."""
    resource.setrlimit(resource.RLIMIT_AS,(CHILD_ADDRESS_SPACE_BYTES,CHILD_ADDRESS_SPACE_BYTES))


def write_json(path, value):
    """Replace a JSON record only after the complete new record is written."""
    with tempfile.NamedTemporaryFile(mode='w', dir=path.parent, delete=False) as f:
        temporary=Path(f.name)
        json.dump(value,f,indent=2); f.write('\n')
    temporary.replace(path)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--resume',action='store_true',help='Resume completed stages of this same unchanged scientific source and input set.')
    parser.add_argument('--max-stages',type=int,help='Run at most this many unfinished stages, then pause without a completion claim.')
    args=parser.parse_args()
    stage_limit=args.max_stages
    if stage_limit is not None and stage_limit<1:
        parser.error('--max-stages must be positive')
    os.chdir(ROOT)
    env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
    cases=json.loads(Path('inputs/cases.json').read_text())
    fixed_cases=json.loads(Path('inputs/fixed-codebooks.json').read_text())
    anchor_spec=json.loads(Path('inputs/anchor-pam3.json').read_text())
    selection=json.loads(Path('inputs/selection.json').read_text())
    estimate=2*selection['candidate_count_per_pass']
    if estimate+selection['pilot_candidate_count']>300000:
        raise RuntimeError('Aggregate planned candidate cap exceeded')
    results=Path('results');results.mkdir(exist_ok=True)
    # An old successful report must never survive as a current success after a
    # new invocation fails. Resume assumes unchanged scientific source files.
    write_json(results/'campaign.json',{
        'complete_locked_case_replay':False,
        'status':'running; no current completion claim',
        'resume':args.resume})
    before=resource.getrusage(resource.RUSAGE_CHILDREN)
    wall=time.perf_counter()
    logs=json.loads((results/'commands.json').read_text()) if args.resume and (results/'commands.json').exists() else []
    completed={r['stage'] for r in logs if r['returncode']==0}
    if args.resume:
        for s in cases:
            if 'generate-'+s['id'] in completed:
                if json.loads((results/(s['id']+'.json')).read_text())['case']!=s:
                    raise RuntimeError('Inputs changed; start a fresh reproduction')
            if 'check-'+s['id'] in completed:
                if not json.loads((results/(s['id']+'-check.json')).read_text())['accepted']:
                    raise RuntimeError('A completed check is not accepted')
        for s in fixed_cases:
            if 'fixed-generate-'+s['id'] in completed:
                certificate=json.loads((results/'fixed-codebook'/(s['id']+'.json')).read_text())
                if certificate['case']['id']!=s['id'] or certificate['case']['encoder']!=s['encoder']:
                    raise RuntimeError('Fixed-codebook inputs changed; start a fresh reproduction')
            if 'fixed-check-'+s['id'] in completed:
                if not json.loads((results/'fixed-codebook'/(s['id']+'-check.json')).read_text())['accepted']:
                    raise RuntimeError('A completed fixed-codebook check is not accepted')
    stages=[]
    for s in cases:
        stages.extend([('generate-'+s['id'],['src/synthesis.py','--case',s['id']]),
                       ('check-'+s['id'],['src/checker.py','--case',s['id']])])
    stages.extend([('semantic-projection',['src/semantic_projection.py']),
                   ('projection-check',['src/projection_check.py']),
                   ('projection-controls',['tests/projection_controls.py'])])
    for spec in cases:
        stages.extend([('proof-generate-'+spec['id'],['src/frontier_proofs.py','--case',spec['id']]),
                       ('proof-check-'+spec['id'],['src/frontier_proof_check.py','--case',spec['id']])])
    stages.extend([('proof-controls',['tests/frontier_proof_controls.py']),
                   ('proof-summary',['src/proof_summary.py'])])
    for spec in fixed_cases:
        stages.extend([('fixed-generate-'+spec['id'],['src/fixed_codebook_proof.py','--case',spec['id']]),
                       ('fixed-check-'+spec['id'],['src/fixed_codebook_check.py','--case',spec['id']])])
    stages.append(('fixed-controls',['tests/fixed_codebook_controls.py']))
    stages.extend([('anchor-census',['src/anchor_census.py']),
                   ('anchor-census-check',['src/anchor_census_check.py']),
                   ('anchor-census-controls',['tests/anchor_census_controls.py']),
                   ('encoding-properties',['tests/encoding_properties.py']),
                   ('theory',['src/theory_checks.py']),('controls',['tests/controls.py']),('scalarization',['src/baseline.py']),('metadata-integrity',['tests/metadata_integrity.py']),('orchestration-controls',['tests/orchestration.py'])])
    def resumable_producer_stage(name):
        # Resume may reuse only immutable, claim-producing stages whose outputs
        # are checked again below. Checkers, controls, summaries, and metadata
        # audits always rerun so source changes cannot inherit stale success.
        return (
            name.startswith('generate-')
            or name.startswith('proof-generate-')
            or name.startswith('fixed-generate-')
            or name in {'semantic-projection', 'anchor-census'}
        )

    executed=0
    for name,command_args in stages:
        if args.resume and name in completed and resumable_producer_stage(name):
            continue
        if stage_limit is not None and executed>=stage_limit:
            usage=resource.getrusage(resource.RUSAGE_CHILDREN)
            write_json(results/'campaign.json',{'complete_locked_case_replay':False,
                'status':'paused at durable stage boundary','completed_stages':len(completed)+executed,
                'child_cpu_seconds_this_invocation':usage.ru_utime+usage.ru_stime-before.ru_utime-before.ru_stime})
            print('Paused; resume unchanged scientific sources to finish.',flush=True)
            return
        t=time.perf_counter()
        child_before=resource.getrusage(resource.RUSAGE_CHILDREN)
        try:
            r=subprocess.run([sys.executable,*command_args],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                             text=True,timeout=CHILD_TIMEOUT_SECONDS,preexec_fn=set_child_limits)
        except subprocess.TimeoutExpired:
            write_json(results/'campaign.json',{'complete_locked_case_replay':False,
                'status':'timeout','failed_stage':name,'maximum_child_deadline_s':CHILD_TIMEOUT_SECONDS})
            raise
        child_after=resource.getrusage(resource.RUSAGE_CHILDREN)
        record={'stage':name,'child_cpu_seconds':child_after.ru_utime+child_after.ru_stime-child_before.ru_utime-child_before.ru_stime,'command':['python',*command_args],'returncode':r.returncode,
                'wall_seconds':time.perf_counter()-t,'child_peak_rss_kib_this_invocation':child_after.ru_maxrss,'stdout':r.stdout,'stderr':r.stderr}
        logs.append(record)
        write_json(results/'commands.json',logs)
        print(name,r.returncode,round(record['wall_seconds'],3),flush=True)
        if r.returncode:
            write_json(results/'campaign.json',{'complete_locked_case_replay':False,
                'status':'failed','failed_stage':name,'returncode':r.returncode})
            raise RuntimeError(f'{name} failed: {r.stderr}')
        executed+=1
        usage=resource.getrusage(resource.RUSAGE_CHILDREN)
        cpu=(usage.ru_utime+usage.ru_stime)-(before.ru_utime+before.ru_stime)
        if cpu>6*3600:raise RuntimeError('Reserved repair/reproduction CPU budget reached')
    summaries=[json.loads((results/(s['id']+'.json')).read_text()) for s in cases]
    checks=[json.loads((results/(s['id']+'-check.json')).read_text()) for s in cases]
    with (results/'summary.csv').open('w',newline='') as f:
        writer=csv.writer(f);writer.writerow(['case','q','n','payload_bits','designs','frontier','pair_only_frontier','generation_cpu_s','check_cpu_s','max_peak_rss_kib'])
        for r,c in zip(summaries,checks):
            s=r['case'];fr=';'.join(f"({p['error']},{p['gates']})" for p in r['frontier'])
            pr=';'.join(f"({p['pair_error_bound']},{p['gates']})" for p in r['pair_only_frontier'])
            writer.writerow([s['id'],s['q'],s['n'],s['k'],r['candidate_designs'],fr,pr,r['cpu_seconds'],c['cpu_seconds'],max(r['peak_rss_kib'],c['peak_rss_kib'])])
    controls=json.loads((results/'controls.json').read_text())
    if len(controls)!=8 or not all(r['passed'] for r in controls):
        raise RuntimeError('A required control is missing or failed')
    theory=json.loads((results/'theory.json').read_text())
    if not theory.get('ternary_cross_noncontractive'):
        raise RuntimeError('Explicit obstruction checks are missing')
    scalar=json.loads((results/'scalarization.json').read_text())
    if len(scalar['cases'])!=len(cases):
        raise RuntimeError('Scalarization audit is incomplete')
    projection=json.loads((results/'semantic-projection-check.json').read_text())
    if not projection.get('accepted') or len(projection['cases']) != len(cases):
        raise RuntimeError('Semantic projection check incomplete')
    projection_controls=json.loads((results/'projection-controls.json').read_text())
    if len(projection_controls)!=6 or not all(r['passed'] for r in projection_controls):
        raise RuntimeError('Semantic control missing or failed')
    proof_summary=json.loads((results/'proof-frontiers'/'summary.json').read_text())
    if not proof_summary.get('accepted') or proof_summary.get('cases')!=len(cases):
        raise RuntimeError('Proof-carrying frontier replay incomplete')
    proof_controls=json.loads((results/'proof-frontiers'/'controls.json').read_text())
    if proof_controls.get('passed')!=8:
        raise RuntimeError('Proof-certificate controls incomplete')
    fixed_results=[json.loads((results/'fixed-codebook'/(s['id']+'.json')).read_text()) for s in fixed_cases]
    fixed_checks=[json.loads((results/'fixed-codebook'/(s['id']+'-check.json')).read_text()) for s in fixed_cases]
    if not all(item.get('accepted') for item in fixed_checks):
        raise RuntimeError('Fixed-codebook replay incomplete')
    fixed_controls=json.loads((results/'fixed-codebook'/'controls.json').read_text())
    if fixed_controls.get('passed')!=8:
        raise RuntimeError('Fixed-codebook controls incomplete')
    anchor=json.loads((results/'anchor-pam3.json').read_text())
    anchor_check=json.loads((results/'anchor-pam3-check.json').read_text())
    anchor_controls=json.loads((results/'anchor-pam3-controls.json').read_text())
    encoding_properties=json.loads((results/'encoding-properties.json').read_text())
    if not anchor_check.get('accepted') or anchor_check.get('pairwise_valid_mappings_checked')!=anchor.get('pairwise_valid_mappings'):
        raise RuntimeError('Anchor printed-constraint census replay incomplete')
    if len(anchor_controls)!=8 or not all(item.get('passed') for item in anchor_controls):
        raise RuntimeError('Anchor census mutation controls incomplete')
    if not encoding_properties.get('accepted'):
        raise RuntimeError('Small-oracle encoding property checks incomplete')
    metadata=json.loads((results/'metadata-integrity.json').read_text())
    if not metadata.get('accepted') or metadata.get('scholarly_references_checked',0)<55:
        raise RuntimeError('Metadata and literature integrity audit incomplete')
    semantic_rows_checked=sum(item['received_rows_checked'] for item in projection['cases'])
    retained_proof_obligations=(proof_summary['proof_checker_node_visits'] + semantic_rows_checked
        + sum(item['cubes_checked']+item['packing_pairs_checked']+item['planes_checked'] for item in fixed_checks)
        + proof_summary['encoder_plane_certificates']+proof_summary['decoder_relation_certificates']
        + anchor_check['raw_received_rows_checked']
        + encoding_properties['cardinality']['assignments']
        + encoding_properties['relational']['bounds']
        + encoding_properties['relational']['correlated_forbidden_tuple_checks'])
    if retained_proof_obligations>150000:
        raise RuntimeError('Retained proof-obligation ceiling exceeded')
    after=resource.getrusage(resource.RUSAGE_CHILDREN)
    report={'complete_locked_case_replay':all(c['accepted'] for c in checks),'cases':len(cases),
            'generation_designs':sum(r['candidate_designs'] for r in summaries),
            'checker_design_visits':sum(c['candidate_designs_replayed'] for c in checks),
            'plane_cost_certificates_checked':sum(c['plane_minimality_certificates'] for c in checks),
            'frontier_points':sum(len(r['frontier']) for r in summaries),
            'semantic_projection_accepted':projection['accepted'],
            'encoder_bound_profiles_checked':projection['profiles_checked'],
            'encoders_checked_in_projection':projection['encoders_checked'],
            'semantic_controls_passed':len(projection_controls),
            'proof_frontier_cases':proof_summary['cases'],
            'proof_encoder_coverage':proof_summary['encoders_covered'],
            'proof_plane_certificates':proof_summary['encoder_plane_certificates']+proof_summary['decoder_relation_certificates'],
            'proof_dpll_search_nodes':proof_summary['dpll_search_nodes'],
            'proof_checker_node_visits':proof_summary['proof_checker_node_visits'],
            'proof_certificate_bytes':proof_summary['certificate_bytes'],
            'proof_mutation_controls_passed':proof_summary['mutation_controls_passed'],
            'semantic_received_rows_checked':semantic_rows_checked,
            'retained_proof_obligations_checked':retained_proof_obligations,
            'fixed_codebook_cases':len(fixed_cases),
            'fixed_codebook_frontier_points':sum(len(item['frontier']) for item in fixed_results),
            'fixed_codebook_decoder_completion_exponents':[item['decoder_completion_count_power_of_two'] for item in fixed_results],
            'fixed_codebook_planes_checked':sum(item['planes_checked'] for item in fixed_checks),
            'fixed_codebook_cubes_checked':sum(item['cubes_checked'] for item in fixed_checks),
            'fixed_codebook_packing_pairs_checked':sum(item['packing_pairs_checked'] for item in fixed_checks),
            'fixed_codebook_mutation_controls_passed':fixed_controls['passed'],
            'anchor_pairwise_valid_mappings':anchor['pairwise_valid_mappings'],
            'anchor_independent_pairwise_mappings_checked':anchor_check['pairwise_valid_mappings_checked'],
            'anchor_total_decoder_error_two_mappings':anchor_check['exact_total_error_two_mappings'],
            'anchor_source_reported_pairwise_count':anchor_check['source_reported_count'],
            'anchor_printed_rule_count':anchor_check['printed_rule_count'],
            'anchor_count_discrepancy_resolved':False,
            'anchor_mutation_controls_passed':len(anchor_controls),
            'encoding_property_assignments_checked':encoding_properties['cardinality']['assignments'],
            'encoding_relation_bounds_checked':encoding_properties['relational']['bounds'],
            'metadata_integrity_accepted':metadata['accepted'],
            'scholarly_references_checked':metadata['scholarly_references_checked'],
            'unique_dois_checked':metadata['unique_dois_checked'],
            'external_resources_checked':metadata['external_resources_checked'],
            'claim_records_checked':metadata['claim_records_checked'],
            'primitive_error_pair_evaluations_in_generation':sum(r['explicit_error_pair_evaluations'] for r in summaries),
            'worker_processes_at_a_time':1,'maximum_child_deadline_s':CHILD_TIMEOUT_SECONDS,
            'child_address_space_limit_bytes':CHILD_ADDRESS_SPACE_BYTES,
            'child_cpu_seconds_this_invocation':after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime,
            'measured_generation_and_checker_cpu_seconds':sum(r['cpu_seconds'] for r in summaries)+sum(c['cpu_seconds'] for c in checks),
            'recorded_completed_stage_wall_seconds':sum(r['wall_seconds'] for r in logs if r['returncode']==0),
            'cpu_accounting_note':'Per-case generation/checker CPU excludes interpreter startup. child_cpu_seconds_this_invocation and wall_seconds cover this invocation; recorded_completed_stage_wall_seconds sums all retained successful stage records. A resumed invocation retains prior successful stage records.',
            'resumed_stages':len(completed),'completed_stages':len(stages),
            'parent_cpu_seconds':time.process_time(),'wall_seconds':time.perf_counter()-wall,
            'peak_child_rss_kib':max(r.get('child_peak_rss_kib_this_invocation',0) for r in logs),
            'pilot_candidate_visits':selection['pilot_candidate_count'],
            'design_visits_for_this_reproduction_plus_original_pilot':estimate+selection['pilot_candidate_count']+anchor['pairwise_valid_mappings'],
            'proof_format':'Semantic row cores; deterministic relational-SOP CNF with independently replayed unit-conflict DPLL trees for the locked joint cases; forced-cell packing proofs for the fixed-codebook scaling case; and an independently replayed external printed-constraint census.',
            'research_gate':'Implemented and independently replayed code-specific proof-carrying finite frontier enumeration for the frozen grammar, a 2^72-completion fixed-codebook case, and a complete external PAM-3 printed-constraint census. The source-count discrepancy is disclosed rather than resolved; no generic MO-MaxSAT, physical-design, or asymptotic claim.'}
    write_json(results/'campaign.json',report)
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
