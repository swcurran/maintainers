# Maintainers Generator

The Maintainers Generator is a Python tool for automatically generating and updating MAINTAINERS.md files across an organization’s repositories. It consumes centrally managed YAML configuration files (team memberships, repo roles, and governance text blocks) and produces accurate, consistent, human-readable maintainer documentation for each repository.

Many open-source foundations and multi-repository projects maintain their actual permissions and membership data in a machine-readable Governance Repository (e.g., GitHub teams, repo roles, admin/maintain/read privileges). However, humans need readable documentation in each repo. This tool automates that process and keeps MAINTAINERS.md files synchronized with organizational governance.

A generated MAINTAINERS.md file includes:
	•	Introductory text (configurable per organization/project/repo)
	•	A table of current maintainers with:
	•	GitHub ID
	•	Display name (via GitHub API)
	•	Email address (if available)
	•	Company affiliation (if available)
	•	Roles (admin/maintain/write/triage/read)
	•	Governance text after the table:
	•	Duties of maintainers
	•	How to update team membership
	•	How to become a maintainer
	•	How to remove maintainers
	•	And more, depending on config

The generator ensures the information is:
	•	Accurate – pulled from authoritative YAML configuration
	•	Consistent – identical formatting across all repos
	•	Auditable – changes appear as Pull Requests
	•	Customizable – overrides allowed at project and repo level

It is designed for foundations, large open-source projects, and multi-repo teams who want uniform governance documentation across many repositories.

⸻

Table of Contents 
	•	How It Works￼
	•	Configuration Layering￼
	•	Running the Generator Locally￼
	•	GitHub Action Integration￼
	•	Organization-Level Maintainers Configuration￼
	•	Snapshot Testing￼
	•	Contributing￼
	•	License￼

⸻

How It Works

The generator combines three inputs:

1. Governance Repository Configuration (Teams/Roles YAML)

Defines the truth for:
	•	Which GitHub teams exist
	•	Who is in each team
	•	Which teams have which roles (admin/maintain/write/triage/read) per repository
	•	Visibility and access control

This file is the authoritative source of permissions.

⸻

2. Organization-Level Maintainers Configuration

(usually maintainers-config.yaml in the Governance Repository)

Defines:
	•	The default before_text (appears before the maintainer table)
	•	The default after_text (appears after the table)
	•	Values for template substitutions:
	•	{organization}
	•	{gov_org}
	•	{yaml_link}
	•	{yaml_raw_link}
	•	The location of the Governance YAML file
	•	Optional generator defaults

⸻

3. Optional Project-Level and Repo-Level Overrides

Project-level config:
Used when a project needs custom text not suitable globally.

Repo-level config (.maintainers-config.yaml):
Allows per-repository customization without affecting the rest of the project.

⸻

The generator produces a complete MAINTAINERS.md file composed of:
	1.	Before-text block
	2.	Maintainers table
	3.	After-text block

A GitHub Action in each repository runs the generator on a schedule, creates updated output, and opens PRs whenever changes occur.

⸻

Configuration Layering

Configuration is merged in this order (highest precedence last):
	1.	Organization-level config
	2.	Project-level config (optional)
	3.	Repository-level config (.maintainers-config.yaml, optional)

Each layer may override:
	•	before_text
	•	after_text
	•	Organization or project name
	•	Governance repository name
	•	Governance YAML location
	•	Any variable used in template text

This enables:
	•	Global defaults
	•	Per-project customization
	•	Per-repo overrides

Most repositories typically rely entirely on the organization-level config.

⸻

Running the Generator Locally

To manually generate a MAINTAINERS.md file:

python3 generate-maintainers.py \
    --repo <repository-name> \
    --project "<human project name>" \
    --config <path-or-url-to-maintainers-config> \
    --output MAINTAINERS.md

Example:

python3 generate-maintainers.py \
    --repo acapy \
    --project "ACA-Py" \
    --config https://raw.githubusercontent.com/<org>/governance/main/maintainers-config.yaml \
    --output MAINTAINERS.md

