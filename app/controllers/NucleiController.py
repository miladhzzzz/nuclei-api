import random
import logging
from typing import Dict, List, Optional, Union
from pathlib import Path
from helpers.config import Config
from tempfile import NamedTemporaryFile
from controllers.DockerController import DockerController
from controllers.TemplateController import TemplateController

logger = logging.getLogger(__name__)

class NucleiController:
    def __init__(self, docker_controller=None, template_controller=None, conf=None):
        self.docker = docker_controller or DockerController()
        self.template_controller = template_controller or TemplateController()
        self.conf = conf or Config()
        self.nuclei_image = "projectdiscovery/nuclei:latest"
        self.nuclei_template = self.conf.nuclei_template_path

    def generate_scan_id(self) -> int:
        """
        Generate a random 6-digit number.
        
        Returns:
            int: A random 6-digit number.
        """
        return random.randint(100000, 999999)
    
    def check_docker(self):
        """Check if Docker is available and running."""
        try:
            res = self.docker._run_command("docker version")
            if res is None:
                raise RuntimeError("Docker is not running or not accessible")
            return True
        except Exception as e:
            logger.error(f"Docker check failed: {e}")
            raise RuntimeError(f"Docker Not Found or not accessible: {e}")

    def pull_nuclei_image(self):
        """Ensure the latest Nuclei image is pulled."""
        try:
            self.check_docker()
            result = self.docker.pull_image(self.nuclei_image)
            logger.info("Nuclei image pulled successfully")
            return {"message": "Image pulled successfully", "details": result}
        except Exception as e:
            logger.error(f"Failed to pull Nuclei image: {e}")
            raise

    def _build_nuclei_command(self, target: str, template: Optional[List[str]] = None, 
                            template_file: Optional[str] = None, cve_id: Optional[str] = None) -> List[str]:
        """
        Build the Nuclei command based on scan parameters.
        
        Args:
            target: The target to scan
            template: List of template names
            template_file: Path to a specific template file
            cve_id: CVE ID for AI-generated templates
            
        Returns:
            List of command arguments
        """
        command = ["-u", target, "-nmhe"]
        
        if template_file:
            # Custom template file
            template_name = Path(template_file).name
            local_template_path = Path(self.nuclei_template) / "custom" / template_name
            is_workflow = self.template_controller.is_nuclei_workflow(str(local_template_path))
            flag = "-w" if is_workflow else "-t"
            command.extend([flag, f"custom/{template_name}"])
            
        elif cve_id:
            # AI-generated template
            ai_template_path = f"ai/{cve_id}.yaml"
            # Check if template exists before using it
            template_full_path = Path(self.nuclei_template) / ai_template_path
            if not template_full_path.exists():
                raise FileNotFoundError(f"AI template not found: {ai_template_path}")
            
            is_workflow = self.template_controller.is_nuclei_workflow(ai_template_path)
            flag = "-w" if is_workflow else "-t"
            command.extend([flag, ai_template_path])
            
        elif template and template != ["."]:
            # Specific template list
            command.extend(["-t"] + template)
            
        # Default: scan with all templates (no additional flags needed)
        
        return command

    def _get_volume_mounts(self) -> Dict[str, str]:
        """Get volume mounts for Nuclei templates."""
        return {f"{self.nuclei_template}": "/root/nuclei-templates"}

    def run_nuclei_scan(self, target: str, template: Optional[List[str]] = None, 
                       template_file: Optional[str] = None, cve_id: Optional[str] = None) -> Dict[str, str]:
        """
        Run a Nuclei scan in a Docker container.
        
        Args:
            target: The target to scan
            template: Optional list of template names to use
            template_file: Path to a specific template file
            cve_id: CVE ID for AI-generated templates
            
        Returns:
            Dict containing scan information or error message
            
        Raises:
            ValueError: If invalid parameters are provided
            RuntimeError: If Docker operations fail
        """
        try:
            # Validate inputs
            if not target:
                raise ValueError("Target is required")
            
            # Check Docker availability
            self.check_docker()
            
            # Build command
            command = self._build_nuclei_command(target, template, template_file, cve_id)
            
            # Get volume mounts
            volumes = self._get_volume_mounts()
            
            # Generate unique container name
            scan_id = self.generate_scan_id()
            container_name = f"nuclei_scan_{scan_id}"
            
            # Run container
            container_id = self.docker.run_container(
                image=self.nuclei_image,
                command=" ".join(command),
                detach=True,
                name=container_name,
                volumes=volumes
            )
            
            if not container_id:
                raise RuntimeError("Failed to start Nuclei container")
            
            logger.info(f"Nuclei scan started - ID: {scan_id}, Container: {container_name}, Command: {' '.join(command)}")
            
            return {
                "scan_id": scan_id,
                "container_name": container_name,
                "container_id": container_id,
                "target": target,
                "command": command,
                "status": "started",
                "message": "Scan started successfully"
            }
            
        except ValueError as e:
            logger.error(f"Invalid parameters for Nuclei scan: {e}")
            return {"error": f"Invalid parameters: {str(e)}", "status": "failed"}
        except FileNotFoundError as e:
            logger.error(f"Template file not found: {e}")
            return {"error": f"Template not found: {str(e)}", "status": "failed"}
        except Exception as e:
            logger.error(f"Nuclei scan failed: {e}", exc_info=True)
            return {"error": f"Scan failed: {str(e)}", "status": "failed"}

    def get_scan_status(self, container_name: str) -> Dict[str, str]:
        """
        Get the status of a running scan.
        
        Args:
            container_name: Name of the container to check
            
        Returns:
            Dict containing container status
        """
        try:
            status = self.docker.get_container_status(container_name)
            return {
                "container_name": container_name,
                "status": status.get("status", "unknown"),
                "running": status.get("running", False)
            }
        except Exception as e:
            logger.error(f"Failed to get scan status for {container_name}: {e}")
            return {"error": f"Status check failed: {str(e)}"}

    def get_scan_results(self, container_name: str) -> Dict[str, str]:
        """
        Get the results of a completed scan.
        
        Args:
            container_name: Name of the container to get logs from
            
        Returns:
            Dict containing scan results
        """
        try:
            logs = self.docker.get_container_logs(container_name)
            return {
                "container_name": container_name,
                "logs": logs,
                "status": "completed"
            }
        except Exception as e:
            logger.error(f"Failed to get scan results for {container_name}: {e}")
            return {"error": f"Failed to get results: {str(e)}"} 
