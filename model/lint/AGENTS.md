## Lint rules
- A rule has no exceptions: no allow list of files or lines. Every existing violation is fixed when the rule goes on; one that needs a design change stops and is reported.
- A targeted `# noqa: CODE` on a line that legitimately does the flagged thing is fine, kept honest by ruff's `PGH004` and `RUF100`; no rule bans suppression comments.
- Every rule has rule tests in `rule-tests/` and runs over all existing code before it lands.
- A rule enforces what can be decided syntactically; what needs counting across files is an audit.
