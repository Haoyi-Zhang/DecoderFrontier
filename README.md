# Proof-Carrying Total-Decoder Frontiers

This artifact certifies complete error-versus-counted-site frontiers for the
locked constrained-code grammar and inputs. It includes separately implemented
semantic/certificate checkers and exhaustive small-case oracles. Completeness is
for those inputs, not every parameter combination under the dimensional caps,
a generic MaxSAT proof system or physical-design performance.

## Environment and quick checks

Use Python 3.10 or newer. The complete subprocess driver requires Linux/POSIX
`resource` limits and `signal.alarm`; it is not a native Windows driver. Only
the standard library is required: no installation, network, GPU or solver.

From the artifact root, a small portable certificate-domain check is:

```sh
python -B -m unittest discover -s tests -p test_certificate_numbers.py -v
```

The separate pure incidence regression is:

```sh
python -B tests/regression_plane_incidence.py -v
```

It regenerates 384 plane certificates, checks ordered CNFs and all sixteen cases,
and tests tiny relations, refusals and retained mutations without writing results.
On Windows a deny-all `resource` import stub permits pure functions only, not
POSIX orchestration. These checks do not relabel the retained full campaign.

## Complete or resumable reproduction

**Use a fresh disposable copy of the artifact.** Unlike a read-only checker,
`reproduce.py` creates or replaces files under that copy's `results/`, including
command/progress records. Keep the shipped results as the comparison evidence.

From the disposable artifact root on POSIX:

```sh
python -B reproduce.py
```

The driver executes 81 unique stages with one child at a time, a 600-second
deadline per child and a 3-GiB child address-space limit. Only complete success
sets `results/campaign.json:complete_locked_case_replay` to true. Failures and
timeouts retain their command output and mark the campaign incomplete.

Alternatively, start a bounded run and repeat the resume command:

```sh
python -B reproduce.py --max-stages 8
python -B reproduce.py --resume --max-stages 8
```

Each invocation advances the longest valid completed prefix by at most eight
stages. Source/input identity is bound in `results/resume-state.json`; changed
inputs reject resume, and a missing stage output invalidates that stage and its
suffix. Restart without `--resume` only in the disposable copy. The retained
eleven-invocation campaign finished all 81 stages; those invocation counts are
historical observations, not required counts for a new run.

The scientific workflow runs the numeric checks, incidence regression and full
campaign on Ubuntu 24.04 with whole-run limits, and uploads available raw outputs
on success or failure.

## Inputs, results and exports

- `inputs/cases.json`: sixteen locked joint specifications; `selection.json`
  records selection and candidate counts, including development cases.
- `inputs/fixed-codebooks.json`: fixed-codebook X01; `inputs/anchor-pam3.json`:
  the external printed-constraint audit input.
- `src/semantic_projection.py`, `projection_check.py`: legal row relations and
  separately reconstructed semantic cores.
- `src/frontier_proofs.py`, `frontier_proof_check.py`: attaining SOP circuits and
  independently reconstructed/replayed DPLL lower-bound certificates.
- `src/fixed_codebook_proof.py`, `fixed_codebook_check.py`: spec-bound X01
  circuit/packing certificates; `synthesis.py` and `checker.py`: exhaustive
  function-table oracle and separate cost/frontier replay.
- `src/anchor_census.py`, `anchor_census_check.py`: separately ordered complete
  censuses of the published PAM-3 rule.
- `tests/`, `proofs/`: executable controls, derivations and certificate arguments.
- `results/`: raw certificates, checker records, controls and summaries.
  `campaign.json` and `commands.json` record completion;
  `evidence-counts.json` separates logical coverage, proof objects and execution.
- `claim_evidence_ledger.csv`, `literature-audit.csv`,
  `external_resources.csv`: preserved evidence and source/provenance mappings.

Export derived LaTeX tables, macros and PGFPlots coordinates without rerunning
the campaign, using a separate output directory:

```sh
python -B src/export_tables.py --results results --output-dir ../decoder-tables
```

The complete project can use those generated inputs in its paper build; the flat
artifact repository does not require a sibling paper directory.

## Certificate and evidence conditions

Each exact plane certificate contains an attaining circuit and, for a positive
minimum, a complete lower-bound split tree closed by unit propagation. A zero
minimum needs no lower proof. The checker reconstructs domain, cube order,
relations, counters, clauses, objective profile and encoder coverage without
importing the producer or exhaustive synthesizer. The diagnostic pair-only
frontier is outside the complete independent-frontier claim.

The PAM-3 A01 census yields 96 mappings under the displayed rule, whereas the
source reports 72. The unresolved discrepancy is retained as a printed-constraint
audit, not a numerical reproduction or correction of the source. T02/X01 are
disclosed development cases; the locked synthetic cases and complete A01 census
do not establish population prevalence or practical speed.

Python, checker code and handwritten soundness arguments remain trusted.
Separate code paths are not independent human review or mechanical proof;
the format is not DRAT/LRAT/VeriPB. Incidence reuse changes no independent
reconstruction and has no measured-runtime-gain claim.

## License and external material

Authored artifact code and inputs use `LICENSE`. Scholarly sources are cited,
not redistributed. Provenance and recorded reading depth remain in the source
ledgers; no credential, private data or external binary solver is required.
