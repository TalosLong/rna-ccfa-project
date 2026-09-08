# Phase II Exact Structured Decoder Protocol

Status: **`PHASE2_STRUCTURED_DECODER_PROTOCOL_FROZEN`**

Protocol version: **`PHASE2_DECODER_V1.0`**

Date: **2026-09-09 UTC**

Implementation: **`NOT_AUTHORIZED_IN_THIS_TASK`**

## 1. Decoder choice

The primary decoder is **neural scoring plus exact weighted noncrossing dynamic
programming**. At protocol-freeze time the scoring function is an abstract
pairwise-decomposable interface; no neural model exists or is authorized.

This choice is deliberate:

| Option | Noncrossing | Pseudoknots | Exactness/complexity | Differentiability | Auditability and decision |
| --- | --- | --- | --- | --- | --- |
| Weighted interval DP | Exact primary support | No | `O(n^3)` time, `O(n^2)` memory | Score-level training can be separate; decoder need not be differentiated | Deterministic and simplest to audit; **PRIMARY** |
| ILP | Exact with explicit constraints | Can support selected PK constraints | Worst-case exponential; solver/version/tolerances matter | Usually external to gradient path | **OPTIONAL PK EXTENSION**, separately frozen |
| Maximum-weight matching | One-partner support | Crossing allowed by default | Polynomial for unconstrained graph matching | Usually external | Does not by itself enforce RNA noncrossing/min-loop; not primary |
| Differentiable structured optimization | Depends on relaxation | Depends | Added numerical/relaxation complexity | Yes | Unneeded for validity; future research only |
| Unconstrained neural decoder/post-hoc repair | No guarantee | Arbitrary | Fast but outcome depends on repair heuristics | Yes | **PROHIBITED** |

ILP is not needed in the primary track because the frozen score and edit cost
are pairwise decomposable and all mandatory primary constraints admit interval
DP. Pseudoknots remain a separate secondary track rather than weakening the
primary contract.

## 2. Inputs and variables

Inputs are:

- normalized RNA sequence `x` of length `n`, `30 <= n <= 600`;
- valid source structure `S0`;
- complete legal candidate set `C(x)` from the task protocol;
- finite pair scores `s_ij` for `(i,j) in C(x)`; and
- nonnegative `lambda_edit` fixed on MODEL_SELECTION.

No input can depend on ground truth. Define binary variables:

\[
y_{ij}\in\{0,1\}\quad\text{for every }(i,j)\in C(x),
\]

where `y_ij=1` selects the pair. An implicit unpaired indicator is
`u_i = 1 - sum_j y_min(i,j),max(i,j)` and need not be independently optimized.

## 3. Objective and edit cost

The exact objective is:

\[
\max_y\left[
\sum_{(i,j)\in C(x)}s_{ij}y_{ij}
-\lambda_{edit}\left(
\sum_{(i,j)\in S_0}(1-y_{ij})+
\sum_{(i,j)\in C(x)\setminus S_0}y_{ij}
\right)\right].
\]

The constant `-lambda_edit*|S0|` can be omitted. The effective selection weight
is therefore:

\[
w_{ij}=s_{ij}+\lambda_{edit}\;\text{if }(i,j)\in S_0,
\qquad
w_{ij}=s_{ij}-\lambda_{edit}\;\text{otherwise}.
\]

KEEP costs 0, DELETE costs 1, ADD costs 1 and coupled REPLACE costs 2. There
are no separate favorable weights for REPLACE.

E0 hard facts are implemented by restricting the feasible set: every direct
positive pair has `y_ij=1`, and every pair incident to a supported-unpaired
nucleotide has `y_ij=0`. The decoder must validate mutual consistency before
optimization.

## 4. Hard constraints

Every candidate already satisfies bounds, pair alphabet and minimum loop. The
decoder additionally enforces:

1. **one partner**

   \[
   \sum_{j:(\min(i,j),\max(i,j))\in C(x)}y_{\min(i,j),\max(i,j)}\le1
   \quad\forall i;
   \]

