# ResearchFlow 0.1.0 — Review and verification report

Initial review: 2026-11-05. Publication preparation resumed: 2026-11-07.
This report distinguishes the current publication-session checks
from the earlier authoring-session record. Both are **assistant self-review**, not
independent scientific expert review or hosted-model benchmarks.

## Publication-session verification

The supplied source ZIP was extracted to an isolated directory and checked again
on Linux with **Python 3.12.14**. These checks were rerun on 2026-11-07 for the resumed publication
session, rather than inferred from the earlier test log:

| Check | Actual result before publication |
|---|---|
| `python3 -m unittest discover -s tests -v` | **74 tests successful; 0 failures, 0 errors, 0 skipped** |
| `python3 tools/validate_package.py` | Passed |
| `python3 tools/build_release.py` | Passed; source ZIP, skill ZIP and SHA256SUMS.txt rebuilt |
| Publication-helper dry run | Passed; no remote mutation performed by the dry run |
| Public distribution inventory | 51 files; hidden configuration and CI included |
| README local links and image | All referenced local paths exist; workflow image inspected |
| Supplied install ZIP versus canonical skill | Identical file contents and `researchflow/SKILL.md` layout |
| Version and license | 0.1.0 consistent; repository and bundled MIT licenses identical |
| Sensitive-material review | No private research files or credential values detected in the reviewed inventory |
| Actual Claude/Codex behavioral evaluation | **Not run** |
| AI-account installation or marketplace registration | **Not performed** |

The authenticated GitHub connection identified `YeongChanLee`. The existing
`YeongChanLee/ResearchFlow` repository was public, default branch `main`, and empty:
its branch/release listings and `git ls-remote` contained no existing history.
The original connector write request returned HTTP 403 (`Resource not accessible
by integration`) despite the account-level repository permissions. The browser was
subsequently authenticated as `YeongChanLee` on 2026-11-07. GitHub CLI is installed
in the resumed environment but has no authenticated account. The existing empty
public repository is therefore being populated through the authenticated browser.
The included publication helper was reviewed and its dry run checked. Its execute
mode deliberately refuses an existing remote, so the browser resumes this empty
repository without invoking the new-repository creation helper.

This section records **pre-publication** verification only. Repository commits,
release assets, downloaded checksums and remote Actions results must be verified
from GitHub separately and are not inferred from these local tests. The final
publication record and release notes distinguish completed remote checks from any
remaining authentication or tool limitations.

The fixed stages, approval policy, planning-only scope, skill implementation and MIT
license were not changed for deployment. Only this report and its detailed test log
were updated to distinguish current evidence from historical results.

## Initial authoring-session record (historical)

The following summary and earlier defect history are retained as authoring provenance.
In particular, the earlier environment and publication blocker are historical facts,
not claims about the tools or repository state in the current publication session.

### Initial status summary

| Item | Result |
|---|---|
| Canonical Agent Skills package | Created; fixed five-stage entry point, references and templates |
| Automated local tests | **74 passed**, zero failures or errors |
| Package lint | Passed: metadata conventions, stage names/order, local links, Python syntax, distribution scope |
| YAML parsing | Passed for SKILL.md frontmatter, host metadata, CI workflow and citation file |
| Skill ZIP extraction and helper smoke test | Passed in the unit suite |
| Local installation to an isolated directory | Passed; existing installation overwrite rejected |
| Reproducible packaging and checksums | Passed in the unit suite |
| Extracted source with local Git metadata | Passed: a separately extracted source ZIP was initialized as a Git checkout and all 74 tests plus lint passed again |
| Real Claude/Codex behavioral runs | **Not run**; 20 scenarios supplied for future evaluation |
| Human scientific validation | **Not performed** |
| GitHub publication | **Not completed**; write-capable authenticated publishing environment unavailable |
| Installation in the user's AI account | **Not performed** |

Local environment: Python 3.13.5, Linux.
The helper targets Python 3.10+; other interpreter/operating-system combinations were
not actually run here. Cross-platform paths are implemented, not a claim of tested
Windows/macOS host behavior.

## Requirements review

