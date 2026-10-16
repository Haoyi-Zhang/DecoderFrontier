# PAM-3 3b2s printed-constraint audit

## Locked external input

The project anchor paper displays the nine four-bit words

`0000, 0001, 0011, 0100, 0101, 0111, 1100, 1101, 1111`

for its PAM-3 3b2s example and prints the pairwise no-error-growth condition

`d_H(f(i), f(j)) >= d_H(i, j)`

for all three-bit messages `i,j`. An encoding is an injection from the eight messages into eight of the nine words.

The artifact intentionally distinguishes three statements:

1. the source text reports 72 no-error-growth encodings;
2. the exact printed codeword list and inequality above define a finite combinatorial census;
3. the project's stronger total-decoder semantics additionally quantifies over every raw four-bit received word within one bit of a selected codeword.

Statements 2 and 3 are recomputed here. The exact mathematical count for statement 2 is 96, established below without relying on a search implementation. The source's 72 remains an accurately quoted published number; it is inconsistent with these printed conditions. This resolves the count for the explicit model, not the behavior of an unavailable source implementation.

## Exact count by cube cycles

The nine codewords form the Cartesian product of two three-vertex paths under bit-Hamming-distance-one adjacency: the pairs `00,01,11` make a 3-by-3 grid. Its center is `0101`, its four corners have even parity, and its four edge midpoints have odd parity.

For a noncontracting injection, each distance-one pair of selected codewords must have distinct inverse messages at distance one. Thus its selected codeword graph embeds bijectively as a spanning subgraph of the three-dimensional binary cube `Q3`.

- Omitting a corner leaves the center with four neighbors. This cannot embed into the degree-three cube.
- Omitting an edge midpoint leaves a connected bipartite graph whose parity classes have sizes five and three. A bijective edge-preserving embedding into `Q3` would preserve or swap the bipartition, but the cube has four vertices in each class. This is impossible.
- Consequently `0101` is the omitted word. The remaining eight vertices form the cycle

  `0000,0001,0011,0111,1111,1101,1100,0100,0000`.

Its inverse message labels must be a Hamilton cycle of `Q3`. Conversely every Hamilton labeling satisfies all the distance inequalities: code-distance-one pairs are cube edges; code-distance-two pairs have equal cube parity and distinct labels, hence message distance two; code distances at least three already dominate every three-bit message distance.

There are eight choices for the first message and three for its cube neighbor. Fixing the directed first edge to `000 -> 001` leaves exactly four completions:

| Message order around the fixed codeword cycle |
|---|
| `000,001,011,010,110,111,101,100` |
| `000,001,011,111,101,100,110,010` |
| `000,001,101,100,110,111,011,010` |
| `000,001,101,111,011,010,110,100` |

The next message is either `011` or `101`. In each branch the two remaining walks in the table are forced by avoiding a repeated vertex and closing the cycle. Cube isometries carry any directed edge to the fixed one. The exact count is therefore `8 * 3 * 4 = 96`. The codeword cycle has a fixed start and orientation; no rotation or reversal division is appropriate for labeled encoder functions.

There is also a short consistency obstruction to 72: the 48 cube isometries (three-bit permutations and XOR translations) act freely on injective encoders and preserve all printed conditions. A complete set must consequently have size divisible by 48. Our 96 mappings form two orbits of size 48; 72 cannot be the complete labeled count for this model.

`src/anchor_count_proof.py` checks all nine omission cases, the four fixed-edge completions, both isometry orbits, and an unpruned traversal of all `9P8 = 362,880` injections. It imports neither census implementation and compares the complete resulting mapping sets. This additional count-only traversal is reported separately from the locked synthesis-design visit budget.

## Complete pairwise census

`src/anchor_census.py` assigns the messages in numeric order. At each partial assignment it rejects a candidate word immediately when it violates the printed inequality against any assigned message. This explores 3,666 partial nodes and emits all 96 complete mappings.

`src/anchor_census_check.py` assigns messages in the different order `0,7,3,4,1,2,5,6`, traverses candidate words in reverse order, and reconstructs the complete set independently. It explores 1,298 partial nodes and obtains the same 96 mappings. It compares the exact solution sets, not just their counts.

Every accepted mapping omits `0101`.

## Total-decoder consequence

For a mapping `f`, a raw received word `y`, and error bound `a`, the checker builds

`D_y(a) = { z : d_H(x,z) <= a for every x with d_H(f(x),y) <= 1 }`,

intersected with the inverse pin when `y` is an encoded word. The exact total-decoder error is the least `a` for which every `D_y(a)` is nonempty.

For all 96 pairwise-valid mappings:

- `D_0101(1)` is empty;
- `0101` is off the encoder image;
- the four source messages at that row form a deletion-minimal empty intersection of radius-one message balls; and
- all rows are feasible at bound two.

Hence every mapping has exact total-decoder error two. This supplies an externally defined census of the semantic gap. Circuit costs for those 96 mappings are not evaluated.

## Logical coverage versus executed calls

The full audit grid contains `96 mappings * 16 received rows * 4 error bounds = 6,144` logical mapping/row/bound slots. This number describes the complete finite domain whose outcomes are classified; it is not a count of calls made by the implementation. The independent minimum-bound routine stops after the first infeasible row at a bound, so instrumentation of the current control flow records 4,512 calls to the row-output constructor. `results/anchor-pam3-check.json` retains both counters. They are intentionally not added together or relabeled as proof-tree nodes.

## Mutation and trust boundary

Eight mutations alter the count, delete or duplicate a mapping, change the omitted word, understate the total error, move the obstruction row, delete a core source, or falsely mark the source count as matched. The independent checker rejects all eight.

The handwritten cube argument establishes the count, while the three complete executable paths cross-check its finite objects. Python and the checker implementations remain trusted. Four additional portable unit tests check the exact count and candidate coverage, reject truncation to 72 mappings, and ensure that the source quotation itself stays 72.
