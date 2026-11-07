# Sources and design provenance

Reviewed on 2026-11-05. The five-stage ResearchFlow workflow, templates and helper
implementation are original project work developed from Yeong Chan Lee's stated
requirements. The sources below explain packaging, host behavior or design influences;
they are not empirical validation of ResearchFlow.

## Directly consulted implementation guidance

| Primary source | What informed this package |
|---|---|
| [Agent Skills specification](https://agentskills.io/specification) | Canonical folder name, required frontmatter, optional references/assets/scripts |
| [Agent Skills authoring practices](https://agentskills.io/skill-creation/best-practices) | Focused entry point, progressive disclosure, concrete procedures and evaluation |
| [Anthropic skill-creator](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md) | Separate drafting, test cases, behavior evaluation and revision; no benchmark claimed without actual runs |
| [Claude Code skills](https://code.claude.com/docs/en/skills) | Personal/project installation paths and explicit invocation |
| [Claude skill use](https://support.claude.com/en/articles/12512180-use-skills-in-claude) | Custom-skill ZIP upload and account-policy caveats |
| [OpenAI Build skills](https://learn.chatgpt.com/docs/build-skills) | Codex installation paths, invocation and optional UI metadata |
| [OpenAI Skills in ChatGPT](https://help.openai.com/en/articles/20001066-skills-in-chatgpt) | Distinction between packaged files and supported installation surfaces |

## Research and architectural motivation

Scientist-in-the-loop collaboration follows the motivation discussed in
[Epiflow's project](https://github.com/timothy0922/Epiflow). No unpublished manuscript,
private data or reported performance values are included in this release.

The design discussion also considered specification-driven development, dialogue-led
planning, and separate change proposals as architectural patterns. ResearchFlow is
not a fork of Spec Kit, OpenSpec, Superpowers, or another scientific-skills library.
No third-party source code from those projects is copied or bundled.

The conceptual diagram was supplied in the project conversation. It is an overview:
the single drawn feedback loop does not mean that revisions can return only to Stage 1.
Affected stages and dependencies can be revisited wherever appropriate.

## Limitations of this record

Authoring guidance is not a scientific evaluation. A local integrity checker does not
validate methods or authenticate confirmation provenance. Host feature availability
may change independently of this package; use primary product documentation rather
than treating this version's installation notes as permanent guarantees.