| Requirement | Implementation/review evidence |
|---|---|
| Keep the five exact stages | Core skill, JSON/spec templates and tests validate names/order |
| Scientist-in-the-Loop is central | Stage-specific decision packets and scoped confirmation policy |
| Reverse engineering is important, not the whole framework | Stage 2 reference selection + reported-workflow reconstruction |
| Broad research applicability | Profiles for computational, laboratory, observational, qualitative, theoretical, simulation, humanities and mixed-method work |
| Discuss variables/resources and acquisition | Stage 3 definitions, access/content checks, acquisition and contingencies |
| Stop at the research specification | Explicit execution boundaries; helper has no network or research-execution imports |
| Honest evidence extraction | Reported / not reported / inaccessible / conflicting / inferred / proposed distinctions |
| Agile updates when data cannot be obtained | Change proposals, impact scope, alternatives, reconfirmation and new baseline |
| Keep approval, evidence and availability separate | Independent fields, receipt checks, resource and issue states |
| Preserve previous approved plans | Versioned snapshots, overwrite rejection and hash/inventory verification |
| Ground changed design in researcher decisions | Change decision records and new stage confirmations |
| Support teaching and subsequent distribution | English/Korean README, lecture notes, fictional teaching walkthrough and portable ZIP |

## Defects found and corrected during review

1. **Approval scope:** approval digests now include the shared preamble and project
   framing metadata, upstream specification sections and relevant supporting records.
   An edit outside a numbered section cannot silently retain an old approval.
2. **Availability changes:** changing resource metadata invalidates affected dependent
   confirmations rather than treating researcher approval as proof of availability.
3. **Readiness label:** integrity errors now produce a blocked status, never a misleading
   ready-for-handoff label alongside an error.
4. **Conditions:** final approval must acknowledge every pending required-resource or
   execution-level condition; ordinary checks also detect a missing acknowledgement.
5. **Dependency status:** downstream confirmations require current upstream confirmation,
   not merely matching text with an upstream approval flagged for review.
6. **Platform-independent scope keys:** reference paths in approval digests use POSIX
   separators so host path notation alone does not redefine the scoped file keys.
7. **Checkout independence:** a publishing-guard test was changed to use an isolated
   temporary root, so a real Git checkout does not invalidate its setup assumptions.
8. **History:** actual receipt contents are retained in the local event log and snapshot
   set rather than retaining only a shorthand reference.

## Automated coverage

The suite checks incomplete drafts; scoped approvals; missing/ambiguous-by-structure
receipts; skipped stages; stale approvals; upstream/downstream propagation; resource
and issue prerequisites; conditional plans; unavailable resources; change proposals;
change closure evidence; baseline preservation; tampered snapshots; invalid paths;
symlinks; locking; malformed state; installer paths and overwrite refusal; ZIP layout;
reproducibility; checksums; extracted helper operation; publishing dry-run, wrong-account
and missing-tool guards. Test approval and evidence data are explicitly **synthetic**.

Current publication-session local output: [test-results.txt](test-results.txt).
The tests do not understand scientific adequacy or the semantics of a researcher's
quote. The helper records provenance but cannot authenticate identity. Hash manifests
are not signed, tamper-proof storage.

## Behavioral evaluation status

The 20 cases in [evals/evals.json](../evals/evals.json) cover fresh/resumed projects,
reference selection, inaccessible/conflicting sources, method transfer, unavailable
or planned data, partial/ambiguous approval, unattended drafting, qualitative/theoretical
research, post-result changes, execution requests, prompt injection, no filesystem,
stale confirmations, stopping and completeness-versus-validity. They were reviewed
as design requirements, **not run as independent model trials**. No behavioral pass
rate or gain over an unskilled baseline is claimed.

## Earlier publication evidence and blocker (historical)

The connected account was identifiable as `YeongChanLee`, but the current connector
exposed read-only operations and returned no installed repository-access entries.
A read for `YeongChanLee/ResearchFlow` returned 404; that alone cannot prove global
nonexistence. No write operation was available through the connector.

The explicit local publication attempt stopped before any remote write with:
`Missing required publishing tool: gh`. No GitHub CLI authentication/token was present
in the authoring environment. Therefore no repository, commit, release or marketplace
listing is represented as created remotely.

The package includes a [publication helper](publishing.md) for an authenticated
Git/gh environment. Its dry run and safety guards were tested; the live remote
creation/push/release path was **not integration-tested** in this session.

## Release limitations

This is a reviewed initial development package, not a guarantee of error-free behavior,
research validity or universal host compatibility. Public publication uses the included
MIT license only after the maintainer reviews and explicitly executes that action.
Private research workspaces, uploaded papers and credentials are not release assets.
