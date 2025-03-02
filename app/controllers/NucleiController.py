import random, os, subprocess, asyncio
from dotenv import load_dotenv
from tempfile import NamedTemporaryFile
from controllers.DockerController import DockerController
from controllers.TemplateController import TemplateController

load_dotenv()

class NucleiController:
    def __init__(self):
        self.docker = DockerController()
        self.template_controller = TemplateController()
        self.nuclei_image = "projectdiscovery/nuclei:latest"
        self.nuclei_template = os.getenv("NUCLEI_TEMPLATE_PATH")

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

    def run_nuclei_scan(self, target: str, template: list = None, template_file=None):
        """
        Run a Nuclei scan in a Docker container.
        
        Args:
            target (str): The target to scan.
            template (list): Optional templates to use for the scan.
            template_file (UploadFile): Custom Template YAML file.
        Returns:
            dict: Container Name or error message.
        """
        volumes = {}
        command = ["-u", target , "-nmhe"]

        if template_file:
            volumes = {f"{self.nuclei_template}": "/root/nuclei-templates"}
            # Detect if it's a workflow or template
            is_workflow = self.template_controller.is_nuclei_workflow(template_file)
            flag = "-w" if is_workflow else "-t"
            command += [flag, f"custom/{template_file}"]

        if template and template != ["."]:
            command += ["-t"] + template
        
        container_name = f"nuclei_scan_{self.generate_scan_id()}"
        container_id = self.docker.run_container(
            image=self.nuclei_image,
            command=" ".join(command),
            detach=True,
            name=container_name,
            **({"volumes": volumes} if volumes else {})
        )

        print(f"New Scan Started: nuclei_command:{command}, container_name:{container_name}")

        return {"container_name": container_name, "message": "Scan started successfully"}
    