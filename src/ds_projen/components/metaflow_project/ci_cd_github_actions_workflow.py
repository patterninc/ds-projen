"""CI-CD.

CI: runs when (a) PR-opened and (b) new code pushed
- lint (run pre-commit)
- test (run pytest)
- backtesting?

CD:
- main can deploy to Prod or Staging
- feature branches can deploy to Staging
- main is auto-deployed to Prod on new code pushed, e.g. post merge
- Staging can be manually cleaned up on workflow dispatch

- deploy to outerbounds
    - to `default` perimeter with `data-science-projects-dev` outerbounds user if
        - branch != main
        - OR if environment == dev and workflow_dispatch is triggered
    - to `prod` perimeter with `data-science-projects-prod` outerbounds user if
        - branch == main
        - AND environment == prod and workflow_dispatch is triggered

Options:
- on merge to main, automatically deploy the latest dag version
- OR manually trigger the deployment of the flow (via workflow dispatch)
"""

from textwrap import dedent
from typing import TYPE_CHECKING

from projen import Component, YamlFile

if TYPE_CHECKING:
    from ds_projen.components.metaflow_project.metaflow_project import MetaflowProject

# Constants for Outerbounds usernames
PROD_OUTERBOUNDS_USERNAME = "data-science-projects-prod"
DEV_OUTERBOUNDS_USERNAME = "data-science-projects-dev"

# Constants for Outerbounds perimeters
PROD_PERIMETER = "prod"
DEFAULT_PERIMETER = "default"


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
                "push": {"branches": ["main"]},
                "pull_request": {"types": ["opened", "synchronize"]},
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
            flow_id = flow.flow_path.name.replace(".", "_")
            workflow_content["jobs"][f"auto-deploy-{flow_id}"] = self._get_auto_deploy_job(
                flow_id=flow_id,
                flow_fname=flow.flow_path.name,
            )

        # Add manual-deploy job that deploys all flows
        workflow_content["jobs"]["manual-deploy"] = self._get_manual_deploy_job()

        # Create the workflow file using YamlFile
        YamlFile(
            scope=self,
            file_path=f".github/workflows/{workflow_name}",
            obj=workflow_content,
            marker=False,  # No marker comment at the top
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
            "name": "Run Tests (pytest)",
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

    def _get_auto_deploy_job(self, flow_id: str, flow_fname: str) -> dict:
        """Get the auto-deploy job configuration for a specific flow."""
        return {
            "name": f"Auto-deploy {flow_id} to prod (on merge to main)",
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
                            uv run src/{flow_fname} \\
                            --config ./configs/prod.json \\
                            --environment=fast-bakery \\
                            --package-suffixes='.csv' \\
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
        for i, flow in enumerate(self.metaflow_project.flows):
            flow_name = flow.flow_path.name
            steps.append(
                {
                    "name": f"Deploy {flow_name}",
                    "run": dedent(f"""\
                        if [[ "${{{{ github.event.inputs.environment }}}}" == "prod" ]]; then
                          uv run src/{flow_name} \\
                            --config ./configs/prod.json \\
                            --environment=fast-bakery \\
                            --package-suffixes='.csv' \\
                            --production \\
                            argo-workflows create
                        else
                          uv run src/{flow_name} \\
                            --environment=fast-bakery \\
                            --package-suffixes='.csv' \\
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
