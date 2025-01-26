import random
from controllers.DockerController import DockerController

class NucleiController:
    def __init__(self):
        self.docker = DockerController()
        self.nuclei_image = "projectdiscovery/nuclei:latest"

    def generate_scan_id(self) -> int:
        """
        Generate a random 6-digit number.
        
        Returns:
            int: A random 6-digit number.
        """
        return random.randint(100000, 999999)
    
    def check_docker(self):
        res = self.docker._run_command("docker version")
        if res is None:
            print("Docker Not Found!")
            exit(222)

    def pull_nuclei_image(self):
        """Ensure the latest Nuclei image is pulled."""
        self.check_docker()
        
        result = self.docker.pull_image(self.nuclei_image)
        return {"message": "Image pulled successfully", "details": result}

    def run_nuclei_scan(self, target: str, template: str = None):
        """
        Run a Nuclei scan in a Docker container.
        
        Args:
            target (str): The target to scan.
            template (str): Optional template to use for the scan.
        
        Returns:
            dict: Container Name or error message.
        """
        command = ["-u", target]
        if template:
            command += ["-t", template]
        
        container_name = f"nuclei_scan_{self.generate_scan_id()}"
        container_id = self.docker.run_container(
            image=self.nuclei_image,
            command=" ".join(command),
            detach=True,
            name=container_name
        )

        print(f"New Scan Started: nuclei_command:{command}, container_name:{container_name}")

        return {"container_name": container_name, "message": "Scan started successfully"}
    