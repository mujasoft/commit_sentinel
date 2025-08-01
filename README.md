# Commit Sentinel
![Python](https://img.shields.io/badge/python-3.8+-blue)
![License](https://img.shields.io/github/license/mujasoft/git_log_analyser)
![Status](https://img.shields.io/badge/status-WIP-orange)
![Demo Available](https://img.shields.io/badge/demo-available-green)

A CLI tool that uses AI to score and summarize the latest Git commit before submission.


## Why This Exists

Code changes move fast. Commits come in quickly and often introduce unintentional risk. This tool helps assess the risk of the **latest commit (HEAD)** before it gets merged.

- Configure once — no need to modify the code
- Simple CLI interface, CI/CD-ready
- Unix style design

## How It Works

This tool:
1. Connects to any Git repository
2. Obtains head commit
3. Uses local LLM (via **llama3**) to perform risk assessment

## Demo
[Watch Demo (2m)](./demo.mov)


## Limitations
- Currently only analyzes the **HEAD** of your feature branch.
- Large diffs may exceed the LLM’s token limit and result in truncated prompts — a warning will be printed in such cases.
- If the full diff doesn't fit, the LLM's response may be less accurate due to missing context.

## Configuration

All runtime settings live in a single file: `settings.toml`

```toml
[default]

ollama_url = "http://localhost:11434/api/generate"
model_name = "llama3"
branch = "main"
git_repo_dir = "~/Desktop/development/vscode"
output = "head_commit_analysis.txt"
```

> Helpful for deployment in pipelines. Settings can also be overwritten by CLI flags anytime.

## Usage

### 1. Start your local LLM
```bash
ollama run llama3
# You can also use mistral, but keep in mind it has a smaller context window than llama3.
```

### 2. Configure your settings
```bash
vim settings.toml
```

### 3. Run the tool
```bash
python3 commit_sentinel.py
```

## Sample Output

```text
Commit Analysis:
---------------
ID: c41721940bd3bf510f76e1770c75efcc8e2d3cda
Summary: This commit updates the `CommandLineAutoApprover` to use a new configuration setting for matching command lines against allow patterns, and makes some minor fixes.

Risk Factors:

* The changes affect how the `CommandLineAutoApprover` handles matching command lines against allow patterns.
* There is a potential risk of unexpected behavior if the new configuration setting is not properly updated or tested.
* Some tests were added to ensure the correctness of the changes, but it's always good to double-check.

Risk Score: 6 (Medium)

Review Recommendation: Required

The commit makes some significant changes to the `CommandLineAutoApprover` and its testing infrastructure. While the changes are relatively minor, they do affect how the component handles command line matching, which is an important functionality. As such, I recommend that this commit be reviewed manually before merging to ensure that the changes are correct and properly tested.
```

## Prompt Customization

The prompt was left hardcoded for simplicity. However, if you would like to change the prompt, it can be done so in **commit_sentinel.py**.

## Requirements

- Python 3.8+
- [`dynaconf`](https://www.dynaconf.com/)
- [`typer`](https://typer.tiangolo.com/)
- [`requests`](https://docs.python-requests.org/en/master/)
- [`GitPython`](https://gitpython.readthedocs.io/en/stable/)
- [`ollama`](https://ollama.com) (optional but recommended for local LLM inference)

---

## TODO
- add an option to check a certain commit.
- add unit test(s)
- add a check to see if ollama+mistral is running and if they are not, perform a sys.exit()

## License

MIT License — see [LICENSE](./LICENSE)

---

## Author

**Mujaheed Khan**
DevOps | Python | Automation | CI/CD
GitHub: [github.com/mujasoft](https://github.com/mujasoft)
