# AGENTS.md - `untaped-jira`

Single source of truth for Jira-specific guidance in this standalone CLI repo.
Suite-wide conventions live in the core SDK docs:
`untaped/docs/plugins.md` and `untaped/docs/tool-conventions.md`. This file
keeps only Jira rules, contracts, and gotchas.

## Mission

`untaped-jira` is a standalone CLI built on the `untaped` SDK, invoked as
`untaped-jira`. It owns Jira Data Center ticket workflow: issue
lookup/search/create/edit/comment/transition plus lightweight project, board,
and sprint lookup helpers. The `untaped` SDK owns the binary, config loading,
output helpers, HTTP/TLS primitives, profile selection, and shared errors.
Profile selection is built into the SDK and works in any token position.

## Hard Rules

1. **Keep `AGENTS.md` and the packaged skill up to date.** Architecture,
   command behavior, settings, and major Jira workflow changes must be
   documented here and in
   `src/untaped_jira/skills/untaped-jira/SKILL.md`.
2. **Expose the CLI through the SDK entry point.** The console script
   `untaped-jira = "untaped_jira.__main__:main"` hands the Cyclopts `app`
   and a `ToolSpec` to `untaped.api.run_tool`. The `ToolSpec` declares
   `command="untaped-jira"`, `section="jira"`, `profile_model=JiraSettings`,
   and the packaged `untaped-jira` skill. `untaped_jira/__init__.py`
   re-exports `app` lazily via a PEP 562 module `__getattr__` so importing
   the package stays CLI-free.
3. **Import the SDK surface from `untaped.api` only** (tests may also use
   `untaped.testing`, plus SDK internals such as `untaped.settings`/
   `untaped.identity` when a name is not exported by `untaped.api`). Never
   reach into core internals from `src/`.
4. **Cyclopts command signatures are explicit.** Use
   `Annotated[..., Parameter(...)]` and explicit public names. Required
   inputs are required positional-only params (`Parameter(help=...)` before
   `/`); a missing value renders `error: ... requires an argument` (exit 2)
   automatically -- never an optional default plus a manual help dance.
5. **Secrets stay secret.** `JiraSettings.token` is a `SecretStr`.
6. **CLI commands resolve settings through bare `untaped.api.app_context()`.**
   Profile selection is owned by the SDK's root `--profile` option (valid in
   any token position); commands must not declare their own `--profile`. The
   Jira HTTP client is built with `untaped.api.connected_client` (settings
   validation, bearer auth, TLS resolution) and passes Jira's explicit
   `startAt`/`maxResults` parameter names to `untaped.api.paginate_offset`.

## Architecture

```text
src/untaped_jira/
├── __init__.py       # small root API: JiraClient, JiraSettings, lazy app
├── __main__.py       # console-script entrypoint: run_tool(app, SPEC)
├── settings.py       # config model for this tool's `jira` section
├── cli/              # Cyclopts commands; composition root
├── application/      # use cases and ports
├── domain/           # pure models and helpers
└── infrastructure/   # JiraClient, REST pagination
```

The CLI declares `JiraSettings` as its `jira` settings section, mounts the
Cyclopts `app` as the root command, and ships the packaged `untaped-jira`
agent skill. Keep that static skill asset current with major Jira workflow
changes. Command code reads typed settings with
`app_context().section("jira", JiraSettings)`, not a global aggregate
attribute.

## Jira Target

V1 targets Jira Data Center / self-hosted Jira. It uses:

- `/rest/api/2` for platform resources such as issues, comments,
  transitions, projects, search, and `myself`.
- `/rest/agile/1.0` for Jira Software boards and sprints.

Cloud REST v3, Basic auth, OAuth, attachments, worklogs, Jira Service
Management request APIs, and admin CRUD are out of scope for V1.

## Auth Model

The CLI uses personal access tokens as bearer tokens:
`Authorization: Bearer <token>`.

Settings live under `jira`:

```yaml
profiles:
  default:
    jira:
      base_url: https://jira.example.com
      token: <personal-access-token>
      assigned_jql: assignee = currentUser() AND resolution = Unresolved
```

`jira.token` is redacted by `untaped-jira config list` and can be supplied by
`UNTAPED_JIRA__TOKEN`.

`untaped-jira issue assigned` lists the authenticated user's assigned issues
using `jira.assigned_jql` unless `--jql` is passed. `untaped-jira issue get KEY`
is the canonical concise ticket lookup command.

## Output and piping

Jira row-producing commands tag `--format pipe` records with these namespaced
`kind` hints:

| `kind` | Commands |
| --- | --- |
| `jira.issue` | `issue get` / `search` / `assigned` / `create` / `edit` / `transition` |
| `jira.comment` | `issue comment` |
| `jira.transition` | `issue transitions` |
| `jira.project` | `project list` / `get` |
| `jira.board` | `board list` |
| `jira.sprint` | `sprint list` |
| `jira.user` | `me` |

## See Also

- [`untaped` SDK](https://github.com/alexisbeaulieu97/untaped) - CLI
  launcher, settings registry, config-file helpers, output helpers.
- [`untaped` configuration docs](https://github.com/alexisbeaulieu97/untaped/blob/main/docs/configuration.md)
  - user-facing profile, config, secrets, and TLS behavior.
