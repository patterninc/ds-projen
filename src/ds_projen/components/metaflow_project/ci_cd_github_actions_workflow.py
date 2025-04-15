"""CI-CD.

| Trigger           | Lint/Test? (CI) | Auto Deploy? | Environment                                                          |
| ----------------- | --------------- | ------------ | -------------------------------------------------------------------- |
| PR (open/sync)    | ✅ Yes           | ❌ No         | But you can use `workflow_dispatch` to deploy to `dev`                                                                |
| Merge to main     | ✅ Yes           | ✅ Yes        | `prod`                                                                 |
| Workflow dispatch | ❌ No            | ✅ Yes        | choice: `main` => `dev` or `prod`; `!main` => `dev` |

| Trigger        | Branch  | Outerbounds User             | Perimeter |
| -------------- | ------- | ---------------------------- | --------- |
| PR (open/sync) | `!main` | `data-science-projects-dev`  | `default` |
| Merge to main  | `main`  | `data-science-projects-prod` | `prod`    |
| Workflow dispatch | any  | depends                      | depends   |
"""

from textwrap import dedent
from typing import TYPE_CHECKING

from projen import Component, YamlFile

if TYPE_CHECKING:
    from ds_projen.components.metaflow_project.metaflow_project import MetaflowProject


PROD_OUTERBOUNDS_USERNAME = "data-science-projects-prod"
DEV_OUTERBOUNDS_USERNAME = "data-science-projects-dev"
PROD_PERIMETER = "prod"
DEFAULT_PERIMETER = "default"
PACKAGE_SUFFIXES: str = ",".join(
    [
        ".csv",
        ".sql",
        ".json",
    ]
)


