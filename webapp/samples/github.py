import json
import logging

import requests


class Github:
    QUERY_LABELS = "bugfinder"  # comma separated string, e.g., bug,ui,@high
    CREATION_LABELS = ["bug", "bugfinder"]

    def __init__(self, token: str, repo_owner: str, repo_name: str):
        self._token = token
        self._repo_owner = repo_owner
        self._repo_name = repo_name
        self._headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.v3+json"}
        self._issues_url = f"https://api.github.com/repos/{self._repo_owner}/{self._repo_name}/issues"

    def iter_existing_issues(self):
        """iterate through existing issues"""
        response = requests.get(self._issues_url, headers=self._headers, params={"state": "all", "labels": self.QUERY_LABELS})
        if response.status_code == 200:
            for issue in response.json():
                yield issue
        else:
            logging.error(f"Failed to retrieve issues. Response: {response.text}")
            raise RuntimeError(f"GitHub Issues: {response.text}")

    @property
    def existing_issue_titles_to_issue_map(self) -> dict:
        """Iterate existing issues and return set of titles (str)"""
        return {issue["title"]: issue for issue in self.iter_existing_issues()}

    def create_issue(self, title: str, body: str):
        """create issue if title not already exists in issues"""
        existing_issues = self.existing_issue_titles_to_issue_map
        if title in existing_issues:
            logging.warning(f"issue already exists: {title}")
            return existing_issues[title]
        payload = {"title": title, "body": body, "labels": self.CREATION_LABELS}
        response = requests.post(self._issues_url, headers=self._headers, data=json.dumps(payload))
        if response.status_code == 201:
            logging.info("Issue created successfully!")
            return response.json()
        else:
            logging.warning(f"Failed to create issue. Response: {response.text}")
