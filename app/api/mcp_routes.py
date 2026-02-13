from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse
from app.services.helper import ScanService, TemplateService
import logging

# MCP endpoints for Model Context Protocol (LLM/agent integration)
router = APIRouter()
scan_service = ScanService()
template_service = TemplateService()
logger = logging.getLogger(__name__)

def get_mcp_tools_manifest():
    return {
        "tools": [
            {
                "name": "nuclei_scan",
                "description": "Run a Nuclei scan on a target.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "target": {"type": "string"},
                        "templates": {"type": "array", "items": {"type": "string"}},
                        "prompt": {"type": "string"}
                    },
                    "required": ["target"]
                }
            },
            {
                "name": "nuclei_scan_ai",
                "description": "Run a Nuclei scan with prompt-driven template generation.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "target": {"type": "string"},
                        "prompt": {"type": "string"}
                    },
                    "required": ["target", "prompt"]
                }
            },
            {
                "name": "nuclei_scan_custom_template",
                "description": "Run a Nuclei scan with a custom template file provided by the user.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "target": {"type": "string"},
                        "template_content": {"type": "string", "description": "Base64 encoded YAML template content"},
                        "template_filename": {"type": "string", "description": "Optional filename for the template"}
                    },
                    "required": ["target", "template_content"]
                }
            },
            {
                "name": "template_upload",
                "description": "Upload a custom Nuclei template.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filename": {"type": "string"},
                        "content": {"type": "string", "description": "YAML content, base64-encoded or plain."}
                    },
                    "required": ["filename", "content"]
                }
            },
            {
                "name": "get_task_status",
                "description": "Get the status/result of a scan or pipeline task.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "string"}
                    },
                    "required": ["task_id"]
                }
            },
            {
                "name": "get_container_logs",
                "description": "Get logs for a specific container by name.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "container_name": {"type": "string"}
                    },
                    "required": ["container_name"]
                }
            },
            {
                "name": "get_container_status",
                "description": "Get status for a specific container by name.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "container_name": {"type": "string"}
                    },
                    "required": ["container_name"]
                }
            }
        ]
    }

@router.get("/v1/tools", tags=["MCP"])
def mcp_tools_manifest():
    return get_mcp_tools_manifest()

@router.post("/v1/tool-calls", tags=["MCP"])
def mcp_tool_calls(payload: dict = Body(...)):
    tool_name = payload.get("tool_name")
    args = payload.get("arguments", {})
    try:
        if tool_name == "nuclei_scan":
            target = args["target"]
            templates = args.get("templates")
            prompt = args.get("prompt")
            if prompt:
                task = scan_service.run_ai_scan(target, prompt)
                return {"result": {"task_id": task.id, "message": "AI scan pipeline started"}}
            else:
                result = scan_service.run_scan(target, templates)
                if isinstance(result, dict):
                    return {"result": result}
                return {"result": {"task_id": result.id, "message": "Scan pipeline started"}}
        elif tool_name == "nuclei_scan_ai":
            target = args["target"]
            prompt = args["prompt"]
            task = scan_service.run_ai_scan(target, prompt)
            return {"result": {"task_id": task.id, "message": "AI scan pipeline started"}}
        elif tool_name == "nuclei_scan_custom_template":
            target = args["target"]
            template_content = args["template_content"]
            template_filename = args.get("template_filename")
            result = scan_service.run_custom_template_scan(target, template_content, template_filename)
            if "error" in result:
                return JSONResponse(status_code=500, content={"error": result["error"]})
            return {"result": {"message": "Custom template scan completed", "scan_result": result}}
        elif tool_name == "template_upload":
            filename = args["filename"]
            content = args["content"]
            import base64
            try:
                file_bytes = base64.b64decode(content)
            except Exception:
                file_bytes = content.encode()
            save_validation = template_service.upload_template(file_bytes, filename)
            if save_validation is not None:
                return JSONResponse(status_code=400, content={"error": f"Invalid template: {save_validation}"})
            return {"result": {"template_name": filename, "message": "Template Saved successfully"}}
        elif tool_name == "get_task_status":
            from celery.result import AsyncResult
            task_id = args["task_id"]
            task_result = AsyncResult(task_id)
            if not task_result:
                return JSONResponse(status_code=404, content={"error": "Task not found"})
            response = {"task_id": task_id, "status": task_result.status}
            if task_result.ready():
                if task_result.successful():
                    response["result"] = task_result.result
                else:
                    response["error"] = str(task_result.result)
            return {"result": response}
        elif tool_name == "get_container_logs":
            container_name = args["container_name"]
            from controllers.DockerController import DockerController
            docker_controller = DockerController()
            try:
                container_status = docker_controller.get_container_status(container_name)
                if "error" in container_status:
                    return JSONResponse(status_code=404, content={"error": f"Container not found: {container_name}"})
                logs = docker_controller.get_container_logs(container_name)
                return {"result": {"container_name": container_name, "status": container_status, "logs": logs}}
            except Exception as e:
                return JSONResponse(status_code=500, content={"error": f"Failed to get container logs: {str(e)}"})
        elif tool_name == "get_container_status":
            container_name = args["container_name"]
            from controllers.DockerController import DockerController
            docker_controller = DockerController()
            try:
                container_status = docker_controller.get_container_status(container_name)
                if "error" in container_status:
                    return JSONResponse(status_code=404, content={"error": f"Container not found: {container_name}"})
                return {"result": {"container_name": container_name, "status": container_status}}
            except Exception as e:
                return JSONResponse(status_code=500, content={"error": f"Failed to get container status: {str(e)}"})
        else:
            return JSONResponse(status_code=400, content={"error": f"Unknown tool: {tool_name}"})
    except Exception as exc:
        logger.error(f"MCP tool call error for {tool_name}: {exc}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": f"Internal error: {str(exc)}"}) 