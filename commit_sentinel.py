# MIT License

# Copyright (c) 2025 Mujaheed Khan

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from datetime import datetime
from git import NULL_TREE, Repo
import os
import requests
import typer

from dynaconf import Dynaconf

# Load typer
app = typer.Typer(
    help="Analyse HEAD commit and assess risk using a LLM."
)

# Load config
settings = Dynaconf(
    settings_files=["settings.toml"],
    environments=True,
    default_env="default",
)


def get_head_commit_info(branch: str, git_repo_dir: str):
    """Fetch the HEAD commit on the specified branch and extract metadata."""
    repo = Repo(git_repo_dir)
    commit = repo.head.commit
    parent = commit.parents[0] if commit.parents else NULL_TREE
    diffs = commit.diff(parent, create_patch=True)

    diff_text = "\n".join(d.diff.decode("utf-8", errors="ignore") for d in diffs)
    stats = commit.stats.total
    ts_epoch = commit.committed_date
    ts = datetime.fromtimestamp(ts_epoch).strftime('%Y-%m-%d %H:%M:%S')

    return {
        "hexsha": commit.hexsha,
        "author": commit.author.name,
        "msg": commit.message,
        "committed_date": ts,
        "diff": diff_text,
        "statistics": stats,
        "files": list(commit.stats.files.keys())
    }


def ask_question(commit: dict, ollama_url: str, model_name: str) -> str:
    commit_str = str(commit)
    full_prompt = f"""
You are a senior DevOps engineer reviewing a code submission before it is merged.

Here is the commit information:
{commit_str}

Please analyze this commit and provide the following:
1. A short, human-readable summary of what was changed.
2. Highlight any risky or sensitive changes (e.g., auth, deletion, major refactor).
3. Assign a risk score from 1 (low) to 10 (high) based on the magnitude and sensitivity of the changes.
4. Recommend whether this commit should be reviewed manually before merging.

Respond in the following format:

Commit Analysis:
---------------
ID: {commit['hexsha']}
Summary: <summary>
Risk Factors: <bullet list or 'None'>
Risk Score: <1–10>
Review Recommendation: <Required / Optional / Not Needed>
"""

    payload = {
        "model": model_name,
        "prompt": full_prompt,
        "stream": False
    }

    response = requests.post(ollama_url, json=payload)

    limits = {"llama3": 8000, "mistral": 4000}
    if len(full_prompt) // 4 > limits.get(model_name, 4000):
        print("*** Warning: Truncated prompt detected."
              " Not all data was included. ***")

    return response.json().get("response", "[No response]")


@app.command()
def analyse(
    branch: str = typer.Option(settings.branch, "--branch", "-b",
                               help="Name of branch."),
    git_repo_dir: str = typer.Option(settings.git_repo_dir, "--git-repo_dir", 
                                     "-g", help="Repo directory."),
    model_name: str = typer.Option(settings.model_name, "--model", "-m",
                                   help="Model name."),
    output: str = typer.Option(settings.output, "--output", "-o",
                               help="Output file (e.g. result.txt)"),
    ollama_url: str = typer.Option(settings.ollama_url, "--ollama-url", "-l",
                                   help="URL of the local LLM server.")
):
    """Analyze the latest commit and output LLM assessment."""
    head_commit = get_head_commit_info(branch, git_repo_dir)
    answer = ask_question(head_commit, ollama_url, model_name)

    print(f"\n{answer.strip()}\n")

    # Ensure valid output filename
    if not output.endswith(".txt"):
        output = os.path.join(output, "llm_commit_analysis.txt")

    with open(output, "w") as f:
        f.write(answer)


if __name__ == "__main__":
    app()
