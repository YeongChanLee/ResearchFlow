# Optional local helper

Python 3.10+, standard library only. No API keys, network requests, research-data
processing, model training, experiments, or production analysis code. These commands
manage planning documents only. The skill remains usable without the helper.

## Initialize and edit a draft

```text
python <skill-dir>/scripts/researchflow.py init <new-project-dir> --title "Project title"
python <skill-dir>/scripts/researchflow.py check <project-dir>
```

The destination must not already exist. Fill the five sections in `research_spec.md`;
keep the exact numbered headings. Save references and decisions in the generated
planning files. Replace `[TODO]` fields before confirming a section. Keep the project
outside a public skill source tree, or in an ignored private workspace.

`check` accepts an honest unfinished draft and reports placeholder warnings.
`check --baseline-ready` is stricter: all stage receipts must be current, baseline-level
issues resolved, changes closed, and remaining execution/acquisition conditions
acknowledged in the final receipt. It is not a scientific-quality assessment.

## Structured state

`project_state.json` is authoritative for stage approval status. Do not duplicate
current approval flags in the scientific text. The top-level fields are fixed; edit
record lists deliberately. Each ID must be unique across sources/resources/issues/changes.

A source record:

```json
{
  "id": "REF-001",
  "citation": "Verified bibliographic citation, or explicitly unverified candidate",
  "locator": "Verified URL, DOI, or supplied-file locator; empty if unverified",
  "access": "abstract_only",
  "verification": "unverified"
}
```

`access`: `metadata_only`, `abstract_only`, `full_text`, `full_text_and_supplement`,
`user_provided`, `unavailable`. `verification`: `verified`, `unverified`, `conflicting`.
These record source identity/access, not whether every methodological claim is correct.
Put claim-level evidence states and precise locations in reference workflow cards.

A resource record (illustrative, not a verified dataset):

```json
{
  "id": "RES-001",
  "label": "Planned measurement resource",
  "required": true,
  "availability": "planned_collection",
  "evidence": "Researcher reports that acquisition is planned; not yet collected",
  "contingency": "Revisit the sampling and evaluation design if acquisition fails"
}
```

Availability vocabulary is in [Stage 3](stage-3-resources.md). `verified_usable` requires
nonempty evidence. A required `unavailable` resource blocks a baseline. Other unverified
required resources create conditions and need a contingency. Resource availability
must remain honest, even when a research plan has been approved.

An issue record:

```json
{
  "id": "ISS-001",
  "description": "Required external access approval is pending",
  "status": "open",
  "gate": "execution"
}
```

`gate`: `baseline`, `execution`, `advisory`. `status`: `open`, `resolved`; resolved issues
need a nonempty `resolution`. Open execution issues become condition IDs. Open baseline
issues block final approval. Advisory items are retained but do not automatically block.

## Record actual scoped confirmation

1. Complete the scope to be shown and any decision/evidence record edits.
2. Run `packet <project-dir> --stage N` to obtain the current scoped content digest.
3. Show the relevant content/decisions and conditions to the researcher. Obtain an
   explicit answer that actually covers this scope. A hash alone is not a useful
   explanation. If the content changes, create a new packet before confirmation.
4. Record the real answer and its provenance in a receipt file **outside the managed
   project** (or otherwise outside hashed planning artifacts). Never manufacture a
   quote or use the template below as a fictional approval.
5. Run `approve` with that receipt. Do not edit the approved scientific text to paste
   its own hash or repeat the receipt; state and `audit.jsonl` store the confirmation.

Receipt structure (placeholders are intentionally invalid):

```json
{
  "stage": 1,
  "decision": "approve",
  "scope_sha256": "[DIGEST_FROM_PACKET]",
  "researcher": "[ACTUAL_RESEARCHER]",
  "confirmed_at": "[ISO_TIMESTAMP_WITH_TIMEZONE]",
  "source": "[IDENTIFIABLE_MESSAGE_OR_DECISION_RECORD]",
  "quote": "[ACTUAL_SCOPED_CONFIRMATION]",
  "conditions": []
}
```

```text
python <skill-dir>/scripts/researchflow.py packet <project-dir> --stage 1
python <skill-dir>/scripts/researchflow.py approve <project-dir> --receipt <receipt.json>
```

Earlier stages must be confirmed before a later stage is confirmed. A receipt binds
content, metadata and relevant dependencies. Later draft sections can be written before
confirmation, but cannot be treated as approved. Stage 2's two discussion checkpoints
belong in the decision log before its combined stage receipt is recorded.

For Stage 5, `conditions` must include every condition ID reported by its packet.
A coherent future-data-collection plan can be approved conditionally. The helper does
not authenticate the person, interpret the quoted text or establish the truth of
availability evidence. Human/host review remains necessary.

## Amendments

```text
python <skill-dir>/scripts/researchflow.py request-change <project-dir> --id CR-001 --stage 3 --trigger "Required data cannot be obtained"
```

This creates a proposal and conservatively marks Stage 3 and later approvals for
reconfirmation; it does not edit research content or accept the change. In the change
file, document evidence, consequences, alternatives, result exposure and the actual
researcher decision. If earlier framing is affected, include that stage too.

After explicit acceptance, update the approved draft changes and related records.
In the corresponding state entry, use `accepted` while implementation is pending and
`implemented` when the approved planning edits are complete. Use `rejected` for a
rejected proposal. These non-proposed states require:

```json
{
  "decision_record": {
    "researcher": "[ACTUAL_RESEARCHER]",
    "confirmed_at": "[ISO_TIMESTAMP_WITH_TIMEZONE]",
    "source": "[ACTUAL_CONFIRMATION_REFERENCE]",
    "quote": "[ACTUAL_CONFIRMATION]"
  }
}
```

The example is a schema illustration, not a ready-to-use approval. Closing a change
request does not reapprove stages. Reconfirm affected stages and Stage 5. Rejected
changes may still require confirming that the previous plan remains feasible.

## Snapshot and inspect

```text
python <skill-dir>/scripts/researchflow.py check <project-dir> --baseline-ready
python <skill-dir>/scripts/researchflow.py snapshot <project-dir> --version 1.0.0
```

Snapshots include the current draft, state, supporting planning records and hashes.
No existing version is overwritten. Baseline versions must increase. The current
state points to the latest saved baseline; the snapshot's own state preserves the
state at capture time, which may still reference the previous baseline. Its
`snapshot_metadata.json` identifies the captured version unambiguously.

Avoid simultaneous manual edits during a helper command. Mutating helper commands
use a local lock against one another, but an external editor can ignore that lock.
`check` detects stale approvals and ordinary snapshot modifications. Hash manifests
are not a cryptographically signed audit log or a security boundary.
