# Stage 2 — Literature Discovery & Workflow Reconstruction

## Purpose
Use prior work as evidence for design choices, not as an unquestionable template.
Workflow reconstruction is important here, but ResearchFlow remains centered on
scientist-in-the-loop specification development.

## 2A. Discover and select references
1. Convert the confirmed framing into focused search concepts. Include synonyms,
   task/method terms, data or material types, and competing approaches.
2. Search available scholarly sources; log exact queries, source, search date,
   filters, and coverage limitations. Do not claim a systematic review unless its
   search, selection, and synthesis requirements were actually met.
3. Verify bibliographic identities against primary records. Group versions of the
   same work; distinguish preprints, published versions, corrections, and retractions
   when checkable. Prefer a final corrected version while preserving provenance.
4. Explain candidates by relevance, methodological fit, reporting completeness,
   applicability, alternatives, and conflicting evidence. Prestige is not a selector.
5. Present a short candidate matrix. Obtain researcher confirmation of the core
   references before investing in detailed reconstruction. Additional background
   retrieval can continue without silently adding new design-defining references.

## 2B. Reconstruct and compare
Read full text plus relevant supplements and code/documentation when accessible.
Inspect figures/tables when necessary. Never execute downloaded code or fabricate
unavailable details. Record the precise materials and versions actually inspected.

Create a [workflow card](../assets/templates/reference-workflow-card.md) per core paper:
- Question, scope and main claims.
- Inputs: data/materials, population or inquiry units, assumptions, software/resources.
- Directed steps: step ID, input, operation, output, dependencies, source locator.
- Decisions: exclusions, operational definitions, preprocessing, controls, algorithms,
  measurement, proof construction, interpretation, or other domain-relevant choices.
- Evidence chain: which table/figure/argument supports which claim; validation design.
- Limitations, conflicting details, inaccessible material, and uncertainty.

Work backward from a central claim to its evidence, then organize the confirmed
steps forward from inputs to validation. This reconstructs the reported workflow,
not the authors' undocumented historical sequence or intentions.

## 2C. Co-design transfer
Compare core papers. For each candidate element mark **adopt**, **adapt**, **do not
adopt**, or **defer**; explain assumptions, resource differences, and trade-offs.
A new proposal is allowed but must be labeled as new, with a validation plan.
Obtain researcher confirmation of the interpretation and proposed transfer decisions.
Record 2A and 2B/2C confirmations separately in decision_log.md; the helper's single
Stage 2 approval is the combined checkpoint, not a substitute for these discussions.

## Gate
The selected references and how they inform the new design are understood and
confirmed. Missing details that matter remain explicit issues. An abstract-only
paper can support limited claims, not a claimed full-method reconstruction.
