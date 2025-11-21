# Test Suite Overview

This directory contains a complete test harness for validating the generate-maintainers.py script. It uses:

- pytest — the test runner
- pytest-snapshot — snapshot testing of generated MAINTAINERS.md output
- Synthetic test configurations to simulate org, project, and repo inheritance
- A synthetic governance access_config.yaml for stable, offline testing

These tests verify that:

1. Configuration inheritance (extends:) works correctly
2. Org → Project → Repo overrides behave as expected
3. The output MAINTAINERS.md content is stable
4. Snapshot content changes are intentional
5. The script gracefully handles missing repos or configs
This ensures that future changes to the generator don’t accidentally break the output.

## Directory Structure

```bash
tests/
  data/
    access_config.yaml           # Synthetic test governance teams/roles config
  org/
    maintainer_config.yaml       # Full org-level default config
  project/
    maintainer_config.yaml       # Project-level override
  repo/
    maintainer_config.yaml       # Repo-level override
  listonly/
    maintainer_config.yaml       # Bare config for --list-only mode
  errors/
    missing_config.yaml          # Used for error-handling tests

  conftest.py                    # pytest fixtures
  helpers.py                     # Helper function to run generator
  test_generator.py              # Main test suite
  snapshots/
    test_generator/
      repo.md
      project.md
      org.md
      list_only.md               # Auto-generated snapshot outputs
```

The `snapshots/` folder is automatically created and managed by `pytest-snapshot`.

## Running Tests Locally

Tests should always be run inside a Python virtual environment. This ensures consistent dependency versions and avoids conflicts with your system Python.

1. Create and activate a virtual environment

Linux/macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

Windows (PowerShell):

```powershell
python -m venv venv
venv\Scripts\activate
```

You should see (venv) in your prompt once it’s activated.

2. Install development dependencies

`pip install -r requirements-dev.txt`

This installs the necessary packages listed in `requirements-dev.txt`.

3. Run the test suite

`pytest`

All tests should pass by comparing the existing snapshots with the current generator output.

## Updating Snapshots

Snapshot files capture the expected output of the generator. If you intentionally change the generator’s behavior (for example, changing BEFORE/AFTER text templates or the layout of the table), you must update the snapshots.

After verifying the changes to the test outputs, update the snapshots by running:

`pytest --snapshot-update`

This regenerates the snapshot files under:

tests/snapshots/test_generator/
  repo.md
  project.md
  org.md
  list_only.md

Always review the diffs of snapshot files and then commit them.

## Snapshot Test Behavior

- On the first run, snapshot tests will create snapshot files and then report that the snapshot directory was modified. This is a reminder to inspect and commit the new snapshots.
- On subsequent runs, the generated output is compared byte-for-byte against the stored snapshot.
- If the output changes unexpectedly, the test will fail until you either:
- Fix the regression, or
- Intentionally update the snapshots with pytest --snapshot-update.

This helps ensure that any change to the generated MAINTAINERS.md is deliberate and reviewed.

## Error-Handling Tests

The errors/ directory contains configurations used to test that the generator handles invalid situations correctly, such as:

- Referencing a repository that does not exist in the governance YAML
- Using incomplete or incorrect configuration

Tests in test_generator.py verify that these cases result in clear, meaningful error messages rather than crashes or silent failures.

## How the Test Harness Works

The helper function in helpers.py executes the generator script as a subprocess, roughly equivalent to:

python generate-maintainers.py --repo <name> --project <name> --config <path> --no-fetch

Key points:

- `--no-fetch` is always used during tests so that the script does not call out to external services (e.g., GitHub APIs).
- All input data comes from the synthetic `access_config.yaml` in the `./data` folder, and the scenario-specific maintainer_config.yaml files under tests/.
- The script’s stdout is captured and compared to the stored snapshot content.

## Contributor Workflow

Before submitting a pull request that touches generate-maintainers.py or its configuration:
1. Create and activate a virtual environment.
2. Install dev dependencies with `pip install -r requirements-dev.txt`.
3. Run the tests:

`pytest`

4. If your changes intentionally modify the generated output:

   - Run `pytest --snapshot-update`.
   - Review the updated snapshot files under `tests/snapshots/test_generator/`.
   - Commit both your code changes and the updated snapshot files.

5. Push your branch and open a pull request.

Pull requests that change generator output but do not update snapshots will cause CI failures.

### Tips

- Use `pytest -vv` for more verbose output and clearer diffs when tests fail.
- If a snapshot diff looks suspicious, regenerate that snapshot only after confirming the change is expected.
- The test suite does not rely on network access, so failures are typically due to logic or formatting changes rather than environment issues.

### Need Help?

If you’re unsure how to interpret a snapshot failure or how to update the tests for a new feature, feel free to:

- Open an issue in the repository, or
- Ask in the project’s discussion channels (if available).

We’re happy to help contributors understand and extend the test suite.
