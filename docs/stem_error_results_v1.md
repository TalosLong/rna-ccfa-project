# Legacy121 v1 Stem-Error Result Semantics

The authoritative protocol is `docs/error_taxonomy_v1.md`. This document only
describes the generated result representation; it does not modify the frozen
taxonomy, candidate threshold, or matching procedure.

## `stem_error_events.jsonl`

Each line represents one normalized prediction record. `isolated_matches`
contains eligible one-to-one relations and their single primary state.
`ambiguous_components` contains the complete GT and predicted stem lists plus
candidate edges, but no pairwise primary assignment. `missing_gt_stems` and
`unmatched_predicted_stems` contain only zero-candidate residual stems.

## `stem_errors.csv`

Each isolated one-to-one relation is one row with both `gt_outer_pair` and
`pred_outer_pair`. Each missing or unmatched stem is one row with only its own
side populated.

An ambiguous component is represented without fabricating a one-to-one match:

- every involved GT stem receives one `complex_mismatch` row with only GT
  fields populated;
- every involved predicted stem receives one `complex_mismatch` row with only
  predicted fields populated;
- all such rows share `ambiguous_component_id` within their normalized record.

Consequently, ambiguous `complex_mismatch` rows are stem-side residual rows,
not pairwise relationships. `isolated_complex_mismatch_count` in the model
summary counts only eligible isolated one-to-one relations; ambiguous component
and stem counts are reported in separate columns.
