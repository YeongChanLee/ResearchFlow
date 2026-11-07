# Maintainer instructions for ResearchFlow

ResearchFlow develops research specifications; it does not execute scientific studies.
Preserve these five exact stages and their order:
1. Research Framing
2. Literature Discovery & Workflow Reconstruction
3. Data & Resource Co-design
4. Methodology & Evaluation Design
5. Specification Review & Baseline Approval

Keep scientist-in-the-loop collaboration and agile specifications central. Do not
make reverse engineering the framework's overall center or narrow it to cohort work.
Separate approval, evidence quality and resource availability. Never fabricate a
researcher's confirmation. Do not publish private research workspaces or papers.

Edit the canonical skill in skills/researchflow only; do not duplicate competing
copies. Keep SKILL.md concise and put detail in references and templates.
The helper uses Python 3.10+ standard library only and does no network I/O.
Run `python -m unittest discover -s tests -v` and `python tools/validate_package.py`.
Behavioral evaluation scenarios are not passed merely because static checks pass.
Update docs/review-report.md honestly; do not claim an independent/model benchmark
or remote deployment that was not actually performed.
