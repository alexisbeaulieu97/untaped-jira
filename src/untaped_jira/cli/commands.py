"""Cyclopts commands for Jira Data Center ticket workflow."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated, Literal

from cyclopts import Parameter, validators
from untaped.api import (
    ColumnsOption,
    ConfigError,
    FormatOption,
    ProfileOverrideOption,
    create_app,
    echo,
    existing_file,
    parse_kv_pairs,
    render_rows,
    report_errors,
)

from untaped_jira.cli._client import current_jira_settings, open_client
from untaped_jira.domain import (
    JiraIssueSearchFilters,
    build_issue_payload,
    parse_json_field_assignments,
    read_payload_file,
)

LimitOption = Annotated[
    int,
    Parameter(
        name="--limit",
        validator=validators.Number(gte=1),
        help="Maximum rows to return.",
    ),
]
FieldOption = Annotated[
    list[str] | None,
    Parameter(name="--field", help="Set a string field KEY=VALUE.", consume_multiple=False),
]
JsonFieldOption = Annotated[
    list[str] | None,
    Parameter(name="--json-field", help="Set a field from JSON KEY=JSON.", consume_multiple=False),
]
app = create_app(
    name="jira",
    help="Manage Jira Data Center tickets from untaped.",
)
issue_app = create_app(name="issue", help="Manage Jira issues.")
project_app = create_app(name="project", help="Look up Jira projects.")
board_app = create_app(name="board", help="Look up Jira Software boards.")
sprint_app = create_app(name="sprint", help="Look up Jira Software sprints.")


@app.command(name="me")
def me_command(
    *,
    fmt: FormatOption = "table",
    columns: ColumnsOption = None,
    profile: ProfileOverrideOption = None,
) -> None:
    """Show the authenticated Jira user."""

    from untaped_jira.application import WhoAmI  # noqa: PLC0415

    with report_errors():
        with open_client(profile) as client:
            row = WhoAmI(client)().model_dump()
        echo(render_rows([row], fmt=fmt, columns=columns))


@issue_app.command(name="get")
def issue_get_command(
    key: Annotated[str, Parameter(help="Issue key or id.")],
    /,
    *,
    fmt: FormatOption = "table",
    columns: ColumnsOption = None,
    profile: ProfileOverrideOption = None,
) -> None:
    """Fetch one issue."""

    from untaped_jira.application import GetIssue  # noqa: PLC0415

    with report_errors():
        with open_client(profile) as client:
            row = GetIssue(client)(key).model_dump()
        echo(render_rows([row], fmt=fmt, columns=columns))


@issue_app.command(name="search")
def issue_search_command(
    *,
    jql: Annotated[str | None, Parameter(name="--jql", help="Raw JQL base query.")] = None,
    project: Annotated[str | None, Parameter(name="--project")] = None,
    assignee: Annotated[str | None, Parameter(name="--assignee")] = None,
    status: Annotated[str | None, Parameter(name="--status")] = None,
    text: Annotated[str | None, Parameter(name="--text")] = None,
    sprint: Annotated[str | None, Parameter(name="--sprint")] = None,
    limit: LimitOption = 50,
    fmt: FormatOption = "table",
    columns: ColumnsOption = None,
    profile: ProfileOverrideOption = None,
) -> None:
    """Search issues with JQL plus common shortcuts."""

    from untaped_jira.application import SearchIssues  # noqa: PLC0415

    with report_errors():
        filters = JiraIssueSearchFilters(
            raw_jql=jql,
            project=project,
            assignee=assignee,
            status=status,
            text=text,
            sprint=sprint,
        )
        with open_client(profile) as client:
            rows = [issue.model_dump() for issue in SearchIssues(client)(filters, limit=limit)]
        echo(render_rows(rows, fmt=fmt, columns=columns))


@issue_app.command(name="assigned")
def issue_assigned_command(
    *,
    jql: Annotated[str | None, Parameter(name="--jql", help="Raw JQL base query.")] = None,
    project: Annotated[str | None, Parameter(name="--project")] = None,
    status: Annotated[str | None, Parameter(name="--status")] = None,
    text: Annotated[str | None, Parameter(name="--text")] = None,
    sprint: Annotated[str | None, Parameter(name="--sprint")] = None,
    limit: LimitOption = 50,
    fmt: FormatOption = "table",
    columns: ColumnsOption = None,
    profile: ProfileOverrideOption = None,
) -> None:
    """List issues assigned to the authenticated Jira user."""

    from untaped_jira.application import SearchIssues  # noqa: PLC0415

    with report_errors():
        settings = current_jira_settings(profile)
        filters = JiraIssueSearchFilters(
            raw_jql=_resolve_assigned_jql(jql=jql, configured=settings.assigned_jql),
            project=project,
            status=status,
            text=text,
            sprint=sprint,
        )
        with open_client(profile) as client:
            rows = [issue.model_dump() for issue in SearchIssues(client)(filters, limit=limit)]
        echo(render_rows(rows, fmt=fmt, columns=columns))


def _resolve_assigned_jql(*, jql: str | None, configured: str) -> str:
    if jql is None:
        return configured
    stripped = jql.strip()
    if not stripped:
        raise ConfigError("--jql must not be blank")
    return stripped


@issue_app.command(name="create")
def issue_create_command(
    *,
    template: Annotated[
        Path | None,
        Parameter(name="--template", validator=existing_file),
    ] = None,
    project: Annotated[str | None, Parameter(name="--project")] = None,
    issue_type: Annotated[str | None, Parameter(name="--issue-type")] = None,
    summary: Annotated[str | None, Parameter(name="--summary")] = None,
    description: Annotated[str | None, Parameter(name="--description")] = None,
    field: FieldOption = None,
    json_field: JsonFieldOption = None,
    fmt: FormatOption = "table",
    columns: ColumnsOption = None,
    profile: ProfileOverrideOption = None,
) -> None:
    """Create one issue from flags and an optional Jira-shaped template."""

    from untaped_jira.application import CreateIssue  # noqa: PLC0415

    with report_errors():
        base = read_payload_file(template) if template is not None else {}
        payload = build_issue_payload(
            base=base,
            project=project or current_jira_settings(profile).default_project,
            issue_type=issue_type,
            summary=summary,
            description=description,
            fields=parse_kv_pairs(field, flag="--field"),
            json_fields=parse_json_field_assignments(json_field),
        )
        with open_client(profile) as client:
            row = CreateIssue(client)(payload).model_dump()
        echo(render_rows([row], fmt=fmt, columns=columns))


@issue_app.command(name="edit")
def issue_edit_command(
    key: Annotated[str, Parameter(help="Issue key or id.")],
    /,
    *,
    body_file: Annotated[
        Path | None,
        Parameter(name="--body-file", validator=existing_file),
    ] = None,
    summary: Annotated[str | None, Parameter(name="--summary")] = None,
    description: Annotated[str | None, Parameter(name="--description")] = None,
    field: FieldOption = None,
    json_field: JsonFieldOption = None,
    fmt: FormatOption = "table",
    columns: ColumnsOption = None,
    profile: ProfileOverrideOption = None,
) -> None:
    """Edit one issue from flags and an optional Jira-shaped body file."""

    from untaped_jira.application import EditIssue  # noqa: PLC0415

    with report_errors():
        base = read_payload_file(body_file) if body_file is not None else {}
        payload = build_issue_payload(
            base=base,
            summary=summary,
            description=description,
            fields=parse_kv_pairs(field, flag="--field"),
            json_fields=parse_json_field_assignments(json_field),
        )
        with open_client(profile) as client:
            row = EditIssue(client)(key, payload).model_dump()
        echo(render_rows([row], fmt=fmt, columns=columns))


@issue_app.command(name="comment")
def issue_comment_command(
    key: Annotated[str, Parameter(help="Issue key or id.")],
    /,
    *,
    body: Annotated[str | None, Parameter(name="--body", help="Comment body.")] = None,
    body_file: Annotated[
        Path | None,
        Parameter(name="--body-file", validator=existing_file),
    ] = None,
    fmt: FormatOption = "table",
    columns: ColumnsOption = None,
    profile: ProfileOverrideOption = None,
) -> None:
    """Add a comment to one issue."""

    from untaped_jira.application import AddComment  # noqa: PLC0415

    with report_errors():
        resolved_body = _resolve_body(body=body, body_file=body_file)
        with open_client(profile) as client:
            row = AddComment(client)(key, resolved_body).model_dump()
        echo(render_rows([row], fmt=fmt, columns=columns))


@issue_app.command(name="transitions")
def issue_transitions_command(
    key: Annotated[str, Parameter(help="Issue key or id.")],
    /,
    *,
    fmt: FormatOption = "table",
    columns: ColumnsOption = None,
    profile: ProfileOverrideOption = None,
) -> None:
    """List available workflow transitions for one issue."""

    from untaped_jira.application import ListTransitions  # noqa: PLC0415

    with report_errors():
        with open_client(profile) as client:
            rows = [transition.model_dump() for transition in ListTransitions(client)(key)]
        echo(render_rows(rows, fmt=fmt, columns=columns))


@issue_app.command(name="transition")
def issue_transition_command(
    key: Annotated[str, Parameter(help="Issue key or id.")],
    /,
    *,
    to: Annotated[str | None, Parameter(name="--to", help="Transition name.")] = None,
    transition_id: Annotated[str | None, Parameter(name="--id", help="Transition id.")] = None,
    fmt: FormatOption = "table",
    columns: ColumnsOption = None,
    profile: ProfileOverrideOption = None,
) -> None:
    """Apply one workflow transition by name or id."""

    from untaped_jira.application import TransitionIssue  # noqa: PLC0415

    with report_errors():
        with open_client(profile) as client:
            row = TransitionIssue(client)(
                key,
                transition_id=transition_id,
                transition_name=to,
            ).model_dump()
        echo(render_rows([row], fmt=fmt, columns=columns))


@project_app.command(name="list")
def project_list_command(
    *,
    fmt: FormatOption = "table",
    columns: ColumnsOption = None,
    profile: ProfileOverrideOption = None,
) -> None:
    """List visible projects."""

    from untaped_jira.application import ListProjects  # noqa: PLC0415

    with report_errors():
        with open_client(profile) as client:
            rows = [project.model_dump() for project in ListProjects(client)()]
        echo(render_rows(rows, fmt=fmt, columns=columns))


@project_app.command(name="get")
def project_get_command(
    key: Annotated[str, Parameter(help="Project key or id.")],
    /,
    *,
    fmt: FormatOption = "table",
    columns: ColumnsOption = None,
    profile: ProfileOverrideOption = None,
) -> None:
    """Fetch one project."""

    from untaped_jira.application import GetProject  # noqa: PLC0415

    with report_errors():
        with open_client(profile) as client:
            row = GetProject(client)(key).model_dump()
        echo(render_rows([row], fmt=fmt, columns=columns))


@board_app.command(name="list")
def board_list_command(
    *,
    project: Annotated[
        str | None,
        Parameter(name="--project", help="Filter by project key or id."),
    ] = None,
    name: Annotated[str | None, Parameter(name="--name", help="Filter by board name.")] = None,
    board_type: Annotated[Literal["scrum", "kanban"] | None, Parameter(name="--type")] = None,
    limit: LimitOption = 50,
    fmt: FormatOption = "table",
    columns: ColumnsOption = None,
    profile: ProfileOverrideOption = None,
) -> None:
    """List visible Jira Software boards."""

    from untaped_jira.application import ListBoards  # noqa: PLC0415

    with report_errors():
        with open_client(profile) as client:
            rows = [
                board.model_dump()
                for board in ListBoards(client)(
                    project_key_or_id=project,
                    name=name,
                    board_type=board_type,
                    limit=limit,
                )
            ]
        echo(render_rows(rows, fmt=fmt, columns=columns))


@sprint_app.command(name="list")
def sprint_list_command(
    *,
    board_id: Annotated[int | None, Parameter(name="--board-id", help="Board id.")] = None,
    state: Annotated[
        str | None,
        Parameter(name="--state", help="Sprint state filter, e.g. active,future."),
    ] = None,
    limit: LimitOption = 50,
    fmt: FormatOption = "table",
    columns: ColumnsOption = None,
    profile: ProfileOverrideOption = None,
) -> None:
    """List sprints for a board."""

    from untaped_jira.application import ListSprints  # noqa: PLC0415

    with report_errors():
        settings = current_jira_settings(profile)
        with open_client(profile) as client:
            rows = [
                sprint.model_dump()
                for sprint in ListSprints(client, default_board_id=settings.default_board_id)(
                    board_id=board_id,
                    state=state,
                    limit=limit,
                )
            ]
        echo(render_rows(rows, fmt=fmt, columns=columns))


def _resolve_body(*, body: str | None, body_file: Path | None) -> str:
    if body is not None and body_file is not None:
        raise ConfigError("provide --body or --body-file, not both")
    if body is not None:
        return body
    if body_file is not None:
        try:
            return _trim_terminal_newline(body_file.read_text())
        except OSError as exc:
            raise ConfigError(f"could not read {body_file}: {exc}") from exc
    if not sys.stdin.isatty():
        raw_body = sys.stdin.read()
        if raw_body.strip():
            return _trim_terminal_newline(raw_body)
    raise ConfigError("comment body is required (pass --body, --body-file, or stdin)")


def _trim_terminal_newline(value: str) -> str:
    if value.endswith("\r\n"):
        return value[:-2]
    if value.endswith(("\n", "\r")):
        return value[:-1]
    return value


app.command(issue_app, name="issue")
app.command(project_app, name="project")
app.command(board_app, name="board")
app.command(sprint_app, name="sprint")
