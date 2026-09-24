# Proof-Carrying Total-Decoder Frontiers

This standalone repository reproduces the finite results in **Proof-Carrying Total-Decoder Frontiers for Constrained-Code Synthesis**. It certifies complete error-versus-counted-site frontiers for the exact locked grammar and inputs. It does not claim completeness for all parameter combinations under the broader dimensional caps, a generic MaxSAT proof system, or physical-design performance.

## Headline results

The joint campaign covers 16 binary/ternary specifications and every one of their 174 injective encoders. It produces:

- 234 independently checked semantic obstruction profiles;
- 210 feasible decoder relations;
- 384 exact encoder/decoder plane minima;
- 88,664 independently replayed unit-conflict DPLL nodes;
- 18 certified joint-case Pareto points;
- agreement with an independent exhaustive replay of 48,456 encoder/decoder function pairs and 45,502 truth-table plane minima; and
- a fixed five-bit codebook, X01, with exact frontier `{(1,20),(2,18)}` without enumerating its `2^72` decoder completions;
- a complete audit of the PAM-3 3b2s codeword list and pairwise inequality printed in the anchor paper: two independent searches find 96 pairwise-valid mappings, and all 96 have exact total-decoder error two under radius-one raw-bit errors; and
- exhaustive small-oracle checks for the sequential counter and relational CNF interfaces.

## Quick reproduction

Run from this directory:

```bash
python reproduce.py
```

The driver uses one child process at a time. Each child has a 600-second deadline and a 3 GiB address-space limit. A failed or timed-out stage marks `results/campaign.json` incomplete before stopping. Only all 81 successful stages set `complete_locked_case_replay` to `true`. The final stage checks the bibliography, source ledger, claim ledger, required files, and absence of fabricated repository placeholders.

A bounded, resumable run is also supported:

```bash
python reproduce.py --max-stages 8
python reproduce.py --resume --max-stages 8
```

Resume may reuse only completed high-cost producer stages, and only when their locked inputs still match. Checkers, controls, summaries, scalarization, metadata audit, and orchestration controls rerun. Repeat until `results/campaign.json` reports 81 completed stages. A paused result is not a completion claim.

No package installation, network access, GPU, external solver, or non-standard Python module is required.

## Repository map

- `inputs/cases.json` - sixteen locked joint-synthesis specifications.
- `inputs/fixed-codebooks.json` - fixed-codebook scaling case X01.
- `inputs/selection.json` - frozen selection and candidate-count account.
- `inputs/anchor-pam3.json` - externally sourced PAM-3 printed-constraint audit input.
- `src/semantic_projection.py` - legal decoder-output relations and semantic cores.
- `src/projection_check.py` - independent semantic reconstruction and count checks.
- `src/frontier_proofs.py` - relational-SOP CNFs, attaining circuits, and DPLL lower-bound trees.
- `src/frontier_proof_check.py` - independent certificate reconstruction and replay.
- `src/fixed_codebook_proof.py` - X01 circuits and forced-cell packing certificates.
- `src/fixed_codebook_check.py` - independent X01 checker.
- `src/synthesis.py` - exhaustive encoder/decoder function-table oracle.
- `src/checker.py` - separately implemented exact truth-table cost and frontier replay.
- `src/baseline.py` - positive weighted-sum audit.
- `src/anchor_census.py` and `src/anchor_census_check.py` - independent complete censuses of the anchor paper's displayed PAM-3 codeword list and pairwise inequality.
- `tests/` - original, semantic, proof, fixed-codebook, anchor-census, encoding-property, orchestration, and metadata-integrity controls.
- `proofs/` - handwritten derivations and certificate-format arguments.
- `results/` - generated certificates, independent checker records, controls, and summaries.
- `claim_evidence_ledger.csv` - mapping from paper claims to exact evidence.
- `literature-audit.csv` - 60-reference source and reading-depth audit.
- `external_resources.csv` - external-source, asset, and tool provenance.
- `tests/metadata_integrity.py` - structural audit of all 60 references, 60 unique DOIs, provenance rows, claim records, required files, and repository-link hygiene.

## Certificate boundary

For a fixed encoder and error bound, every received word has a finite set of legal decoded messages. An empty set yields either an inverse-pin conflict or an empty Hamming-ball intersection core. A nonempty row relation is compiled into a deterministic CNF for a bounded shared-product SOP plane.

Each exact plane certificate contains:

1. an explicit circuit attaining the claimed product count; and
2. a complete split tree proving the CNF with one fewer product unsatisfiable, with every leaf closed by unit propagation.

