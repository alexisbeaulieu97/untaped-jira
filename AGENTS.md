# AGENTS.md - `untaped-jira`

Single source of truth for this standalone plugin repo. If architecture,
command behavior, settings behavior, or workflow changes, update this file
in the same commit.

## Mission

`untaped-jira` is an `untaped` plugin. It owns the `untaped jira` command
group for Jira Data Center ticket workflow. `untaped` core owns the binary,
plugin discovery, config/profile resolution, output helpers, HTTP/TLS
primitives, and shared errors.

## Hard Rules

1. Keep `AGENTS.md` up to date.
2. Expose the plugin through the `untaped.plugins` entry point.
3. Use the 4-layer plugin layout: `cli -> application -> domain`, with
   `infrastructure -> domain`.
4. Declare use-case ports in `application/ports.py`.
5. Use absolute imports only.
6. Every Typer app and every command with required args sets
   `no_args_is_help=True`.
7. stdout is data only; diagnostics and status go to stderr.
8. Secrets stay secret. `JiraSettings.token` is a `SecretStr`.
9. Every Jira HTTP client must use `untaped.HttpClient` and
   `resolve_verify(settings.http)`.
10. Finish with `uv run ruff check`, `uv run ruff format`, `uv run mypy`,
    and `uv run pytest`.

## Architecture

```text
src/untaped_jira/
├── __init__.py
├── plugin.py
├── settings.py
├── cli/
├── application/
├── domain/
└── infrastructure/
```

The plugin registers `JiraSettings` as the `jira` profile settings section
and mounts the Typer app as the root `jira` command.

## Jira Target

V1 targets Jira Data Center / self-hosted Jira. It uses:

- `/rest/api/2` for platform resources such as issues, comments,
  transitions, projects, search, and `myself`.
- `/rest/agile/1.0` for Jira Software boards and sprints.

Cloud REST v3, Basic auth, OAuth, attachments, worklogs, Jira Service
Management request APIs, and admin CRUD are out of scope for V1.

## Auth Model

The plugin uses personal access tokens as bearer tokens:
`Authorization: Bearer <token>`.

Settings live under `jira`:

```yaml
profiles:
  default:
    jira:
      base_url: https://jira.example.com
      token: <personal-access-token>
```

`jira.token` is redacted by `untaped config list` and can be supplied by
`UNTAPED_JIRA__TOKEN`.
