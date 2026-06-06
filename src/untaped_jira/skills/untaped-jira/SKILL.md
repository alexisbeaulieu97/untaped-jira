---
name: untaped-jira
description: Use the untaped Jira plugin.
---

# Untaped Jira

Use this skill when the user wants an agent to operate `untaped jira` for Jira Data Center ticket workflows.

## Setup

- The plugin command group is `untaped jira`.
- V1 targets Jira Data Center and self-hosted Jira, not Jira Cloud REST v3.
- Settings live under `profiles.<name>.jira`: `base_url`, `token`, and optional defaults such as `default_board_id`.
- Use `untaped config set jira.token --prompt` or `--stdin` for personal access tokens.

## Command Patterns

- Use `untaped jira --help` and subcommand `--help` output to confirm the available V1 surface before acting.
- Jira platform calls use `/rest/api/2`; Jira Software board and sprint calls use `/rest/agile/1.0`.
- Prefer JSON output for issue, board, sprint, transition, project, and search workflows.
- Use configured defaults only after checking effective config with `untaped config list --format raw --columns key --columns value`.

## Agent Guidance

- Keep stdout data-only; parse `--format json` rather than table output.
- Do not assume Jira Cloud authentication or endpoints.
- Treat ticket mutations such as transitions or comments as explicit user intent.
- Never echo tokens or raw authorization headers.
