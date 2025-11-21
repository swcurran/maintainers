# Maintainers Generator

This repository contains the Maintainers Generator, a Python tool for automatically creating and updating MAINTAINERS.md files across an organization’s repositories based on centralized governance and configuration files.

In many organizations, maintainer information is controlled in a central Governance Repository that specifies teams, roles, and repository permissions in a machine-readable (YAML) format. Humans want to see a list of the maintainers and their roles at a per repository level in a MAINTAINER.md file. But, we don't want to have to manually keep the human consumable MAINTAINERS.md files up to date with the Governance Repository. The **Maintainers Generator** leverages the centralized data to produce consistent and accurate maintainer listings in each repository of each project within an organization.

A MAINTAINERS.md file includes not only the list of maintainers, but also governance information such as how to become a maintainer, the duties of a maintainer, and how to update team membership. This information is also centrally managed and propagated to each repository -- but is also customizable at the project and repository levels.

The **Maintainers Generator** is designed for organizations that have centralized their maintainer information in a machine-readable form across many repositories but also want that information provided in a human-readable maintainer file in each repository that is:

- Accurate
- Consistent
- Auditable through Pull Requests

Typical use cases include foundations, large open-source projects, and multi-repo community ecosystems.

## Table of Contents<!-- omit in toc -->

