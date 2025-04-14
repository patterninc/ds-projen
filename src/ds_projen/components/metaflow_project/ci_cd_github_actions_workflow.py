from 

example_github_actions_workflow = YamlFile(
    scope=self,
    file_path=f".github/workflows/ci-cd--{self.name}.yml",
    obj={
        "name": "CI",
        "on": {"push": {"branches": ["main"]}},
        "jobs": {
            "build": {
                "runs-on": "ubuntu-latest",
                "steps": [
                    {"name": "Checkout", "uses": "actions/checkout@v2"},
                    {
                        "name": "Set up Python",
                        "uses": "actions/setup-python@v2",
                        "with": {"python-version": "3.12"},
                    },
                    {
                        "name": "Install dependencies",
                        "workdir": str(self.outdir),
                        "run": "pip install -r requirements.txt",
                    },
                    {
                        "name": "Run tests",
                        "run": "pytest",
                    },
                ],
            }
        },
    },
)
