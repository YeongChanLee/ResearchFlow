# Architecture

## One orchestrator, five stages, on-demand references

The portable entry point is `skills/researchflow/SKILL.md`. It controls framing,
scoped scientist interaction, stage transitions, evidence and change policy.
Stage-specific reference files and templates are loaded only when relevant.
Separate autonomous agents are not required; a second reviewer is optional and must
be disclosed as actually available, not simulated or assumed.

The fixed stages are:
1. Research Framing
2. Literature Discovery & Workflow Reconstruction
3. Data & Resource Co-design
4. Methodology & Evaluation Design
5. Specification Review & Baseline Approval

Stages describe the first-pass workflow, not a waterfall. An acquisition failure at
Stage 3 can reopen Stage 1 or 2 and force dependent methods/evaluation to be revised.
The core process is scientist-in-the-loop agile specification. Literature workflow
reconstruction is a reusable capability within Stage 2, not the whole system.

## Separation of responsibilities

| Layer | Responsibility | Not a guarantee of |
|---|---|---|
| Skill instructions | Conversation, evidence handling, design procedure | Host compliance or permission enforcement |
| Domain profiles | Research-type planning prompts | Exhaustive scientific or regulatory guidance |
| Templates | Consistent planning artifacts | Scientific completeness merely from filled fields |
| Optional Python helper | Structural checks, scoped receipts, snapshots | Human identity, approval semantics, scientific validity |
| Host environment | Tool access, sandboxing, permissions and persistence | Data access just because a skill was installed |
| Human researcher | Scientific decisions and explicit confirmation | Actual availability of an approved planned resource |

## Approval binding

Each helper receipt records stage, scoped content digest, decision, researcher,
timestamp, source reference, actual confirmation quote and condition IDs. Approval
scope includes the stage's content and earlier sections. Stage 2 onward also binds
reference records; Stage 3 onward binds resources; Stage 4 onward binds issues;
Stage 5 also binds amendments, supporting records and earlier approval receipts.
The preamble and project intent metadata are covered too.

Changing a dependent input makes a former approval stale. Recording a new upstream
approval conservatively marks later approvals for reconfirmation. This prevents
"approved" flags from surviving meaningful draft changes unnoticed. It deliberately
prefers reconfirmation to guessing that a change is immaterial.

## Change management

A change request records the trigger, scope, consequences, alternatives and decision.
The helper opens a proposal and marks downstream approvals for review, but does not
choose an alternative or edit scientific text. The agent/researcher implements
approved changes in the draft, records the actual change decision, closes the request,
then reconfirms affected stages. Stage 5 approves the revised baseline.

## Baselines and integrity

The helper never intentionally overwrites an existing baseline and rejects decreasing
version numbers. A baseline contains the specification, machine state, supporting
planning records and file digests. `check` verifies snapshot inventories and hashes.
This is tamper-evident bookkeeping against ordinary accidental edits—not signed
storage, a security boundary or proof against an adversary who can rewrite manifests.
Use repository permissions/backups or a trusted external service for stronger controls.

## Runtime dependencies

Core: a language-model host that can read the skill. File tools are optional but
needed for persistence. Literature access depends on the user's available tools.
Helper: Python 3.10+ standard library, local only. No model provider dependency,
API key, analytics, telemetry, remote service or research-data pipeline is bundled.
No provider-specific tool allow-list preauthorizes execution.
