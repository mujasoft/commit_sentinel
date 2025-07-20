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


import chromadb
from chromadb.config import Settings
from dynaconf import Dynaconf
import requests
from sentence_transformers import SentenceTransformer
from pprint import pprint
import typer
from git import Repo, NULL_TREE
from pprint import pformat
from datetime import datetime

# Load typer.
app = typer.Typer(
    help="Analyse git commits without having to read them manually.\n\n\
        This script has no CLI options. You are meant to fill out a\
            configuration file with the questions you want answered."
)

settings = Dynaconf(
    settings_files=["settings.toml"],
    environments=True,
    default_env="default",
)


def get_head_commit_info(branch: str, git_repo_dir: str):
    """Go to a repo, checkout a branch and return a list of n commits.

    Args:
        no_of_commits (int): No. of commits.
        branch (str): Name of git branch.
        git_repo_dir (str): location of git repo.

    Returns:
        list: list of dictionarys containing commit data with field such as:
               - hexsha
               - author
               - msg
               - commited_date
    """

    repo = Repo(git_repo_dir)

    commit = repo.head.commit
    parent = commit.parents[0] if commit.parents else NULL_TREE
    diffs = commit.diff(parent, create_patch=True)

    diff_text = "\n".join(d.diff.decode("utf-8", errors="ignore") for d in diffs)

    files_modified = list(commit.stats.files.keys())
    files_modified_str = "\n+".join(files_modified)

    stats = commit.stats.total

    # Join all diffs as text
    ts_epoch = commit.committed_date
    ts = datetime.fromtimestamp(ts_epoch).strftime('%Y-%m-%d %H:%M:%S')
    commit_dict = {
        "hexsha": commit.hexsha,
        "author": commit.author.name,
        "msg": commit.message,
        "committed_date": ts,
        "diff": diff_text,
        "statistics": stats
    }

    return commit_dict


def ask_question(commit: dict,
                 ollama_url: str,
                 model_name: str) -> str:

    commit_str = pformat(commit)
    # Construct full prompt for the LLM
    full_prompt = f"""You are a senior DevOps engineer reviewing a code submission before it is merged.
    Here is the commit information:
    {commit_str}
    Please analyze this commit and provide the following:
    1. A short, human-readable summary of what was changed.
    2. Highlight any risky or sensitive changes (e.g., auth, deletion, major refactor).
    3. Assign a risk score from 1 (low) to 10 (high) based on the magnitude and sensitivity of the changes.
    4. Recommend whether this commit should be reviewed manually before merging.
    Respond in the following format:
    ---
    Summary: <summary>
    Risk Factors: <bullet list or 'None'>
    Risk Score: <1–10>
    Review Recommendation: <Required / Optional / Not Needed>
    ---
    """

    #print(full_prompt)

    # Send request to local LLM server
    payload = {
        "model": model_name,
        "prompt": full_prompt,
        "stream": False
    }

    response = requests.post(ollama_url, json=payload)

    limits = {"llama3": 8000, "mistral": 4000}

    if len(full_prompt) // 4 > limits[model_name]:
        print("*** Warning: Truncated prompt detected."
              "Not all data was included.***")

    return response.json().get("response", "[No response]")


# CLI option was avoided on purpose as this tool is meant to be text driven.
# It is far too tedious to type our questions on comandline without some
# interactive output. The user is meant to write his/her/their questions
# in the settings.toml and run this script.
@app.command()
def analyse(branch: str = typer.Option(settings.branch,
                                       help="Name of branch."),
            git_repo_dir: str = typer.Option(settings.git_repo_dir,
                                             help="Repo direcotry."),
            model_name: str = typer.Option(settings.model_name,
                                           help="A helpful name for\
                                                collection."),
            ollama_url: str = typer.Option(settings.ollama_url,
                                           help="Location of \
                                            git repo.")):
    """Obtain head commit and analyse."""

    head_comit = get_head_commit_info(branch, git_repo_dir)
    answer = ask_question(head_comit,
                          ollama_url,
                          model_name
                          )
    print(f"{answer.strip()}\n")


if __name__ == "__main__":
    app()