class MetaflowProjectCiCdGitHubActionsWorkflow(Component):
    """GitHub Actions CI/CD workflow for a Metaflow project."""

    def __init__(self, metaflow_project: "MetaflowProject") -> None:
        """Initialize the GitHub Actions workflow component."""
        super().__init__(metaflow_project.repo)
        self.metaflow_project = metaflow_project
        self.working_directory = str(self.metaflow_project.outdir)

        # Create the workflow file
        self._create_workflow_file()

    def _create_workflow_file(self) -> None:
        """Create the CI/CD workflow file for the Metaflow project."""
        workflow_name = f"ci-cd--{self.metaflow_project.domain}--{self.metaflow_project.name}.yml"

        # Define the workflow content as a dictionary
        workflow_content = {
            "name": f"{self.metaflow_project.domain}/{self.metaflow_project.name} (CI/CD)",
            "on": {
                "push": {
                    "branches": ["main"],
                    "paths": [f"{self.working_directory}/**", f".github/workflows/{workflow_name}"],
                },
                "pull_request": {
                    "types": ["opened", "synchronize"],
                    "paths": [f"{self.working_directory}/**", f".github/workflows/{workflow_name}"],
                },
                "workflow_dispatch": {
                    "inputs": {
                        "environment": {
                            "description": "prod: main only; dev: all branches",
                            "required": True,
                            "type": "choice",
                            "options": ["dev", "prod"],
                        }
                    }
                },
            },
            "jobs": {
                "lint": self._get_lint_job(),
                "test": self._get_test_job(),
            },
        }

        # Add auto-deploy jobs for each flow
        for flow in self.metaflow_project.flows:
            job_id_suffix = flow.flow_path.name.replace(".", "_")
            workflow_content["jobs"][f"auto-deploy--{job_id_suffix}"] = self._get_auto_deploy_job(
                job_id_suffix=job_id_suffix,
                flow_file_name=flow.flow_path.name,
            )

        # Add manual-deploy job that deploys all flows
        workflow_content["jobs"]["manual-deploy"] = self._get_manual_deploy_job()

        # Create the workflow file using YamlFile
        YamlFile(
            scope=self,
            file_path=f".github/workflows/{workflow_name}",
            obj=workflow_content,
            marker=True,
        )

    def _get_lint_job(self) -> dict:
        """Get the lint job configuration."""
        return {
            "name": "Run Linter (pre-commit)",
            "if": "github.event_name != 'workflow_dispatch'",
            "runs-on": "ubuntu-latest",
            "defaults": {"run": {"working-directory": self.working_directory}},
            "steps": [
                {"uses": "actions/checkout@v4"},
                {
                    "name": "Set up uv",
                    "uses": "astral-sh/setup-uv@v5",
                    "with": {
                        "enable-cache": True,
                        "cache-dependency-glob": f"${{{{ github.workspace }}}}/{self.working_directory}/uv.lock",
                    },
                },
                {"name": "Run pre-commit", "run": f"uv run pre-commit run --files {self.working_directory}/**"},
            ],
        }

    def _get_test_job(self) -> dict:
        """Get the test job configuration."""
        return {
            "name": "Run tests",
            "if": "github.event_name != 'workflow_dispatch'",
            "runs-on": "ubuntu-latest",
            "defaults": {"run": {"working-directory": self.working_directory}},
            "steps": [
                {"uses": "actions/checkout@v4"},
                {
                    "name": "Set up uv",
                    "uses": "astral-sh/setup-uv@v5",
                    "with": {
                        "enable-cache": True,
                        "cache-dependency-glob": f"${{{{ github.workspace }}}}/{self.working_directory}/uv.lock",
                    },
                },
                {"name": "Run pytest", "run": "uv run pytest tests/"},
            ],
        }

    def _get_auto_deploy_job(self, job_id_suffix: str, flow_file_name: str) -> dict:
        """Get the auto-deploy job configuration for a specific flow."""
        return {
            "name": f"Auto-deploy {job_id_suffix} to prod (on merge to main)",
            "if": "github.event_name == 'push' && github.ref == 'refs/heads/main'",
            "needs": ["lint", "test"],
            "runs-on": "ubuntu-latest",
            "defaults": {"run": {"working-directory": self.working_directory}},
            "permissions": {"contents": "read", "id-token": "write"},
            "steps": [
                {"uses": "actions/checkout@v4"},
                {"name": "Set up uv", "uses": "astral-sh/setup-uv@v5"},
                {
                    "name": "Configure Outerbounds Auth",
                    "run": dedent(f"""\
                            uvx outerbounds service-principal-configure \\
                            --name {PROD_OUTERBOUNDS_USERNAME} \\
                            --deployment-domain pattern.obp.outerbounds.com \\
                            --perimeter {PROD_PERIMETER} \\
                            --github-actions"""),
                },
                {
                    "name": "Deploy Prod Flow",
                    "run": dedent(f"""\
                            uv run src/{flow_file_name} \\
                            --config ./configs/prod.json \\
                            --environment=fast-bakery \\
                            --package-suffixes='{PACKAGE_SUFFIXES}' \\
                            --production \\
                            argo-workflows create"""),
                },
            ],
        }

    def _get_manual_deploy_job(self) -> dict:
        """Get the manual-deploy job configuration that deploys all flows."""
        steps = [
            {"uses": "actions/checkout@v4"},
            {"name": "Set up uv", "uses": "astral-sh/setup-uv@v5"},
            {
                "name": "Configure Outerbounds Auth",
                "run": dedent(f"""\
                        USER_NAME="{DEV_OUTERBOUNDS_USERNAME}"
                        PERIMETER="{DEFAULT_PERIMETER}"
                        if [[ "${{{{ github.event.inputs.environment }}}}" == "prod" ]]; then
                          USER_NAME="{PROD_OUTERBOUNDS_USERNAME}"
                          PERIMETER="{PROD_PERIMETER}"
                        fi

                        uvx outerbounds service-principal-configure \\
                          --name $USER_NAME \\
                          --deployment-domain pattern.obp.outerbounds.com \\
                          --perimeter $PERIMETER \\
                          --github-actions"""),
            },
        ]

        # Add a deploy step for each flow
        for flow in self.metaflow_project.flows:
            flow_name = flow.flow_path.name
            steps.append(
                {
                    "name": f"Deploy {flow_name}",
                    "run": dedent(f"""\
                        if [[ "${{{{ github.event.inputs.environment }}}}" == "prod" ]]; then
                          uv run src/{flow_name} \\
                            --config ./configs/prod.json \\
                            --environment=fast-bakery \\
                            --package-suffixes='{PACKAGE_SUFFIXES}' \\
                            --production \\
                            argo-workflows create
                        else
                          uv run src/{flow_name} \\
                            --environment=fast-bakery \\
                            --package-suffixes='{PACKAGE_SUFFIXES}' \\
                            run \\
                            --tag manual-trigger
                        fi"""),
                }
            )

        return {
            "name": "Manual Deploy All Flows (Dev or Prod)",
            "if": "github.event_name == 'workflow_dispatch'",
            "runs-on": "ubuntu-latest",
            "defaults": {"run": {"working-directory": self.working_directory}},
            "permissions": {"contents": "read", "id-token": "write"},
            "steps": steps,
        }
