# Installation

## Portable package

The canonical package is the directory `skills/researchflow/` with `SKILL.md` inside.
Inspect the files before installing. The source repository also includes maintainer
tests and tooling; those are not needed for the core skill.

Run from the source root:

```bash
python tools/install_skill.py --target claude
python tools/install_skill.py --target codex
```

Choose the host you use; neither command overwrites an existing installation.
For a project-scoped installation:

```bash
python tools/install_skill.py --target claude --project /path/to/project
python tools/install_skill.py --target codex --project /path/to/project
```

For a custom destination or test installation:

```bash
python tools/install_skill.py --destination /path/to/skills/researchflow
```

The destination's final directory must be `researchflow`. Updates are deliberate:
review the new package, back up or remove the old skill directory yourself, then
install. There is no automatic updater or hidden overwrite flag.

## Host-specific discovery

**Claude Code:** personal `~/.claude/skills/researchflow/`; project
`.claude/skills/researchflow/`. Invoke `/researchflow`.

**Codex:** personal `~/.agents/skills/researchflow/`; project
`.agents/skills/researchflow/`. Invoke `$researchflow` or choose it through the skill
selector. This package includes optional `agents/openai.yaml` UI metadata.

**Custom-skill upload interfaces:** build or use `researchflow-skill-0.1.0.zip`, whose
root folder is `researchflow/` and contains `SKILL.md`. In Claude's supported interface,
upload through the Skills/customization UI. In supported ChatGPT surfaces, use the
provided custom-skill installation/import flow. Availability and organization policies
vary; a file attached to a chat is not proof that the skill is persistently installed.
A GitHub source repository is not a public plugin-directory listing.

**Other Agent Skills hosts:** install the canonical folder through that host's documented
mechanism. No automatic connector or data-access permission is granted.

## Verify locally

Ask the host to use ResearchFlow to frame a simple fictional research question. It
should propose Stage 1 content, distinguish assumptions, and request scoped
confirmation rather than completing and approving all stages by itself. Then check
that the intended persistent project files exist when file tools are used.

The optional Python helper is independent of host installation:

```bash
python skills/researchflow/scripts/researchflow.py init ./workspaces/demo --title "My research"
python skills/researchflow/scripts/researchflow.py check ./workspaces/demo
```

On Windows, `python` may be invoked as `py -3`; use the command registered for a Python
3.10+ interpreter. No pip dependencies are needed.

## Documentation sources

Reviewed 2026-11-05. Host behavior can change; the upstream pages are authoritative.
- [Agent Skills specification](https://agentskills.io/specification)
- [Claude Code skills](https://code.claude.com/docs/en/skills)
- [Using skills in Claude](https://support.claude.com/en/articles/12512180-use-skills-in-claude)
- [OpenAI: Build skills](https://learn.chatgpt.com/docs/build-skills)
- [OpenAI: Skills in ChatGPT](https://help.openai.com/en/articles/20001066-skills-in-chatgpt)
