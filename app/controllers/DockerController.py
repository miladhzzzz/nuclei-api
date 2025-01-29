import subprocess, shlex, json
from typing import Iterator

class DockerController:
    def __init__(self):
        pass

    def _run_command(self, command):
        """Helper method to run Docker commands using subprocess."""
        try:
            # Run the command and capture the output
            result = subprocess.run(shlex.split(command), check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return result.stdout.decode('utf-8')
        except subprocess.CalledProcessError as e:
            print(f"Error: {e.stderr.decode('utf-8')}")
            return None

    def list_containers(self, all=False):
        """List running containers or all containers."""
        command = "docker ps"
        if all:
            command += " -a"
        return self._run_command(command)

    def run_container(self, image, name=None, ports=None, detach=True, environment=None, volumes=None, command=None):
        """Run a new container from a specified image with optional configurations and commands."""
        cmd = f"docker run"

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
        
        # Add the image and optional command
        cmd += f" {image}"
        if command:
            cmd += f" {command}"
        
        return self._run_command(cmd)

    def stop_container(self, container_id_or_name):
        """Stop a running container."""
        command = f"docker stop {container_id_or_name}"
        return self._run_command(command)

    def remove_container(self, container_id_or_name, force=False):
        """Remove a container."""
        command = f"docker rm {'-f' if force else ''} {container_id_or_name}"
        return self._run_command(command)

    def stream_container_logs(self, container_id_or_name: str, stream: bool = False) -> Iterator[dict]:
        """
        Fetch logs from a Docker container.

        Args:
            container_id_or_name (str): Container ID or name.
            stream (bool): Stream logs in real-time if True.

        Yields:
            dict: JSON object with log lines or error messages.
        """
        command = f"docker logs --tail 1000 {'--follow' if stream else ''} {container_id_or_name}"
        try:
            process = subprocess.Popen(
                shlex.split(command),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            while True:
                output = process.stdout.readline()
                error_output = process.stderr.readline()

                if output:
                    yield {output.strip()}
                elif error_output:
                    yield {error_output.strip()}
                elif process.poll() is not None:
                    break
        except Exception as e:
            yield {"error": str(e)}

    def container_stats(self, container_id_or_name):
        """Fetch resource usage stats of a running container."""
        command = f"docker stats --no-stream {container_id_or_name}"
        return self._run_command(command)

    def container_inspect(self, container_id_or_name):
        """Inspect a container and retrieve detailed information."""
        command = f"docker inspect {container_id_or_name}"
        result = self._run_command(command)
        return json.loads(result) if result else None

    def exec_in_container(self, container_id_or_name, cmd):
        """Execute a command inside a running container."""
        command = f"docker exec {container_id_or_name} {cmd}"
        return self._run_command(command)
    
    def pull_image(self, image_name):
        """Pull a Docker image."""
        command = f"docker pull {image_name}"
        return self._run_command(command)