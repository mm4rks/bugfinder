import os
import shutil
import tempfile

import pytest

from worker import DockerHandler


@pytest.fixture
def temp_dir():
    # Create a temporary directory
    directory = tempfile.mkdtemp()
    yield directory
    # Teardown: remove the temporary directory
    shutil.rmtree(directory)


def test_run_task(temp_dir):
    # Prepare the sample file in the temporary directory
    sample_hash = "sample_hash"
    sample_file_path = os.path.join(temp_dir, f"{sample_hash}.txt")
    with open(sample_file_path, "w") as file:
        file.write("Sample content")

    # Set parameters for run_task
    image_name = "your_image_name"  # Replace with your Docker image name
    max_time = 60  # Example max time in seconds

    # Call the function
    # container_id = run_task(sample_hash, temp_dir, image_name, max_time)

    # Assertions
    # assert isinstance(container_id, str)
    # Add more assertions as needed

    # Note: Depending on the behavior of run_task, you might need to add
    # more logic to check if the Docker container was created correctly,
    # and possibly clean up the container after the test.
