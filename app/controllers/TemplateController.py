import os, aiofiles, asyncio, yaml
from typing import Optional
import subprocess
from tempfile import NamedTemporaryFile
from helpers.config import Config

class TemplateController:
    def __init__(self, conf=None):
        self.conf = conf or Config()

    def is_nuclei_workflow(self, file_path: str) -> bool:
        """
        Check if a YAML file is a Nuclei workflow.
        
        Args:
            file_path (str): Path to the YAML file.
        Returns:
            bool: True if it's a workflow, False if it's a template or invalid.
        """
        try:
            with open(file_path, 'r') as f:
                content = yaml.safe_load(f)
            
            if not isinstance(content, dict):
                return False
            
            # Check for workflow-specific keys
            if 'workflow' in content or 'workflows' in content:
                return True
            
            # Look for templates key in a nested structure
            for key in content:
                if isinstance(content[key], dict) and 'templates' in content[key]:
                    return True
            
            # If it has 'id' and 'info' but no workflow markers, it's likely a template
            if 'id' in content and 'info' in content and 'workflow' not in content:
                return False
            
            return False  # Default to False if unclear
        except (yaml.YAMLError, FileNotFoundError, Exception) as e:
            print(f"Error parsing {file_path}: {e}")
            return False

    async def save_template(self, template_file: bytes , template_filename: str):

        # Define path to save uploaded template
        save_path = f"{self.conf.nuclei_upload_template_path}/{template_filename}"

        # Ensure the directory exists
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        # Validate the template
        template_validation =  await self.validate_template(template_file)

        if template_validation is not None:
            return template_validation

        # Save the validated template asynchronously
        async with aiofiles.open(save_path, "wb") as f:
            await f.write(template_file)
    
    async def validate_template(self, template_content: bytes) -> str | None:
        """
        Validate a nuclei template.
        
        Args:
            template_content (bytes): The raw bytes of uploaded nuclei template file.
        Returns:
            None: if the template is valid it will return None.
            str: if the template is invalid it returns the error.
        """
        with NamedTemporaryFile(delete=False, suffix=".yaml") as temp_file:
            temp_file.write(template_content)
            temp_path = temp_file.name

        is_workflow = self.is_nuclei_workflow(temp_path)
        flag = "-w" if is_workflow else "-t"
        
        try:
            process = await asyncio.create_subprocess_exec(
                "nuclei", flag, temp_path, "-validate",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            _, stderr = await process.communicate()
            return None if process.returncode == 0 else stderr.decode()
        finally:
            os.unlink(temp_path)

    def validate_template_cel(self, template_path: str) -> Optional[str]:
        """
        Synchronously validate a Nuclei template or workflow.
        Returns None if valid, or an error message if invalid.
        """
        is_workflow = self.is_nuclei_workflow(template_path)
        flag = "-w" if is_workflow else "-t"

        try:
            # Run the nuclei command synchronously
            process = subprocess.run(
                ["nuclei", flag, template_path, "-validate"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,  # Decode output as text (str) instead of bytes
                check=False  # Don't raise an exception on non-zero exit code
            )
            # Return None if successful (returncode == 0), otherwise return stderr
            return None if process.returncode == 0 else process.stderr
        except Exception as e:
            # Handle any subprocess errors (e.g., nuclei not found)
            return str(e)