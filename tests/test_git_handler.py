import pytest
import git
import os
import tempfile

@pytest.fixture
def git_repo_fixture():
    # Create a temporary directory for the local repository
    local_repo_dir = tempfile.mkdtemp()
    local_repo = git.Repo.init(local_repo_dir)

    # Create another temporary directory for the remote repository
    remote_repo_dir = tempfile.mkdtemp()
    remote_repo = git.Repo.init(remote_repo_dir, bare=True)

    # Add the remote repository to the local repository
    local_repo.create_remote('origin', remote_repo_dir)

    # Return paths for both repositories
    yield local_repo_dir, remote_repo_dir

    # Cleanup
    for repo_dir in [local_repo_dir, remote_repo_dir]:
        for root, dirs, files in os.walk(repo_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(repo_dir)

def test_git_operations(git_repo_fixture):
    local_repo_dir, remote_repo_dir = git_repo_fixture

    # Example test operations
    repo = git.Repo(local_repo_dir)
    assert repo.git_dir == os.path.join(local_repo_dir, '.git')
    assert 'origin' in repo.remotes

    # Further operations can be added here to test various Git functionalities

# Run the test
if __name__ == "__main__":
    pytest.main([__file__])