Command-Line Options

Option	Description
--repo	Repository name as defined in governance YAML
--project	Human-readable project name
--config	Path or URL to maintainer config file
--output	Output filename (default: MAINTAINERS.md)
--no-fetch	Skip GitHub user lookups
--list-only	Output only the maintainers table
--token	GitHub token (optional, for authenticated API)


⸻

GitHub Action Integration

The generator is typically run automatically once per week in each repository.

Repositories define the following environment variables:

PROJECT

Human-readable project name (e.g., “ACA-Py”, “Askar”, “Credo”).

Set either as:
	•	An Actions variable,
	•	A workflow variable,
	•	Or hard-coded into the workflow.

REPO

Repository name. Often:

github.event.repository.name

GENERATOR_CONFIG

URL to the organization-level maintainers config, e.g.:

https://github.com/<org>/governance/blob/main/maintainers-config.yaml

GENERATOR_SCRIPT_URL

URL to the raw generate-maintainers.py script.

⸻

Workflow Behavior
	1.	Fail if PROJECT is missing.
	2.	Download the generator script.
	3.	Determine which config file to use:
	•	Repo-level .maintainers-config.yaml if present
	•	Otherwise, GENERATOR_CONFIG
	4.	Run the generator.
	5.	If MAINTAINERS.md changed → create a Pull Request.

A reusable template workflow is included in this repository as:
TEMPLATE_GITHUB_ACTION.yml.

⸻

Organization-Level Maintainers Configuration

Many organizations use a Governance Repository to define:
	•	Teams
	•	Group membership
	•	Repository access rules
	•	Governance processes

The Maintainers Generator consumes an organization-level config file, usually:

governance/maintainers-config.yaml

What Should Be Included?
	•	Complete before_text
	•	Complete after_text
	•	{organization} (human name)
	•	{gov_org} (governance repository name)
	•	{yaml_link} (UI URL to governance YAML)
	•	{yaml_raw_link} (raw GitHub URL)
	•	Any default variables used in templates

How Repository Workflows Use It

Repositories reference this file in their workflow:

GENERATOR_CONFIG: "https://github.com/<org>/governance/blob/main/maintainers-config.yaml"

Overrides may be applied through project or repo-level configs.

Typical Organization Workflow
	1.	Update team membership in the Governance Repository.
	2.	Submit a PR and obtain approvals from maintainers.
	3.	Merge changes.
	4.	Scheduled workflows in affected repos regenerate MAINTAINERS.md.
	5.	PRs appear automatically wherever the list changed.

This keeps maintainer information synchronized across the entire organization.

⸻

Snapshot Testing

This repository includes comprehensive snapshot testing using pytest-snapshot.

Snapshot tests validate:
	•	Output formatting
	•	Config layering
	•	Template substitution
	•	Governance parsing
	•	Maintainer table generation

Run Tests

Activate your venv and run:

pytest

Updating Snapshots

If your code intentionally changes output, update snapshots:

pytest --snapshot-update

Review updated snapshot files under:

tests/snapshots/

Commit these changes along with your code.

Snapshot testing ensures consistent, auditable file generation across versions.

⸻

Contributing

Contributions are welcome!

You can contribute by:
	•	Filing issues
	•	Proposing enhancements
	•	Improving tests
	•	Maintaining or updating templates
	•	Adding support for additional configuration options

Standard PR workflow:
	1.	Fork the repo
	2.	Create a feature branch
	3.	Make changes
	4.	Run tests (and update snapshots if needed)
	5.	Submit a pull request

PRs are reviewed by maintainers before merging.

⸻

License

This project is licensed under the Apache License 2.0.
See the LICENSE￼ file for details.

⸻

If you want, I can also generate:
	•	A matching CONTRIBUTING.md
	•	A Makefile to simplify local testing
	•	Documentation for config file schemas
	•	A “Quick Start Guide” for first-time users