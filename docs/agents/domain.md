# Domain Docs

How the engineering skills should consume this repo's domain documentation when exploring the codebase.

## File structure

Single-context repo:

```
/
├── CONTEXT.md
├── docs/adr/
└── src/
```

## Before exploring, read these

- **`CONTEXT.md`** at the repo root
- **`docs/adr/`** — read ADRs that touch the area you're about to work in

If any of these files don't exist, **proceed silently**. Don't flag their absence.

## Use the glossary's vocabulary

When naming domain concepts, use the term as defined in `CONTEXT.md`. Don't drift to synonyms the glossary explicitly avoids.

## Flag ADR conflicts

If your output contradicts an existing ADR, surface it explicitly rather than silently overriding.
