import logging
import json

import requests


class Github:
    def __init__(self, token: str, repo_owner: str, repo_name: str):
        self._token = token
        self._repo_owner = repo_owner
        self._repo_name = repo_name
        self._headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.v3+json"}
        self._issues_url = f"https://api.github.com/repos/{self._repo_owner}/{self._repo_name}/issues"

    def create_issue(self, title: str, body: str):
        """
        create issue if title not already exists in issues
        """
        existing_issues = self.get_existing_issues()
        if title in existing_issues:
            logging.warning(f"issue already exists: {title}")
            return

        payload = {"title": title, "body": body, "labels": ["bug", "bugfinder"]}
        response = requests.post(self._issues_url, headers=self._headers, data=json.dumps(payload))
        if response.status_code == 201:
            logging.info("Issue created successfully!")
            return response.json()
        else:
            logging.error(f"Failed to create issue. Response: {response.text}")
            raise RuntimeError(response.text)

    def get_existing_issues(self) -> set:
        """
        query repo for existing issue titles, return set with titles
        """
        response = requests.get(self._issues_url, headers=self._headers)
        issue_titles = set()
        if response.status_code == 200:
            issues = response.json()
            for issue in issues:
                issue_titles.add(issue["title"])
        else:
            logging.error(f"Failed to retrieve issues. Response: {response.text}")
            raise RuntimeError(response.text)
        return issue_titles


if __name__ == "__main__":
    import sys

    token = sys.argv[1]
    title = sys.argv[2]
    repo_owner = "mm4rks"
    repo_name = "dewolf"
    g = Github(token, repo_owner, repo_name)
    g.create_issue(title, "body")
