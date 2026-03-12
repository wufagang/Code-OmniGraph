from git import Repo
import re
from typing import List
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from cagr_common.models import Commit

class GitScraper:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.repo = Repo(self.repo_path)
        self.jira_regex = re.compile(r'[A-Z]+-\d+')

    def get_commits_with_jira(self) -> List[Commit]:
        commits = []
        for commit in self.repo.iter_commits('HEAD', max_count=1000):
            if self.jira_regex.search(commit.message):
                commits.append(Commit(
                    hash=commit.hexsha,
                    message=commit.message,
                    author=commit.author.name
                ))
        return commits
