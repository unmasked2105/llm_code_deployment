from typing import List, Tuple, Dict

try:
    from github import Github
except ImportError:
    # Defer raising until the functions that need PyGithub are called.
    Github = None


def create_repo_and_commit(token: str, repo_name: str, files: List[Tuple[str, str]]) -> Dict[str, str]:

    if Github is None:
        raise RuntimeError("PyGithub is not installed. Install with 'pip install PyGithub' or include it in requirements.txt")

    gh = Github(token)
    user = gh.get_user()
    repo = user.create_repo(name=repo_name, private=True, auto_init=False)

    base_message = "Initial commit (generated)"
    for path, content in files:
        repo.create_file(path=path, message=base_message, content=content, branch="main")

    return {
        "clone_url": repo.clone_url,
        "html_url": repo.html_url,
        "full_name": repo.full_name,
    }

def create_issue(token: str, full_name: str, title: str, body: str | None = None) -> str:

    if Github is None:
        raise RuntimeError("PyGithub is not installed. Install with 'pip install PyGithub' or include it in requirements.txt")

    gh = Github(token)
    repo = gh.get_repo(full_name)
    issue = repo.create_issue(title=title, body=body or "")
    return issue.html_url


