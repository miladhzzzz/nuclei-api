import os, aiofiles
from dotenv import load_dotenv
from controllers.NucleiController import NucleiController

load_dotenv()

nulcei_upload_save_path = os.getenv("NUCLEI_CUSTOM_TEMPLATE_UPLOAD_PATH")

nuclei_controller = NucleiController()

class TemplateController():

    def __init__(self):
        pass

    async def save_template(self, template_file: bytes , template_filename: str):

        # Define path to save uploaded template
        save_path = f"{nulcei_upload_save_path}/{template_filename}"

        # Ensure the directory exists
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        # Validate the template
        template_validation =  await nuclei_controller.validate_template(template_file)

        if template_validation is not None:
            return template_validation

        # Save the validated template asynchronously
        async with aiofiles.open(save_path, "wb") as f:
            await f.write(template_file)
