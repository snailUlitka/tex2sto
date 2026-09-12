# Engineering Harness

This directory stores durable engineering context for agents and maintainers.
It is intentionally separate from the Russian user documentation in `docs/`.

## Documents

- [product.md](product.md) defines the goal, v1 scope, non-goals, and confirmed
  product decisions.
- [architecture.md](architecture.md) defines the implemented toolchain, pipeline,
  component boundaries, output contracts, and repository shape.
- [validation.md](validation.md) defines diagnostics, compliance boundaries,
  regression fixtures, and dependency-upgrade gates.
- [roadmap.md](roadmap.md) records sequencing and decisions that are explicitly
  deferred rather than accidentally omitted.
- [standards/ssau.md](standards/ssau.md) is a derived implementation checklist
  for STO 02068410-004-2018. It is not a replacement for the source standard.

## Agent Operating Policy

### Autonomous semantic decisions

Work as autonomously as the authorized scope and safety constraints allow. A
missing semantic, product, dialect, or implementation choice should not block
progress when a reasonable baseline can preserve the intended scope. Choose a
conservative and reversible baseline, encode the decision in the relevant
documentation and tests when it becomes durable, and continue the work.

Report the material alternatives and the selected baseline to the user after
the coherent change is complete. Ask before proceeding only when the decision
requires new authority, changes the agreed product scope materially, creates an
external commitment, or has security, privacy, destructive, or similarly
safety-sensitive consequences.

### Commit discipline

Create Git commits autonomously after every important, coherent change once its
relevant validation passes. Keep unrelated changes in separate commits and do
not include pre-existing user work that is outside the active task.

Use an English lowercase subject with a semantic type and a bullet-list body:

```text
<type>: <lowercase summary>

- <completed work>
- <validation or another completed item>
```

Use a specific lowercase type such as `chore`, `docs`, `feature`, `fix`,
`refactor`, or `test`. The subject and every body bullet must describe work that
is present in that commit.

Describe the externally understandable result, not the planning artifact that
prompted it. Do not use internal workflow labels such as `backlog`, `roadmap
item`, `todo`, or `task` as the subject's main concept; name the behavior,
capability, or defect instead.

## Maintenance Contract

Record stable project decisions here after they are confirmed. Do not preserve
brainstorming, generic Python advice, copied converter manuals, or the complete
text of external standards.

When implementation changes:

1. Update the affected architecture or validation contract.
2. Update the derived standard checklist if compliance behavior changed.
3. Update Russian user documentation when the change is user-visible.
4. Add or update an executable fixture for a mechanically testable rule.
5. Remove guidance that the implementation has superseded.

Exact commands belong here only after they have been configured and verified in
the repository.
