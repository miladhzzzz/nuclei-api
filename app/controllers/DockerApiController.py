import docker
from docker.errors import DockerException, NotFound
from typing import Iterator, Dict, Optional


class DockerController:
    def __init__(self):
        """
        Initialize Docker client using environment configuration.
        Equivalent to Docker CLI context (DOCKER_HOST, etc).
        """
        self.client = docker.from_env()

    # ---------------------------
    # Containers
    # ---------------------------

    def list_containers(self, all: bool = False):
        """
        List containers.
        """
        try:
            containers = self.client.containers.list(all=all)
            return [
                {
                    "id": c.id,
                    "name": c.name,
                    "image": c.image.tags,
                    "status": c.status,
                }
                for c in containers
            ]
        except DockerException as e:
            return {"error": str(e)}

    def run_container(
        self,
        image: str,
        name: Optional[str] = None,
        ports: Optional[Dict[str, str]] = None,
        detach: bool = True,
        environment: Optional[Dict[str, str]] = None,
        volumes: Optional[Dict[str, Dict[str, str]]] = None,
        command: Optional[str] = None,
    ):
        """
        Run a container.

        ports example:
            {"80/tcp": 8080}

        volumes example:
            {
                "/host/path": {
                    "bind": "/container/path",
                    "mode": "rw"
                }
            }
        """
        try:
            container = self.client.containers.run(
                image=image,
                name=name,
                ports=ports,
                detach=detach,
                environment=environment,
                volumes=volumes,
                command=command,
            )
            return {
                "id": container.id,
                "name": container.name,
                "status": container.status,
            }
        except DockerException as e:
            return {"error": str(e)}

    def stop_container(self, container_id_or_name: str):
        try:
            container = self.client.containers.get(container_id_or_name)
            container.stop()
            return {"status": "stopped"}
        except NotFound:
            return {"error": "container not found"}
        except DockerException as e:
            return {"error": str(e)}

    def remove_container(self, container_id_or_name: str, force: bool = False):
        try:
            container = self.client.containers.get(container_id_or_name)
            container.remove(force=force)
            return {"status": "removed"}
        except NotFound:
            return {"error": "container not found"}
        except DockerException as e:
            return {"error": str(e)}

    # ---------------------------
    # Logs & Stats
    # ---------------------------

    def stream_container_logs(
        self,
        container_id_or_name: str,
        stream: bool = False,
        tail: int = 1000,
    ) -> Iterator[str]:
        try:
            container = self.client.containers.get(container_id_or_name)
            logs = container.logs(stream=stream, tail=tail)

            if stream:
                for line in logs:
                    yield line.decode("utf-8").strip()
            else:
                yield logs.decode("utf-8")
        except DockerException as e:
            yield f"error: {str(e)}"

    def container_stats(self, container_id_or_name: str):
        try:
            container = self.client.containers.get(container_id_or_name)
            stats = container.stats(stream=False)
            return stats
        except DockerException as e:
            return {"error": str(e)}

    # ---------------------------
    # Inspect & Status
    # ---------------------------

    def container_status(self, container_id_or_name: str):
        try:
            container = self.client.containers.get(container_id_or_name)
            return container.status
        except DockerException:
            return None

    def container_inspect(self, container_id_or_name: str):
        try:
            container = self.client.containers.get(container_id_or_name)
            return container.attrs
        except DockerException as e:
            return {"error": str(e)}

    def get_container_status(self, container_id_or_name: str):
        try:
            container = self.client.containers.get(container_id_or_name)
            container.reload()

            return {
                "status": container.status,
                "running": container.status == "running",
            }
        except DockerException as e:
            return {"status": "error", "running": False, "error": str(e)}

    def get_container_logs(self, container_id_or_name: str, tail: int = 1000):
        try:
            container = self.client.containers.get(container_id_or_name)
            logs = container.logs(tail=tail)
            return logs.decode("utf-8")
        except DockerException as e:
            return {"error": str(e)}

    # ---------------------------
    # Exec
    # ---------------------------

    def exec_in_container(self, container_id_or_name: str, cmd: str):
        try:
            container = self.client.containers.get(container_id_or_name)
            exec_result = container.exec_run(cmd)
            return exec_result.output.decode("utf-8")
        except DockerException as e:
            return {"error": str(e)}

    # ---------------------------
    # Images
    # ---------------------------

    def pull_image(self, image_name: str):
        try:
            image = self.client.images.pull(image_name)
            return {"id": image.id, "tags": image.tags}
        except DockerException as e:
            return {"error": str(e)}
