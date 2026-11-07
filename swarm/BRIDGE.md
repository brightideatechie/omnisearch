# OmniSearch ↔ Agent Swarm Bridge

This branch is the **inbox** for the Bright Idea Agent Swarm (Perchance).

## Protocol

The swarm communicates with the OmniSearch project by creating **GitHub Issues** in this repository.

### Required labels
- `swarm` — every message from the swarm must have this label
- `research` | `code` | `schema` | `prompt` | `status` — one primary type

### Issue title format
```
[swarm] <short description>
```

### Issue body format (markdown)

```markdown
## Task
<what the swarm was asked to do>

## Result
<the actual output: research summary, schema, code, prompt pack, etc.>

## Files (if any)
- path/to/file.ext — description

## Next recommended action
<what the human / other agents should do with this result>

## Swarm metadata
- agents involved: ...
- confidence: high | medium | low
```

### Optional: code delivery
If the swarm produces code, it should either:
1. Put the full file contents inside fenced code blocks in the issue body, **or**
2. Open a PR from a branch named `swarm/<short-task-name>` into `main` (preferred for larger changes).

## Receiving end (Grok / human)
- Watches issues with label `swarm`
- Reviews, audits, and either merges, requests changes, or feeds the result into other tools (Codex, Bolt, etc.)
- Replies on the issue with status / next instructions

## Status
Bridge receiving end is live as of 2026-11-07.
