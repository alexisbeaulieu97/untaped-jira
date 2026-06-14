# AGENTS.md - `untaped-jira`

Single source of truth for this standalone plugin repo. If architecture,
command behavior, settings behavior, or workflow changes, update this file
in the same commit.

## Mission

`untaped-jira` is an `untaped` plugin. It owns the `untaped jira` command
group for Jira Data Center ticket workflow. `untaped` core owns the binary,
plugin discovery, config loading, output helpers, HTTP/TLS primitives, and
shared errors. Profile selection is contributed by `untaped-profile`.

## Hard Rules

1. Keep `AGENTS.md` and the packaged skill up to date. Architecture, command
   behavior, settings, and major Jira workflow changes must be documented here
   and in `src/untaped_jira/skills/untaped-jira/SKILL.md`.
2. Expose the plugin through the `untaped.plugins` entry point. The plugin
   object must expose `id = "jira"`, literal `untaped_api_version = 5`,
   and `manifest()` returning an `untaped.api.PluginManifest`.
3. Import the SDK surface from `untaped.api` only (tests may also use
   `untaped.testing`). Never reach into core internals from `src/`.
4. `plugin.py` must never import the CLI app. The manifest declares
   `CliSpec(name="jira", import_path="untaped_jira.cli:app", help=...)` and
   `untaped_jira/__init__.py` re-exports `app` lazily via a PEP 562 module
   `__getattr__` so importing the package stays CLI-free.
5. Use the 4-layer plugin layout: `cli -> application -> domain`, with
   `infrastructure -> domain`.
6. Declare use-case ports in `application/ports.py`.
7. Use absolute imports only.
8. Cyclopts command signatures use `Annotated[..., Parameter(...)]` and
   explicit public names. Required inputs are required positional-only
   params (`Parameter(help=...)` before `/`); a missing value renders
   `error: ... requires an argument` (exit 2) automatically — never an
   optional default plus a manual help dance.
9. stdout is data only; diagnostics and status go to stderr.
10. Secrets stay secret. `JiraSettings.token` is a `SecretStr`.
11. CLI commands resolve settings through bare `untaped.api.plugin_context()`.
    Profile selection is owned by the root `--profile` option (valid in any
    token position); commands must not declare their own `--profile`. The
    Jira HTTP client is built with `untaped.api.connected_client` (settings
    validation, bearer auth, TLS resolution) and walks `startAt`/`maxResults`
    envelopes with `untaped.api.paginate_offset`.
12. Finish with `uv run ruff check`, `uv run ruff format`, `uv run mypy`,
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

The plugin manifest declares `JiraSettings` as the `jira` profile settings
section, contributes the root `jira` command as a lazy `CliSpec`
(`untaped_jira.cli:app` is imported only when the command is dispatched), and
ships the packaged `untaped-jira` agent skill. Keep that static skill asset
current with major Jira workflow changes.

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
      assigned_jql: assignee = currentUser() AND resolution = Unresolved
```

`jira.token` is redacted by `untaped config list` and can be supplied by
`UNTAPED_JIRA__TOKEN`.

`untaped jira issue assigned` lists the authenticated user's assigned issues
using `jira.assigned_jql` unless `--jql` is passed. `untaped jira issue get KEY`
is the canonical concise ticket lookup command.

## Output and piping

Every row-producing command supports `--format pipe` (core's self-describing
NDJSON): one `{"untaped":"1","kind":...,"record":{...}}` object per line, so a
jira command's output can be piped into another untaped command. Each record is
tagged with a namespaced `kind` hint:

| `kind` | Commands |
| --- | --- |
| `jira.issue` | `issue get` / `search` / `assigned` / `create` / `edit` / `transition` |
| `jira.comment` | `issue comment` |
| `jira.transition` | `issue transitions` |
| `jira.project` | `project list` / `get` |
| `jira.board` | `board list` |
| `jira.sprint` | `sprint list` |
| `jira.user` | `me` |

`kind` is an advisory hint, not a contract; downstream consumers validate only
the fields they need.
