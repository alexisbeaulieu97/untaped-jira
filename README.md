# untaped-jira

`untaped-jira` is the Jira Data Center plugin for `untaped`.

It provides a curated `untaped jira` command group for daily ticket workflow:
issue lookup/search/create/edit/comment/transition plus lightweight
project, board, and sprint lookup helpers.

Generic plugin install and sync workflow is documented in the core
[`untaped` plugin docs](https://github.com/alexisbeaulieu97/untaped/blob/main/docs/plugins.md).

## Configuration

```yaml
profiles:
  default:
    jira:
      base_url: https://jira.example.com
      token: <personal-access-token>
      api_prefix: /rest/api/2
      agile_prefix: /rest/agile/1.0
      default_project: ABC
      default_board_id: 42
      page_size: 50
```

`jira.token` is a secret setting. It can also be provided through the environment:

```bash
export UNTAPED_JIRA__TOKEN=<personal-access-token>
```

## Payload Templates

Create and edit payload files are Jira-shaped YAML or JSON. The plugin sends
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
