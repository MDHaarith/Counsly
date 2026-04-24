<!-- BEGIN:nextjs-agent-rules -->
# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` before writing any code. Heed deprecation notices.
<!-- END:nextjs-agent-rules -->

## Framework

Before writing any code, read `FRAMEWORK.md` for the complete project structure, design rules, coding conventions, and agent coordination protocol.

## Timeline Registry Rule

All AI agents working in this repository must use `TIMELINE.md` as the shared append-only work registry.

- Append a new entry whenever you complete a meaningful task, make a change, or finish an investigation.
- Each entry must include the local timestamp, the agent name (`codex`, `claude`, `gemini`, etc.), and a concise summary of what was done.
- Include the main files touched when applicable.
- Keep entries in chronological order with new entries added at the end.
- Do not rewrite, delete, or reorder older entries unless the user explicitly asks for it.
