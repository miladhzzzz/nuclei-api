import subprocess, shlex, json
from typing import Iterator

class DockerController:
    def __init__(self):
        pass  # Stateless; no instance variables required

    def _run_command(self, command):
        try:
            result = subprocess.run(shlex.split(command), check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return result.stdout.decode('utf-8')
        except subprocess.CalledProcessError as e:
            print(f"Error: {e.stderr.decode('utf-8')}")
            return None

    def list_containers(self, all=False):
        command = "docker ps"
        if all:
            command += " -a"
        return self._run_command(command)

    def run_container(self, image, name=None, ports=None, detach=True, environment=None, volumes=None, command=None):
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
        cmd += f" {image}"
        if command:
            cmd += f" {command}"
        return self._run_command(cmd)

    def stop_container(self, container_id_or_name):
        command = f"docker stop {container_id_or_name}"
        return self._run_command(command)

    def remove_container(self, container_id_or_name, force=False):
        command = f"docker rm {'-f' if force else ''} {container_id_or_name}"
        return self._run_command(command)

    def stream_container_logs(self, container_id_or_name: str, stream: bool = False) -> Iterator[dict]:
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
        """
        Get detailed container status information.
        
        Args:
            container_id_or_name: Container ID or name
            
        Returns:
            Dict containing status information
        """
        try:
            status_cmd = f"docker inspect --format='{{.State.Status}}' {container_id_or_name}"
            running_cmd = f"docker inspect --format='{{.State.Running}}' {container_id_or_name}"
            
            status = self._run_command(status_cmd)
            running = self._run_command(running_cmd)
            
            return {
                "status": status.strip() if status else "unknown",
                "running": running.strip().lower() == "true" if running else False
            }
        except Exception as e:
            return {"status": "error", "running": False, "error": str(e)}

    def get_container_logs(self, container_id_or_name, tail=1000):
        """
        Get container logs.
        
        Args:
            container_id_or_name: Container ID or name
            tail: Number of lines to return
            
        Returns:
            Container logs as string
        """
        command = f"docker logs --tail {tail} {container_id_or_name}"
        return self._run_command(command)