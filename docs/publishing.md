# Publishing ResearchFlow to GitHub

The intended personal repository is **YeongChanLee/ResearchFlow**. Account connection,
repository authorization, and a supported write-capable interface are separate
requirements. A successful account lookup or a local ZIP does not establish publication.

## Safe publication helper

Requires Python 3.10+, Git and an authenticated GitHub CLI (`gh`). Authenticate through
GitHub CLI's normal browser/device flow. Never paste a token into a research conversation
or commit it to this repository.

```bash
gh auth login
python tools/publish_github.py --owner YeongChanLee
```

The first helper command is a **dry run**: it shows the target and actions and does
not contact GitHub or initialize a repository. To explicitly execute:

```bash
python tools/publish_github.py --owner YeongChanLee --execute
```

The helper verifies the active account, runs the local tests/lint/build, refuses an
existing remote repository, prepares a new local Git repository, creates the public
repository, pushes `main`, and creates a prerelease with the two ZIPs and checksums.
It never force-pushes, replaces an existing remote, embeds a credential, or assumes
an HTTP error other than a confirmed 404 means the repository is absent.

If a remote repository was already created during a partial failed attempt, do not
rerun blindly: inspect the error and the repository, then resume deliberately. The
helper stops rather than guessing that an existing repository can be overwritten.

Default license in the prepared package is MIT; review the license before public
publication. Only reusable skill source, synthetic examples and tests are published.
Keep real projects in a separate/private workspace (the default `workspaces/` directory
is ignored by Git and excluded from release packaging).

## Verify a successful publication

Check that the returned repository URL resolves under the correct owner; inspect
`skills/researchflow/SKILL.md`, the commit and release assets. CI completion, directory
listing in a skill marketplace, and installation in a particular AI account are
separate actions and must not be inferred from a successful Git push.
