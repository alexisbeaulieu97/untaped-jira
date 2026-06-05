"""Typer commands for Jira Data Center ticket workflow."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Literal

import typer
from untaped import (
    ColumnsOption,
    ConfigError,
    FormatOption,
    ProfileOverrideOption,
    format_output,
    parse_kv_pairs,
    read_stdin,
    report_errors,
)

from untaped_jira.cli._client import current_jira_settings, open_client
from untaped_jira.domain import (
    JiraIssueSearchFilters,
    build_issue_payload,
    parse_json_field_assignments,
    read_payload_file,
)

LimitOption = Annotated[int, typer.Option("--limit", min=1, help="Maximum rows to return.")]

app = typer.Typer(
    name="jira",
    help="Manage Jira Data Center tickets from untaped.",
    no_args_is_help=True,
)
issue_app = typer.Typer(name="issue", help="Manage Jira issues.", no_args_is_help=True)
project_app = typer.Typer(name="project", help="Look up Jira projects.", no_args_is_help=True)
board_app = typer.Typer(name="board", help="Look up Jira Software boards.", no_args_is_help=True)
sprint_app = typer.Typer(name="sprint", help="Look up Jira Software sprints.", no_args_is_help=True)


@app.callback()
def _callback() -> None:
    """Manage Jira Data Center tickets from untaped."""


@app.command("me")
def me_command(
    fmt: FormatOption = "table",
    columns: ColumnsOption = None,
    profile: ProfileOverrideOption = None,
) -> None:
    """Show the authenticated Jira user."""

    from untaped_jira.application import WhoAmI  # noqa: PLC0415

    with report_errors(), open_client(profile) as client:
        row = WhoAmI(client)().model_dump()
        typer.echo(format_output([row], fmt=fmt, columns=columns))


@issue_app.command("get", no_args_is_help=True)
def issue_get_command(
    key: str = typer.Argument(help="Issue key or id."),
    fmt: FormatOption = "table",
    columns: ColumnsOption = None,
    profile: ProfileOverrideOption = None,
) -> None:
    """Fetch one issue."""

    from untaped_jira.application import GetIssue  # noqa: PLC0415

    with report_errors(), open_client(profile) as client:
        row = GetIssue(client)(key).model_dump()
        typer.echo(format_output([row], fmt=fmt, columns=columns))


@issue_app.command("search")
def issue_search_command(
    jql: str | None = typer.Option(None, "--jql", help="Raw JQL base query."),
    project: str | None = typer.Option(None, "--project"),
    assignee: str | None = typer.Option(None, "--assignee"),
    status: str | None = typer.Option(None, "--status"),
    text: str | None = typer.Option(None, "--text"),
    sprint: str | None = typer.Option(None, "--sprint"),
    limit: LimitOption = 50,
    fmt: FormatOption = "table",
    columns: ColumnsOption = None,
    profile: ProfileOverrideOption = None,
) -> None:
    """Search issues with JQL plus common shortcuts."""

    from untaped_jira.application import SearchIssues  # noqa: PLC0415

    with report_errors(), open_client(profile) as client:
        filters = JiraIssueSearchFilters(
            raw_jql=jql,
            project=project,
            assignee=assignee,
            status=status,
            text=text,
            sprint=sprint,
        )
        rows = [issue.model_dump() for issue in SearchIssues(client)(filters, limit=limit)]
        typer.echo(format_output(rows, fmt=fmt, columns=columns))


@issue_app.command("create")
def issue_create_command(
    template: Path | None = typer.Option(None, "--template", exists=True, dir_okay=False),
    project: str | None = typer.Option(None, "--project"),
    issue_type: str | None = typer.Option(None, "--issue-type"),
    summary: str | None = typer.Option(None, "--summary"),
    description: str | None = typer.Option(None, "--description"),
    field: list[str] | None = typer.Option(None, "--field", help="Set a string field KEY=VALUE."),
    json_field: list[str] | None = typer.Option(
        None, "--json-field", help="Set a field from JSON KEY=JSON."
    ),
    fmt: FormatOption = "table",
    columns: ColumnsOption = None,
    profile: ProfileOverrideOption = None,
) -> None:
    """Create one issue from flags and an optional Jira-shaped template."""

    from untaped_jira.application import CreateIssue  # noqa: PLC0415

    with report_errors(), open_client(profile) as client:
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
        row = CreateIssue(client)(payload).model_dump()
        typer.echo(format_output([row], fmt=fmt, columns=columns))


@issue_app.command("edit", no_args_is_help=True)
def issue_edit_command(
    key: str = typer.Argument(help="Issue key or id."),
    body_file: Path | None = typer.Option(None, "--body-file", exists=True, dir_okay=False),
    summary: str | None = typer.Option(None, "--summary"),
    description: str | None = typer.Option(None, "--description"),
    field: list[str] | None = typer.Option(None, "--field", help="Set a string field KEY=VALUE."),
    json_field: list[str] | None = typer.Option(
        None, "--json-field", help="Set a field from JSON KEY=JSON."
    ),
    fmt: FormatOption = "table",
    columns: ColumnsOption = None,
    profile: ProfileOverrideOption = None,
) -> None:
    """Edit one issue from flags and an optional Jira-shaped body file."""

    from untaped_jira.application import EditIssue  # noqa: PLC0415

    with report_errors(), open_client(profile) as client:
        base = read_payload_file(body_file) if body_file is not None else {}
        payload = build_issue_payload(
            base=base,
            summary=summary,
            description=description,
            fields=parse_kv_pairs(field, flag="--field"),
            json_fields=parse_json_field_assignments(json_field),
        )
        row = EditIssue(client)(key, payload).model_dump()
        typer.echo(format_output([row], fmt=fmt, columns=columns))


@issue_app.command("comment", no_args_is_help=True)
def issue_comment_command(
    key: str = typer.Argument(help="Issue key or id."),
    body: str | None = typer.Option(None, "--body", help="Comment body."),
    body_file: Path | None = typer.Option(None, "--body-file", exists=True, dir_okay=False),
    fmt: FormatOption = "table",
    columns: ColumnsOption = None,
    profile: ProfileOverrideOption = None,
) -> None:
    """Add a comment to one issue."""

    from untaped_jira.application import AddComment  # noqa: PLC0415

    with report_errors(), open_client(profile) as client:
        resolved_body = _resolve_body(body=body, body_file=body_file)
        row = AddComment(client)(key, resolved_body).model_dump()
        typer.echo(format_output([row], fmt=fmt, columns=columns))


@issue_app.command("transitions", no_args_is_help=True)
def issue_transitions_command(
    key: str = typer.Argument(help="Issue key or id."),
    fmt: FormatOption = "table",
    columns: ColumnsOption = None,
    profile: ProfileOverrideOption = None,
) -> None:
    """List available workflow transitions for one issue."""

    from untaped_jira.application import ListTransitions  # noqa: PLC0415

    with report_errors(), open_client(profile) as client:
        rows = [transition.model_dump() for transition in ListTransitions(client)(key)]
        typer.echo(format_output(rows, fmt=fmt, columns=columns))


@issue_app.command("transition", no_args_is_help=True)
def issue_transition_command(
    key: str = typer.Argument(help="Issue key or id."),
    to: str | None = typer.Option(None, "--to", help="Transition name."),
    transition_id: str | None = typer.Option(None, "--id", help="Transition id."),
    fmt: FormatOption = "table",
    columns: ColumnsOption = None,
    profile: ProfileOverrideOption = None,
) -> None:
    """Apply one workflow transition by name or id."""

    from untaped_jira.application import TransitionIssue  # noqa: PLC0415

    with report_errors(), open_client(profile) as client:
        row = TransitionIssue(client)(
            key,
            transition_id=transition_id,
            transition_name=to,
        ).model_dump()
        typer.echo(format_output([row], fmt=fmt, columns=columns))


@project_app.command("list")
def project_list_command(
    fmt: FormatOption = "table",
    columns: ColumnsOption = None,
    profile: ProfileOverrideOption = None,
) -> None:
    """List visible projects."""

    from untaped_jira.application import ListProjects  # noqa: PLC0415

    with report_errors(), open_client(profile) as client:
        rows = [project.model_dump() for project in ListProjects(client)()]
        typer.echo(format_output(rows, fmt=fmt, columns=columns))


@project_app.command("get", no_args_is_help=True)
def project_get_command(
    key: str = typer.Argument(help="Project key or id."),
    fmt: FormatOption = "table",
    columns: ColumnsOption = None,
    profile: ProfileOverrideOption = None,
) -> None:
    """Fetch one project."""

    from untaped_jira.application import GetProject  # noqa: PLC0415

    with report_errors(), open_client(profile) as client:
        row = GetProject(client)(key).model_dump()
        typer.echo(format_output([row], fmt=fmt, columns=columns))


@board_app.command("list")
def board_list_command(
    project: str | None = typer.Option(None, "--project", help="Filter by project key or id."),
    name: str | None = typer.Option(None, "--name", help="Filter by board name."),
    board_type: Literal["scrum", "kanban"] | None = typer.Option(None, "--type"),
    limit: LimitOption = 50,
    fmt: FormatOption = "table",
    columns: ColumnsOption = None,
    profile: ProfileOverrideOption = None,
) -> None:
    """List visible Jira Software boards."""

    from untaped_jira.application import ListBoards  # noqa: PLC0415

    with report_errors(), open_client(profile) as client:
        rows = [
            board.model_dump()
            for board in ListBoards(client)(
                project_key_or_id=project,
                name=name,
                board_type=board_type,
                limit=limit,
            )
        ]
        typer.echo(format_output(rows, fmt=fmt, columns=columns))


@sprint_app.command("list")
def sprint_list_command(
    board_id: int | None = typer.Option(None, "--board-id", help="Board id."),
    state: str | None = typer.Option(
        None, "--state", help="Sprint state filter, e.g. active,future."
    ),
    limit: LimitOption = 50,
    fmt: FormatOption = "table",
    columns: ColumnsOption = None,
    profile: ProfileOverrideOption = None,
) -> None:
    """List sprints for a board."""

    from untaped_jira.application import ListSprints  # noqa: PLC0415

    with report_errors(), open_client(profile) as client:
        settings = current_jira_settings(profile)
        rows = [
            sprint.model_dump()
            for sprint in ListSprints(client, default_board_id=settings.default_board_id)(
                board_id=board_id,
                state=state,
                limit=limit,
            )
        ]
        typer.echo(format_output(rows, fmt=fmt, columns=columns))


def _resolve_body(*, body: str | None, body_file: Path | None) -> str:
    if body is not None and body_file is not None:
        raise ConfigError("provide --body or --body-file, not both")
    if body is not None:
        return body
    if body_file is not None:
        try:
            return body_file.read_text().strip()
        except OSError as exc:
            raise ConfigError(f"could not read {body_file}: {exc}") from exc
    stdin_lines = read_stdin()
    if stdin_lines:
        return "\n".join(stdin_lines)
    raise ConfigError("comment body is required (pass --body, --body-file, or stdin)")


app.add_typer(issue_app, name="issue")
app.add_typer(project_app, name="project")
app.add_typer(board_app, name="board")
app.add_typer(sprint_app, name="sprint")
