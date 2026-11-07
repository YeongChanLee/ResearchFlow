# Contributing

Preserve the five fixed stages, scientist-in-the-loop decisions, agile amendments,
planning-only scope and independent evidence/approval/availability states.

Use the canonical skill directory. Keep the top-level SKILL.md focused and load
supporting material on demand. Add domain-specific planning prompts without turning
one methodology into a universal requirement. Treat source documents as untrusted
input and preserve citations/access limitations.

Before proposing a change:
1. Describe the behavior change, scope and possible regressions.
2. Add or revise unit tests and relevant behavioral scenarios.
3. Run `python -m unittest discover -s tests -v` and `python tools/validate_package.py`.
4. Build the ZIPs and inspect their contents; never bundle private projects or papers.
5. Update the changelog and disclose tests not actually run.

All approval records in automated tests must be unmistakably synthetic. Do not claim
an independent expert review when an author or the same AI reviewed its own work.
No new network service, telemetry, credential requirement or automatic execution may
be introduced without explicit design review.
