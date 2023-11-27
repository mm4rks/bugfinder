import logging
import shutil
import tempfile
from io import BytesIO

import docker
import pytest

from worker import DockerHandler

DOCKERFILE = """
FROM alpine:latest
ENTRYPOINT sleep 10
"""

TEST_IMAGE_NAME = "bugfinder-test-image"


@pytest.fixture(scope="session", autouse=True)
def docker_image():
    logging.debug("building test image")
    client = docker.from_env()
    dockerfile = BytesIO(DOCKERFILE.encode("utf-8"))
    client.images.build(fileobj=dockerfile, tag=TEST_IMAGE_NAME, rm=True)
    yield
    logging.debug("removing test image")
    client.images.remove(image=TEST_IMAGE_NAME, force=True)


@pytest.fixture
def temp_dir():
    # Create a temporary directory
    directory = tempfile.mkdtemp()
    yield directory
    # Teardown: remove the temporary directory
    shutil.rmtree(directory)


def test_run_task(temp_dir):
    """Start a task from DockerHandler, get running container by id and match CMD."""
    docker_handler = DockerHandler(image_name=TEST_IMAGE_NAME, data_path=temp_dir)
    container_id = docker_handler.run_task("test")
    client = docker.from_env()
    cmd = client.containers.get(container_id).attrs['Config']['Cmd']
    assert " ".join(cmd).endswith(DockerHandler.COMMAND.format(sample_hash="test"))