`src/frontier_proof_check.py` deliberately imports neither the producer, the exhaustive synthesizer, nor the original cost checker. It reconstructs the raw domain, cube order, legal row relation, variables, clauses, sequential counters, circuit behavior, branches, objective profile, and encoder coverage. It rejects malformed masks, altered rows, missing branches, invalid variables, cycles, unreachable records, non-conflicting leaves, and omitted encoders.

This is executable finite checking, not a mechanically verified checker or standardized DRAT/LRAT/VeriPB proof. The Python runtime, checker source, and handwritten soundness/equivalence arguments remain trusted.

## Independent exhaustive oracle

`src/synthesis.py` enumerates every injective encoder and every total inverse decoder for the sixteen small cases. It computes exact shared-product minima. `src/checker.py` reconstructs cubes differently, checks explicit circuits, rules out smaller covers, repeats all function pairs, recomputes histograms and frontiers, and verifies connection-cap closure. These passes are independent code paths, but not independent human review.

The diagnostic pair-only frontier in producer results is not part of the complete independent frontier claim. The manuscript's pairwise-versus-total conclusion instead rests on direct proofs and explicit finite witnesses.


## External anchor audit and selection-bias boundary

The PAM-3 A01 audit is not a case designed around the delivered solver: its nine codewords and pairwise no-error-growth inequality come directly from the project anchor paper. The producer and checker enumerate every mapping satisfying that printed rule, using different message and codeword orders. Both obtain 96 mappings; all omit `0101`, all have a four-source off-image obstruction at `0101`, and all require total-decoder error two. The source text reports 72. Because no additional published condition was found that reconciles the counts, the artifact records the discrepancy and calls A01 a **printed-constraint audit**, not a numerical reproduction or a correction of the source.

There is no learned model and therefore no statistical train/test overfitting claim. The analogous threat is post-hoc instance selection. T02 and X01 are explicitly disclosed as development cases; the sixteen joint cases remain synthetic and locked; A01 is a complete externally defined census. The artifact does not infer population-level prevalence or practical speed from any of them.

## Fixed-codebook X01

X01 has a five-bit binary channel and a three-bit payload. The encoder is fixed, so the remaining total-decoder space has `8^(32-8)=2^72` completions. The certificate derives exact legal relations, constructs decoder circuits with five and three products at error bounds one and two, and proves matching lower bounds with incompatible forced-one cells. The independent checker rebuilds all valid cubes and verifies every claimed packing pair.

## Controls

The full run includes:

- 8 original controls: two capacity-infeasible cases and six witness/cost/frontier mutations;
- 6 semantic-projection controls, including a correlated-output counterexample;
- 8 branch-certificate mutations;
- 8 fixed-codebook certificate mutations;
- 8 anchor-census mutations;
- exhaustive small-oracle encoding tests; and
- 2 mocked orchestration failures proving that stale success cannot survive a failed or timed-out invocation; and
- 1 direct assertion that the documented 3 GiB child address-space bound is applied before `exec`.

These controls test interfaces and failure modes; they are not additional practical workloads.

## Expected completed summary

A successful `results/campaign.json` reports, among other fields:

- `completed_stages`: 81
- `child_address_space_limit_bytes`: 3221225472
- `generation_designs`: 48456
- `checker_design_visits`: 48456
- `plane_cost_certificates_checked`: 45502
- `proof_encoder_coverage`: 174
- `proof_plane_certificates`: 384
- `proof_checker_node_visits`: 88664
- `semantic_received_rows_checked`: 3488
- `retained_proof_obligations_checked`: generated by the current run (below 150,000)
- `fixed_codebook_decoder_completion_exponents`: `[72]`
- `frontier_points`: 18
- `metadata_integrity_accepted`: `true`
- `scholarly_references_checked`: 60
- `unique_dois_checked`: 60
- `external_resources_checked`: 67
- `claim_records_checked`: 21
- `anchor_pairwise_valid_mappings`: 96
- `anchor_total_decoder_error_two_mappings`: 96
- `encoding_property_assignments_checked`: 382

Timing fields are observations from the current environment, not performance claims. The retained proof-obligation count and the 837,040 primitive error comparisons are intentionally reported separately.

## Regenerating paper tables

From the paper directory in the complete project:

```bash
python ../artifact/src/export_tables.py --results ../artifact/results --output-dir .
```

This exports LaTeX table rows, macros, and PGFPlots coordinate files from the completed result records. It does not rerun the scientific campaign.

## License and external material

Authored artifact code and inputs are covered by `LICENSE`. Scholarly sources are cited but not redistributed. The artifact contains no public-repository placeholder, credentials, private data, or external binary solver. See `external_resources.csv` and `literature-audit.csv` for provenance and reading-depth details.