- [Maintainers Generator](#maintainers-generator)
  - [How It Works](#how-it-works)
  - [Configuration Layering](#configuration-layering)
  - [Running the Generator Locally](#running-the-generator-locally)
  - [GitHub Action Integration](#github-action-integration)
  - [Organization-Level Maintainers Configuration](#organization-level-maintainers-configuration)
    - [What belongs in the organization-level config?](#what-belongs-in-the-organization-level-config)
    - [Where should it live?](#where-should-it-live)
    - [How repositories consume it](#how-repositories-consume-it)
    - [Typical workflow for organizations](#typical-workflow-for-organizations)
  - [Testing](#testing)
  - [Contributing](#contributing)
  - [License](#license)

## How It Works

The generator builds a complete MAINTAINERS.md file using:

1. Governance Repository machine-readable configuration (teams/roles YAML)
   - Defines GitHub teams and their members
   - Maps teams to repositories and roles (admin, maintain, write, triage, read)
   - Is the authoritative source of who can do what in each repository within the organization.

2. Organization-level Maintainers config (for example, maintainers-config.yaml)
   - Defines the policy text blocks to be used in the MAINTAINERS.md file around the list of maintainers:
     - before_text: Introductory text before the maintainers table
     - after_text: Governance and process information after the maintainers table
   - Contains human-readable values such as {organization} and {gov_org}
   - Holds links to the Governance Repository configuration such as {yaml_link}

3. Optional project-level config
   - Allows overriding organization defaults for a specific project -- for example, custom before/after text.

4. Optional repo-level config (.maintainers-config.yaml in the repo root)
   - Overrides project- and organization-level settings for a single repository -- for example, custom before/after text.

From these inputs, the generator produces the MAINTAINERS.md file with:

- An introductory “before” block of text
- A Maintainers Table (the “Current Maintainers” section) listing GitHub IDs, names, emails, companies, and roles
- A governance and process “after” block of text that can include:
  - Updating team membership
  - Duties of a maintainer
  - Becoming a maintainer
  - Removing maintainers

Each repository adds a GitHub Actions workflow that runs the generator on a schedule (for example, weekly) to keep the MAINTAINERS.md file up to date. When changes are detected, a Pull Request is opened automatically for review and merging.

## Configuration Layering

Configuration is applied in this order:

1. Repository-level config: .maintainers-config.yaml (highest precedence)
2. Project-level config: optional, referenced via “extends”
3. Organization-level config: maintainers-config.yaml in the Governance Repository

Each layer can override:

- Governance YAML source
- before_text
- after_text
- {organization}
- {gov_org}
- Other settings as needed

This layered model enables organization-wide defaults with project- and repo-level customization where required.

In most cases, repositories only need to reference the organization-level config and do not require any repo-level config. The GitHubActions template included in this repository can be used with minimal changes to achieve this "out of the box" setup.

## Running the Generator Locally

You can run the generator locally for testing or manual updates.

Basic usage:

`python3 generate-maintainers.py --repo <repository-name> --project <project-name> --config <path-or-url-to-config> --output MAINTAINERS.md`

Example:

`python3 generate-maintainers.py --repo acapy --project "ACA-Py" --config https://raw.githubusercontent.com/<org>/governance/main/maintainers-config.yaml --output MAINTAINERS.md`

Command-line options:

`--repo`
  Name of the repository as it appears in the governance YAML.

`--project`
  Human-readable project name used in template substitution.

`--config`
  Path or URL to the maintainer configuration file.

`--output`
  File to write the generated Markdown to.

`--no-fetch`
  Skip GitHub API lookups for name, email, and company.

`--list-only`
  Output only the maintainer table.

`--token`
  GitHub token for authenticated API requests (optional).

## GitHub Action Integration

Most repositories use a GitHub Actions workflow to:

- Run the Maintainers Generator on a schedule
- Load the appropriate configuration
- Generate MAINTAINERS.md
- Create a Pull Request when changes occur

Typical environment variables:

PROJECT
  Logical project name for this repository (e.g., “ACA-Py”, “Askar”, “Credo”).
  Set via repository Actions Variables or hard-code in the workflow.

REPO
  The repository name, usually github.event.repository.name.

GENERATOR_CONFIG
  URL to the organization-level config (e.g., maintainers-config.yaml).

GENERATOR_SCRIPT_URL
  Raw GitHub URL for generate-maintainers.py.

Workflow logic usually:

1. Fail early if PROJECT is missing.
2. Checkout repository.
3. Install Python and dependencies.
4. Download the generator script.
5. If .maintainers-config.yaml exists, use it; otherwise use GENERATOR_CONFIG.
6. Run the generator and write MAINTAINERS.md.
7. Detect changes.
8. Create a Pull Request if needed.

A ready-to-copy workflow template is included in this repository as TEMPLATE_GITHUB_ACTION.yml.

---

## Organization-Level Maintainers Configuration

Many organizations maintain a Governance Repository that defines:

- GitHub teams
- Repository permissions
- Access control rules
- Governance policies

The Maintainers Generator integrates with this structure using an organization-level config file, commonly named:

maintainers-config.yaml

### What belongs in the organization-level config?

- Default “before” text block
- Default “after” text block
- Human-readable organization name ({organization})
- Governance Repository display name ({gov_org})
- URL to the team/role configuration ({yaml_link})
- Organization-wide generator defaults

### Where should it live?

Inside the Governance Repository, typically alongside the teams/roles YAML:

governance/access-control.yaml
governance/maintainers-config.yaml

### How repositories consume it

Repositories reference it in their workflow using GENERATOR_CONFIG, for example:

GENERATOR_CONFIG: "https://github.com/<org>/governance/blob/main/maintainers-config.yaml"

Configuration is loaded in this order:

1. Repository-level config
2. Project-level config
3. Organization-level config

Each level overrides the one before it.

### Typical workflow for organizations

1. Update team membership in access-control.yaml.
2. Open a Pull Request with the change.
3. Obtain approval from maintainers.
4. Merge the Pull Request.
5. Each affected repository regenerates MAINTAINERS.md automatically via its scheduled workflow.
6. A Pull Request is opened in each repository when its MAINTAINERS.md changes.

This ensures maintainers lists stay consistent across the organization.

---

## Testing

This repository includes a test harness in a maintainers/tests directory.

Tests validate:

- Config inheritance
- Template substitution
- Governance YAML parsing
- Maintainer table generation
- Override behavior

Run tests with:

./maintainers/tests/run-tests.sh

(Adjust path if needed.)

---

## Contributing

Contributions are welcome!

Ways to contribute:

- Open issues for bugs or feature requests
- Improve documentation or examples
- Enhance configuration inheritance
- Add test coverage
- Submit Pull Requests with fixes or features

Standard GitHub workflow applies:

1. Fork the repository
2. Create a branch
3. Make changes
4. Open a Pull Request

---

## License

This project is licensed under the Apache License 2.0.
See the [LICENSE](LICENSE) file for full details.
