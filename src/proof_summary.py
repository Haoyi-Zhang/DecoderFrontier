"""Aggregate independently checked proof-frontier results into one compact report."""
from __future__ import annotations
import argparse, json, resource, time
from pathlib import Path


def main() -> None:
    p=argparse.ArgumentParser();p.add_argument('--inputs',type=Path,default=Path('inputs/cases.json'));p.add_argument('--results',type=Path,default=Path('results'));p.add_argument('--proof-dir',type=Path,default=Path('results/proof-frontiers'))
    a=p.parse_args();start=time.process_time();specs=json.loads(a.inputs.read_text());certs=[];checks=[]
    for spec in specs:
        cid=spec['id'];cert=json.loads((a.proof_dir/f'{cid}.json').read_text());check=json.loads((a.proof_dir/f'{cid}-check.json').read_text())
        if not check.get('accepted'):raise RuntimeError(f'{cid} proof certificate not accepted')
        certs.append(cert);checks.append(check)
    controls=json.loads((a.proof_dir/'controls.json').read_text())
    if controls.get('passed')!=8 or not all(x.get('passed') for x in controls['controls']):raise RuntimeError('proof controls incomplete')
    summary={
      'accepted':True,'cases':len(specs),'encoders_covered':sum(x['counts']['encoders'] for x in certs),
      'encoder_plane_certificates':sum(x['counts']['encoder_plane_certificates'] for x in certs),
      'decoder_relation_certificates':sum(x['counts']['decoder_relation_certificates'] for x in certs),
      'semantic_infeasible_profiles':sum(x['semantic_rejections'] for x in checks),
      'feasible_encoder_bound_relations':sum(x['relation_references'] for x in checks),
      'dpll_search_nodes':sum(x['counts']['dpll_search_nodes'] for x in certs),
      'stored_proof_tree_records':sum(x['counts']['stored_proof_tree_records'] for x in certs),
      'proof_checker_node_visits':sum(x['proof_node_visits'] for x in checks),
      'proof_checker_conflict_leaf_visits':sum(x['conflict_leaf_visits'] for x in checks),
      'frontier_points':sum(len(x['frontier']) for x in certs),
      'generation_cpu_seconds':sum(x['cpu_seconds'] for x in certs),
      'generation_wall_seconds_sum':sum(x['wall_seconds'] for x in certs),
      'checking_cpu_seconds':sum(x['cpu_seconds'] for x in checks),
      'checking_wall_seconds_sum':sum(x['wall_seconds'] for x in checks),
      'certificate_bytes':sum((a.proof_dir/f"{s['id']}.json").stat().st_size for s in specs),
      'mutation_controls_passed':controls['passed'],
      'per_case':[{'case':c['case']['id'],'encoders':c['counts']['encoders'],'encoder_planes':c['counts']['encoder_plane_certificates'],'decoder_relations':c['counts']['decoder_relation_certificates'],'proof_search_nodes':c['counts']['dpll_search_nodes'],'proof_records':c['counts']['stored_proof_tree_records'],'frontier':[(p['error_bound'],p['gates']) for p in c['frontier']],'generation_cpu_seconds':c['cpu_seconds'],'checking_cpu_seconds':h['cpu_seconds']} for c,h in zip(certs,checks)],
      'scope':'Exact finite grammar and locked cases only. Unit-conflict DPLL trees are independently replayed; they are not DRAT/VeriPB logs or proof-assistant theorems.',
      'aggregation_cpu_seconds':time.process_time()-start,
      'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    (a.proof_dir/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='per_case'},indent=2))
if __name__=='__main__':main()
