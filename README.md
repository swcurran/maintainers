# Maintainers Generator<!-- omit in toc -->

The **Maintainers Generator** is a Python tool for automatically creating and updating `MAINTAINERS.md` for repositories whose GitHub access permissions are centrally managed in governance data using [CLOWarden] and “MAINTAINER.md” configuration files.

[CLOWarden]: https://github.com/clowarden/clowarden

It is designed for open-source organizations, foundations, multi-repo projects, and ecosystems where:

- GitHub permissions (teams, roles, repo membership) are defined centrally using [CLOWarden]
- Human-facing `MAINTAINERS.md` files in repositories are needed and must stay in sync with the [CLOWarden] data
- Governance policies (maintainer duties, adding/removing maintainers) should be consistent across all repos, but can be overridden at the project or repository level

The generator produces a complete `MAINTAINERS.md` including:

- A table of maintainers (GitHub IDs, names, emails, companies, roles) derived from the [CLOWarden] data
- A templated “before text” section explaining the file contents
- A templated “after text” section describing governance policies, maintainer duties, and instructions for updating maintainers
- Optional overrides at the project or repo level

It is best deployed centrally in the governance repository (beside the [CLOWarden] data) with a GitHub Actions workflow that updates all `MAINTAINERS.md` files via per-repository PRs. Alternatively, it can be deployed at the repository level or just run manually and pushed via a PR.

## Table of Contents<!-- omit in toc -->

- [How It Works](#how-it-works)
- [Deploying the Maintainer List Generator](#deploying-the-maintainer-list-generator)
- [Project or Repository-Level Configuration](#project-or-repository-level-configuration)
- [Running the Generator Locally](#running-the-generator-locally)
  - [Useful Options](#useful-options)
- [GitHub Action Usage](#github-action-usage)
  - [Per-Repository Workflow](#per-repository-workflow)
  - [Centralized Organizational Workflow (recommended)](#centralized-organizational-workflow-recommended)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)

## How It Works

The generator produces a `MAINTAINERS.md` file by combining:

### 1. Governance Access Configuration<!-- omit in toc -->

A [CLOWarden]-managed YAML file (e.g., `access_config.yaml`) that contains:

- GitHub teams
- Team maintainers and members
- Mapping of teams to repositories
- The roles assigned to each team in each repository (`admin`, `maintain`, `write`, `read`, etc.)

This file is the authoritative, machine-readable definition of repository maintainers.

### 2. GitHub API Data<!-- omit in toc -->

Unless the `--no-fetch` option is specified, it retrieves GitHub profile fields for each maintainer:

- Name
- Email
- Company

The GitHub username is taken from the CLOWarden configuration file.

### 3. Maintainer Configuration Files<!-- omit in toc -->

The `maintainer_config.yaml` files control the contents of the `MAINTAINERS.md` file outside of the maintainer table. The data in the files include:

- `before_text` — templated markdown inserted above the maintainer table
- `after_text` — templated markdown inserted below the table
- Organizational and repository-level variables (e.g., organization name, governance repo, repo name)
- Optional `project_map` allowing automatic project assignment based on repo-name patterns

The markdown templating supports:

- `{var}` substitutions
- Default values: `{var:DefaultValue}`
- Simple conditionals:

```info
  {{ if project }}
     This repo is part of {project}.
  {{ else }}
     This repo is unassigned.
  {{ endif }}
```

The directive `extends` allows a repository to inherit configuration from another `maintainer_config.yaml` file, enabling overrides of specific sections while retaining the rest. This allows for consistent organizational policies with per-repo or per-project customizations.

Typically, organizations manage a single `maintainer_config.yaml` in the governance repo alongside the CLOWarden access config.

## Deploying the Maintainer List Generator

The generator may be used:

- **Locally**, by running the script to generate the up-to-date `MAINTAINERS.md` file and manually opening a PR (see [Running the Generator Locally](#running-the-generator-locally)).
- **Per-repository**, via a GitHub Action that runs the generator periodically and opens a PR when the `MAINTAINERS.md` file changes (see [Per-Repository Workflow](#per-repository-workflow)).
- **Centrally** (**recommended**), where a single organizational workflow maintains all repositories' `MAINTAINERS.md` files (see [Centralized Organizational Workflow (recommended)](#centralized-organizational-workflow-recommended))

Note that even if the centralized approach is used, individual repositories may still provide their own `maintainer_config.yaml` files to override specific settings (see [Project or Repository-Level Configuration](#project-or-repository-level-configuration)).

## Project or Repository-Level Configuration

A repository **may** provide a `maintainer_config.yaml` in its root directory.

This file may:

- Extend (`extends:`) the organization’s configuration
- Extend a project-specific configuration
- Completely replace the organization defaults

Using `extends:` allows a repo to override only specific sections (e.g., governance policies) while inheriting the rest.

## Running the Generator Locally

Example invocation:

```bash
python3 generate-maintainers.py \
  --repo acapy \
  --project "ACA-Py" \
  --config maintainer_config.yaml \
  --output MAINTAINERS.md
```

The `config` parameter be a local file name or the URL to a raw YAML file in a GitHub repository. To reference a raw GitHub file URL, add the query parameter `?raw=true` to the GitHub UI's URL for the file.

### Useful Options

| Option        | Meaning                                |
| ------------- | -------------------------------------- |
| `--no-fetch`  | Skip GitHub API lookups                |
| `--list-only` | Output only the maintainers table      |
| `--token`     | Use a GitHub token for profile lookups |
| `--output`    | Write to a file                        |

You can omit `--project` to see how the templates behave when the repository is not part of a project.

## GitHub Action Usage

Two deployment patterns are suggested.

### Per-Repository Workflow

Each repository includes `.github/workflows/update-maintainers.yml`.

The workflow:

- Checks out the repo
- Fetches the generator
- Loads the configuration
- Runs the generator
- Creates a PR if `MAINTAINERS.md` changed

See an example in `[repo_githubaction.yml](./repo_githubaction.yml)`.

### Centralized Organizational Workflow (recommended)

A single workflow in the governance repository:

1. Loads the [CLOWarden] file (e.g. `access_config.yaml`).
2. Iterates through all repositories listed in the file.
3. Uses the organizational `maintainer_config.yaml` file.
4. Uses the `project_map` in the organization `maintainer_config.yaml` file to automatically associate the repo to a project (if any).
5. Detects whether the repo has a local `maintainer_config.yaml`, using it in place of the organizational one.
6. Generates the new `MAINTAINERS.md`.
7. Creates a PR only if the contents of the file has changed.

See an example in `[org_githubaction.yml](./org_githubaction.yml)`.

This approach avoids maintaining per-repo GitHub Actions.

## Testing

Tests for this tool live in the `tests/` directory and use:

- `pytest`
- Snapshot testing
- Temporary fixture-based generation

To run all of the tests:

```bash
cd tests
pytest
```

If output changes legitimately, update snapshots:

```bash
pytest --snapshot-update
```

Commit the updated snapshots in your PR.

## Contributing

Contributions are welcome!

You can submit PRs for:

- New features
- Documentation improvements
- Test coverage
- Template refinements
- Additional GitHub Action examples

## License

Apache License 2.0