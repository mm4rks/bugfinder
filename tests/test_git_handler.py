import os
import random
import string
import tempfile

import git
import pytest

from worker import GitHandler


@pytest.fixture
def git_repo_fixture():
    # Create a temporary directory for the local repository
    local_repo_dir = tempfile.mkdtemp()
    local_repo = git.Repo.init(local_repo_dir)
    create_commit(local_repo_dir, "initial commit")
    local_repo.create_head("main")  # Create 'main' branch
    local_repo.heads.main.checkout()

    # initial commit and create upstream repo
    remote_repo_dir = tempfile.mkdtemp()
    git.Repo.clone_from(local_repo_dir, remote_repo_dir)
    local_repo.create_remote("origin", remote_repo_dir) # add remote to local repo
    # Push 'main' branch to the remote and set it as the tracking branch
    local_repo.git.push('--set-upstream', 'origin', 'main')
    yield local_repo_dir, remote_repo_dir

    # Cleanup
    for repo_dir in [local_repo_dir, remote_repo_dir]:
        for root, dirs, files in os.walk(repo_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(repo_dir)


def get_random_string(length=10):
    """Generate a random string of fixed length."""
    letters = string.ascii_letters
    return "".join(random.choice(letters) for _ in range(length))


def create_commit(repo_path, message):
    with open(os.path.join(repo_path, "testfile.txt"), "w") as file:
        file.write(get_random_string())
    repo = git.Repo(repo_path)
    repo.index.add("testfile.txt")
    repo.index.commit(message)


def test_git_handler(git_repo_fixture):
    local_repo_dir, remote_repo_dir = git_repo_fixture
    git_handler = GitHandler(local_repo_dir, "main")
    current_local_commit = git_handler.get_current_local_commit()
    current_remote_commit = git_handler.get_current_upstream_commit()  # this also sets rate limit timer.
    assert current_local_commit == current_remote_commit, "repo is not up to most recent upstream commit"
    create_commit(remote_repo_dir, "upstream commit")
    assert not git_handler.has_new_version(), "rate limiting failed"
    assert git_handler.has_new_version(rate_limit=False), "recognizing upstream change failed"
    git_handler.update_local()
    assert not git_handler.has_new_version(rate_limit=False), "updating failed"

