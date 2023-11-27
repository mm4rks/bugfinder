import atexit
import logging
import time
from pathlib import Path

import docker
from git import Repo

# from processing import docker_utils, file_utils


class DatabaseHandler:
    FILTERED_DB = "filtered.sqlite3"

    def __init__(self, data_path: str):
        self.data_path = Path(data_path)

        if not self.data_path.is_dir():
            raise ValueError(f"The specified data path '{self.data_path}' does not exist or is not a directory.")



class GitHandler:
    RATE_LIMIT_DURATION = 600
    COMMIT_HASH_LEN = 8

    def __init__(self, repo_path: str | Path, dewolf_branch: str = "main"):
        self._repo_path = Path(repo_path)
        self.dewolf_branch = dewolf_branch
        self._last_query = 0
        self._current_upstream_commit = None

        if not self._repo_path.is_dir():
            raise ValueError(f"The specified repository path '{self._repo_path}' does not exist or is not a directory.")

        self.repo = Repo(self._repo_path)

    def get_current_local_commit(self) -> str:
        self.repo.git.checkout(self.dewolf_branch)
        commit = self.repo.head.commit.hexsha
        logging.debug(f"current local commit: {commit}")
        return commit[:self.COMMIT_HASH_LEN]

    def _get_current_upstream_commit(self):
        """Query upstream repository for new commit (fetch)."""
        self.repo.git.checkout(self.dewolf_branch)
        self.repo.remotes.origin.fetch()
        commit = self.repo.git.rev_parse(f"{self.dewolf_branch}@{{upstream}}")
        logging.debug(f"current local commit: {commit}")
        return commit[:self.COMMIT_HASH_LEN]

    def _is_rate_limit_hit(self) -> bool:
        """Return True if the query should be rate limited."""
        current_time = time.time()
        time_diff = current_time - self._last_query

        if time_diff < self.RATE_LIMIT_DURATION:
            logging.info("Rate limit hit")
            return True
        return False

    def get_current_upstream_commit(self, rate_limit: bool = True):
        """Query upstream commit if rate limit allows it."""
        logging.info("Checking for upstream commit...")
        if not rate_limit or not self._is_rate_limit_hit():
            self._current_upstream_commit = self._get_current_upstream_commit()
            self._last_query = time.time()
        return self._current_upstream_commit

    def has_new_version(self, rate_limit: bool = True) -> bool:
        """Return True if last upstream commit differs from current local commit."""
        return self.get_current_local_commit() != self.get_current_upstream_commit(rate_limit=rate_limit)

    def update_local(self):
        """Pull the latest changes from upstream."""
        logging.info("Updating local repository with new changes from upstream.")
        self.repo.git.checkout(self.dewolf_branch)
        try:
            self.repo.git.pull('origin', self.dewolf_branch)
            logging.info("Local repository updated successfully.")
        except Exception as e:
            logging.error(f"Failed to update local repository: {e}")
            raise

class DockerHandler:
    COMMAND = "python decompiler/util/bugfinder/bugfinder.py /data/samples/{sample_hash} --sqlite-file /data/samples.sqlite3"
    MOUNT_POINT = "/data"

    def __init__(self, image_name: str, data_path: str | Path, max_time: int = 600):
        self.image_name = image_name
        self.data_path = Path(data_path)
        self.max_time = max_time
        self.client = docker.from_env()

        if not self.data_path.is_dir():
            raise ValueError(f"The specified data path '{self.data_path}' does not exist or is not a directory.")

    def stop_image(self) -> None:
        """
        Stop all containers for the current image.
        """
        logging.info(f"Stopping containers for {self.image_name}...")
        containers = self.client.containers.list(filters={"ancestor": self.image_name})
        if not containers:
            logging.info(f"No containers running for image: {self.image_name}")
        else:
            for container in containers:
                container.stop()

    def wait_image(self) -> None:
        """
        Wait for all containers of the current image to stop.
        """
        logging.info("Wait for running containers...")
        containers = self.client.containers.list(filters={"ancestor": self.image_name})
        if not containers:
            logging.info(f"No containers running for image: {self.image_name}")
            return

        logging.info("Waiting for containers:")
        for container in containers:
            if container.status == "running":
                logging.info(f"Waiting for container: {container.id}")
                container.wait()  # This will block until the container stops
            else:
                logging.info(f"Container {container.id} is not running")

    def run_task(self, sample_hash: str) -> str:
        """
        Run a Docker task in the background.
        """
        full_command = f"timeout {self.max_time} {self.COMMAND.format(sample_hash=sample_hash)}"
        container = self.client.containers.run(
            self.image_name,
            full_command,
            detach=True,
            remove=True,
            mounts=[docker.types.Mount(type="bind", source=str(self.data_path), target=self.MOUNT_POINT)],
        )
        return container.id


class BugfinderWorker:
    base_dir = Path(__file__).parent.resolve()

    IMAGE_NAME = "bugfinder-dewolf"
    BUGFINDER_DB_NAME = "samples.sqlite3"
    DEWOLF_REPO = base_dir / "dewolf" / "repo"
    DEWOLF_BRANCH = "main"
    MAX_WORKERS = 8
    WORKER_TIMEOUT = 600
    DATA_PATH = base_dir / "data"
    SAMPLES_PATH = DATA_PATH / "samples"
    STATE_JSON = base_dir / "data" / "state.json"
    SLEEP_TIME = 6

    def __init__(self):
        self.docker_handler = DockerHandler(self.IMAGE_NAME, self.DATA_PATH)
        self.git_handler = GitHandler(self.DEWOLF_REPO)
        self.quick_run_samples = set()
        self.long_run_samples = set()
        self.all_samples = {file.name for file in self.SAMPLES_PATH.iterdir() if file.is_file()}
        self.load_state()

    def load_state(self):
        logging.info("Loading state")
        pass

    def save_state(self):
        logging.info("Saving state")
        pass

    def update_database(self, tag: str):
        """
        Filter samples.sqlite3 populated by bugfinder.py:
        Write filtered errors with tag to filtered.sqlite3 for display in web interface.
        Rotate samples.sqlite3
        """
        logging.info("Updating database")
        samples_db =self.DATA_PATH / self.BUGFINDER_DB_NAME 
        if not samples_db.is_file():
            logging.warning(f"The database {samples_db} does not exist. Nothing to update")
            return
        # shutil.copyfile(filtered.sqlite3, filtered.sqlite3.bak)
        current_local_commit = self.git_handler.get_current_local_commit()
        # python filter.py -i data/samples.sqlite3 -o data/filtered.sqlite3 --tag ${tag}
        # mv --backup=numbered data/samples.sqlite3 data/"${tag}_${current_commit}.sqlite3"

    def update_dewolf(self):
        logging.info("Updating dewolf")
        pass 

    def init_new_run(self):
        logging.info("Initializing new run")
        pass 

    def dispatch_runner(self):
        logging.info("Dispatching runner...")
        pass 

    def run(self):
        while True:
            if self.git_handler.has_new_version():
                self.update_dewolf()
                self.init_new_run()
            self.dispatch_runner()
            logging.info(f"Sleeping for {self.SLEEP_TIME}")
            time.sleep(self.SLEEP_TIME)

    def cleanup(self):
        logging.info("Cleaning up...")
        self.save_state()
        # stop runners



if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    worker_instance = BugfinderWorker()
    atexit.register(worker_instance.cleanup)

    try:
        worker_instance.run()
    except KeyboardInterrupt:
        logging.info("Program interrupted by user")
    except Exception as e:
        logging.error("Unhandled exception", exc_info=e)