2. **noncrossing**

   \[
   y_{ij}+y_{kl}\le1\quad\text{for every }i<k<j<l;
   \]

3. **E0 direct consistency**, as described above.

The candidate contract independently enforces `0<=i<j<n`, `j-i>3`, and ordered
pair alphabet `AU,UA,GC,CG,GU,UG`.

## 5. Exact recurrence

Let `D[i,j]` be the best deterministic state for subsequence `[i,j]`; empty and
singleton intervals have score zero. For `i<j`:

\[
D[i,j]=\max\left(
D[i,j-1],
\max_{k=i}^{j-4}
\left[D[i,k-1]+D[k+1,j-1]+w_{kj}\right]
\right),
\]

where the inner term exists only when `(k,j)` is a legal candidate and all E0
restrictions are satisfied. Mandatory positive E0 pairs are handled by
interval segmentation/feasibility masks so that a recurrence branch cannot
leave them unselected or select a crossing/competing pair.

The recurrence enumerates every valid noncrossing matching and is exact for the
pairwise objective. Implementation must include a brute-force equivalence test
on exhaustively enumerable short synthetic sequences before any biological
run.

## 6. Numerical and tie contract

Before DP, every finite score and `lambda_edit` is rounded to the nearest
multiple of `1e-8`, ties-to-even, and represented as signed 64-bit integers in
units of `1e-8`. Overflow is a hard failure.

Compare complete solutions in this order:

1. maximum quantized objective;
2. minimum `EditCost(S,S0)`;
3. maximum number of retained `S0` pairs;
4. lexicographically smallest ascending complete pair list.

This tie rule applies inside every DP state and makes output independent of
candidate iteration order, thread scheduling and hash-map order.

## 7. Action extraction and component abstention

The decoder returns a full valid proposal `S_hat`. DELETE and ADD atoms are the
two sides of `S0` symmetric difference. Coupled REPLACE extraction and
component/region construction follow Sections 10--11 of the canonical task
protocol.

The risk controller commits or reverts whole components. Reversion is followed
by the same complete validity audit. The decoder does not implement edit-level
risk decisions inside the recurrence, because doing so could substitute edits
and obscure the finite complete-policy contract.

## 8. Complexity and speed contract

For primary length `n<=600`, worst-case complexity is `O(n^3)` time and
`O(n^2)` memory. Candidate weights can be stored densely or sparsely, but sparse
execution must be output-equivalent to the complete legal universe. CPU
reference inference is mandatory for reproducibility; acceleration is optional
only after byte-equivalence testing.

Inference reports wall time, peak resident memory, candidate count and DP cell
count, but speed cannot change the candidate universe.

## 9. Failure behavior

The decoder fails closed to `S0`, records RNA-level ABSTAIN and commits zero
edits when any of the following occurs:

- invalid `x`, `S0` or E0 package;
- missing/nonfinite pair score;
- score quantization overflow;
- resource limit, solver exception or incomplete traceback;
- output validity failure; or
- component reversion validity failure.

No partial structure, greedy repair or alternative decoder is substituted.
Failure rates are reported by source, length, family and dataset provenance.

## 10. Validity and reproducibility audit

Before any performance experiment, the future implementation must pass:

- 100% bounds/alphabet/min-loop/one-partner/noncrossing checks;
- exact E0 satisfaction for valid E0 packages;
- exact equality with exhaustive enumeration on frozen synthetic fixtures;
- equality of objective computed from variables and extracted edits;
- REPLACE cost exactly 2;
- byte-identical output under repeated runs and permuted candidate input order;
- correct fail-closed handling for every enumerated failure class; and
- no ground-truth import in candidate, score-interface or decoder modules.

These are software/protocol audits, not scientific performance results.

## 11. Optional pseudoknot extension

A future secondary track may use a separately versioned ILP with binary pair
variables, one-partner constraints, selected crossing classes and the same edit
cost. It must freeze solver/version, integrality/feasibility tolerances,
deterministic seed, time limit, optimality-gap policy and failure semantics.
No pseudoknot extension is authorized or implied by this primary freeze.
