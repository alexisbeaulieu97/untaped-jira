# untaped-jira

`untaped-jira` is a standalone Jira Data Center CLI built on the
[`untaped`](https://github.com/alexisbeaulieu97/untaped) SDK. It provides a
curated command group for daily ticket workflow: issue
lookup/search/create/edit/comment/transition plus lightweight project, board,
and sprint lookup helpers, alongside the shared `config`, `profile`, and
`skills` command groups every untaped tool ships.

## Install

```bash
uv tool install git+https://github.com/alexisbeaulieu97/untaped-jira.git
```

This also ships the `untaped-jira` agent skill; install it for Codex or Claude
with `untaped-jira skills install untaped-jira`.

## Configure

```bash
untaped-jira config set token --prompt        # bare key → this tool's section
untaped-jira config set base_url https://jira.example.com
untaped-jira me
untaped-jira --profile work me                 # --profile works in any position
```

Settings are stored per profile in `~/.untaped/config.yml` (shared with the
other untaped tools), under the `jira` section:

```yaml
profiles:
  default:
    jira:
      base_url: https://jira.example.com
      token: <personal-access-token>
      api_prefix: /rest/api/2
      agile_prefix: /rest/agile/1.0
      assigned_jql: assignee = currentUser() AND resolution = Unresolved
      default_project: ABC
      default_board_id: 42
      page_size: 50
```

`jira.token` is a secret setting; it is redacted by `untaped-jira config list`
and can also be provided through the environment:

```bash
export UNTAPED_JIRA__TOKEN=<personal-access-token>
```

## Daily Issue Commands

List tickets assigned to the authenticated Jira user:

```bash
untaped-jira issue assigned
```

`issue assigned` uses `jira.assigned_jql` by default. Pass `--jql` to override
that base query for one run, and combine it with shortcut filters such as
`--project`, `--status`, `--text`, or `--sprint`.

Fetch a single ticket by key or id:

```bash
untaped-jira issue get ABC-123
```

## Commands

```text
untaped-jira me
untaped-jira issue get|search|assigned|create|edit|comment|transitions|transition ...
untaped-jira project list|get ...
untaped-jira board list ...
untaped-jira sprint list ...
untaped-jira config|profile|skills ...
```

## Payload Templates

Create and edit payload files are Jira-shaped YAML or JSON. The CLI sends
`fields` and optional `update` through to Jira without modeling custom fields.

```yaml
fields:
  project:
    key: ABC
  issuetype:
    name: Bug
  summary: Fix deploy failure
  description: Deploy fails during artifact promotion.
  customfield_10000:
    value: Production
```

CLI flags overlay template fields, so project, issue type, summary,
description, `--field`, and `--json-field` can be used for small changes while
keeping company-specific fields in templates.

## Development

```bash
uv sync
uv run pytest
uv run mypy
uv run ruff check --fix
uv run ruff format
uv run untaped-jira --help
```

See [AGENTS.md](./AGENTS.md) for architecture rules and Jira-specific
contracts.

## Security

Please report suspected vulnerabilities privately. See
[SECURITY.md](./SECURITY.md).

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) and [AGENTS.md](./AGENTS.md) for the
local workflow, architecture rules, and Jira-specific contracts.

## License

MIT. See [LICENSE](./LICENSE).
