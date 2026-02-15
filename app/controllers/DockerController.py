import json
import logging
import shlex
import subprocess
from typing import Callable, Iterator

from controllers.DockerApiController import DockerController as DockerApiController

logger = logging.getLogger(__name__)


class ShellDockerController:
    def __init__(self):
        pass  # Stateless; no instance variables required

    def _run_command(self, command):
        try:
            result = subprocess.run(shlex.split(command), check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return result.stdout.decode("utf-8")
        except subprocess.CalledProcessError as e:
            logger.warning("Docker shell command failed: %s", e.stderr.decode("utf-8").strip())
            return None

    def list_containers(self, all=False):
        command = "docker ps"
        if all:
            command += " -a"
        return self._run_command(command)

    def run_container(self, image, name=None, ports=None, detach=True, environment=None, volumes=None, command=None):
        cmd = "docker run"
        if detach:
            cmd += " -d"
        if name:
            cmd += f" --name {name}"
        if ports:
            for host_port, container_port in ports.items():
                cmd += f" -p {host_port}:{container_port}"
        if environment:
            for key, value in environment.items():
                cmd += f" -e {key}={value}"
        if volumes:
            for host_path, container_path in volumes.items():
                cmd += f" -v {host_path}:{container_path}"
        cmd += f" {image}"
        if command:
            if isinstance(command, list):
                cmd += " " + " ".join(shlex.quote(str(arg)) for arg in command)
            else:
                cmd += f" {command}"
        return self._run_command(cmd)

    def stop_container(self, container_id_or_name):
        command = f"docker stop {container_id_or_name}"
        return self._run_command(command)

    def remove_container(self, container_id_or_name, force=False):
        command = f"docker rm {'-f' if force else ''} {container_id_or_name}"
        return self._run_command(command)

    def stream_container_logs(self, container_id_or_name: str, stream: bool = False) -> Iterator[str]:
        command = f"docker logs --tail 1000 {'--follow' if stream else ''} {container_id_or_name}"
        try:
            process = subprocess.Popen(
                shlex.split(command),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            while True:
                output = process.stdout.readline()
                error_output = process.stderr.readline()
                if output:
                    yield output.strip()
                elif error_output:
                    yield error_output.strip()
                elif process.poll() is not None:
                    break
        except Exception as e:
            yield f"error: {str(e)}"

    def container_stats(self, container_id_or_name):
        command = f"docker stats --no-stream {container_id_or_name}"
        return self._run_command(command)

    def container_status(self, container_id_or_name):
        command = f"docker inspect --format='{{.State.Status}}' {container_id_or_name}"
        result = self._run_command(command)
        return result if result else None

    def container_inspect(self, container_id_or_name):
        command = f"docker inspect {container_id_or_name}"
        result = self._run_command(command)
        return json.loads(result) if result else None

    def exec_in_container(self, container_id_or_name, cmd):
        command = f"docker exec {container_id_or_name} {cmd}"
        return self._run_command(command)

    def pull_image(self, image_name):
        command = f"docker pull {image_name}"
        return self._run_command(command)

    def get_container_status(self, container_id_or_name):
        try:
            status_cmd = f"docker inspect --format='{{.State.Status}}' {container_id_or_name}"
            running_cmd = f"docker inspect --format='{{.State.Running}}' {container_id_or_name}"

            status = self._run_command(status_cmd)
            running = self._run_command(running_cmd)

            return {
                "status": status.strip() if status else "unknown",
                "running": running.strip().lower() == "true" if running else False,
            }
        except Exception as e:
            return {"status": "error", "running": False, "error": str(e)}

    def get_container_logs(self, container_id_or_name, tail=1000):
        command = f"docker logs --tail {tail} {container_id_or_name}"
        return self._run_command(command)


class DockerController:
    """
    Docker controller that prefers SDK-backed operations and transparently
    falls back to shell-based Docker CLI commands when SDK calls fail.
    """

    def __init__(self):
        self.shell = ShellDockerController()
        self.api = None
        try:
            self.api = DockerApiController()
        except Exception as e:
            logger.warning("Docker SDK controller initialization failed (%s); using Docker CLI fallback only", e)

    def _should_fallback(self, result) -> bool:
        if result is None:
            return True
        return isinstance(result, dict) and "error" in result

    def _call_with_fallback(self, api_call: Callable[[], object], shell_call: Callable[[], object], op_name: str):
        if self.api is None:
            return shell_call()
        try:
            result = api_call()
            if self._should_fallback(result):
                logger.warning("Docker SDK %s returned an error; falling back to Docker CLI", op_name)
                return shell_call()
            return result
        except Exception as e:
            logger.warning("Docker SDK %s failed (%s); falling back to Docker CLI", op_name, e)
            return shell_call()

    def _run_command(self, command):
        # Backward compatibility for existing call sites.
        return self.shell._run_command(command)

    def list_containers(self, all=False):
        return self._call_with_fallback(
            lambda: self.api.list_containers(all=all),
            lambda: self.shell.list_containers(all=all),
            "list_containers",
        )

    def run_container(self, image, name=None, ports=None, detach=True, environment=None, volumes=None, command=None):
        result = self._call_with_fallback(
            lambda: self.api.run_container(
                image=image,
                name=name,
                ports=ports,
                detach=detach,
                environment=environment,
                volumes=volumes,
                command=command,
            ),
            lambda: self.shell.run_container(
                image=image,
                name=name,
                ports=ports,
                detach=detach,
                environment=environment,
                volumes=volumes,
                command=command,
            ),
            "run_container",
        )

        # Keep historical behavior for callers expecting container id string.
        if isinstance(result, dict) and "id" in result:
            return result["id"]
        return result

    def stop_container(self, container_id_or_name):
        return self._call_with_fallback(
            lambda: self.api.stop_container(container_id_or_name),
            lambda: self.shell.stop_container(container_id_or_name),
            "stop_container",
        )

    def remove_container(self, container_id_or_name, force=False):
        return self._call_with_fallback(
            lambda: self.api.remove_container(container_id_or_name, force=force),
            lambda: self.shell.remove_container(container_id_or_name, force=force),
            "remove_container",
        )

    def stream_container_logs(self, container_id_or_name: str, stream: bool = False, tail: int = 1000) -> Iterator[str]:
        try:
            api_logs = self.api.stream_container_logs(container_id_or_name, stream=stream, tail=tail)
            first_item = next(api_logs, None)
            if first_item is None:
                return
            if isinstance(first_item, str) and first_item.lower().startswith("error:"):
                logger.warning("Docker SDK stream_container_logs returned an error; falling back to Docker CLI")
                yield from self.shell.stream_container_logs(container_id_or_name, stream=stream)
                return

            yield first_item
            for line in api_logs:
                yield line
        except Exception as e:
            logger.warning("Docker SDK stream_container_logs failed (%s); falling back to Docker CLI", e)
            yield from self.shell.stream_container_logs(container_id_or_name, stream=stream)

    def container_stats(self, container_id_or_name):
        return self._call_with_fallback(
            lambda: self.api.container_stats(container_id_or_name),
            lambda: self.shell.container_stats(container_id_or_name),
            "container_stats",
        )

    def container_status(self, container_id_or_name):
        return self._call_with_fallback(
            lambda: self.api.container_status(container_id_or_name),
            lambda: self.shell.container_status(container_id_or_name),
            "container_status",
        )

    def container_inspect(self, container_id_or_name):
        return self._call_with_fallback(
            lambda: self.api.container_inspect(container_id_or_name),
            lambda: self.shell.container_inspect(container_id_or_name),
            "container_inspect",
        )

    def exec_in_container(self, container_id_or_name, cmd):
        return self._call_with_fallback(
            lambda: self.api.exec_in_container(container_id_or_name, cmd),
            lambda: self.shell.exec_in_container(container_id_or_name, cmd),
            "exec_in_container",
        )

    def pull_image(self, image_name):
        return self._call_with_fallback(
            lambda: self.api.pull_image(image_name),
            lambda: self.shell.pull_image(image_name),
            "pull_image",
        )

    def get_container_status(self, container_id_or_name):
        return self._call_with_fallback(
            lambda: self.api.get_container_status(container_id_or_name),
            lambda: self.shell.get_container_status(container_id_or_name),
            "get_container_status",
        )

    def get_container_logs(self, container_id_or_name, tail=1000):
        return self._call_with_fallback(
            lambda: self.api.get_container_logs(container_id_or_name, tail=tail),
            lambda: self.shell.get_container_logs(container_id_or_name, tail=tail),
            "get_container_logs",
        )
