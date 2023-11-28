import time
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


def test_stop_image_no_containers_running(temp_dir):
    docker_handler = DockerHandler(image_name=TEST_IMAGE_NAME, data_path=temp_dir)
    while docker_handler.running_workers:
        logging.warning("wait for runs to finish")
        time.sleep(1)
    assert docker_handler.running_workers == 0
    docker_handler.stop_image()


def test_stop_container(temp_dir):
    """Test if we can stop a single container."""
    expected_delay = 3 # we wait 1 second before force stopping a container 
    client = docker.from_env()
    docker_handler = DockerHandler(image_name=TEST_IMAGE_NAME, data_path=temp_dir)
    start_time = time.time()
    container_id = docker_handler.run_task("test")
    container = client.containers.get(container_id)
    docker_handler._stop_container(container)
    time.sleep(1)
    stop_time = time.time()
    with pytest.raises(docker.errors.NotFound) as e:
        client.containers.get(container_id)
    assert stop_time - start_time < expected_delay

def test_stop_image(temp_dir):
    """Test if we can stop multiple containers for the given image."""
    expected_delay = 5 # there might be some delay 
    docker_handler = DockerHandler(image_name=TEST_IMAGE_NAME, data_path=temp_dir)
    assert docker_handler.running_workers == 0
    for _ in range(10):
        docker_handler.run_task("test")
    assert docker_handler.running_workers == 10
    start_time = time.time()
    docker_handler.stop_image()
    stop_time = time.time()
    elapsed_time = stop_time - start_time
    assert elapsed_time < expected_delay
    assert docker_handler.running_workers == 0



def test_wait_image(temp_dir):
    expected_time = 10 # image sleeps for 10
    docker_handler = DockerHandler(image_name=TEST_IMAGE_NAME, data_path=temp_dir)
    assert docker_handler.running_workers == 0
    start_time = time.time()
    for _ in range(10):
        docker_handler.run_task("test")
    assert docker_handler.running_workers == 10
    docker_handler.wait_image()
    stop_time = time.time()
    elapsed_time = stop_time - start_time
    assert docker_handler.running_workers == 0
    assert elapsed_time > expected_time


def test_run_task(temp_dir):
    """Start a task from DockerHandler, get running container by id and match CMD."""
    docker_handler = DockerHandler(image_name=TEST_IMAGE_NAME, data_path=temp_dir)
    container_id = docker_handler.run_task("test")
    client = docker.from_env()
    cmd = client.containers.get(container_id).attrs["Config"]["Cmd"]
    assert " ".join(cmd).endswith(DockerHandler.COMMAND.format(sample_hash="test"))
