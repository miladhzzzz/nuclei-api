from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ScanRequest(BaseModel):
    target: str = Field(..., example="google.com")
    templates: Optional[List[str]] = Field(None, example=["cves/"])
    prompt: Optional[str] = Field(None, example="run a scan for finding this CVE on this Operating system")

class ScanWithPromptRequest(BaseModel):
    target: str = Field(..., example="google.com")
    prompt: str = Field(..., example="Generate a template for XSS on this target.")

class ComprehensiveScanRequest(BaseModel):
    target: str = Field(..., example="google.com", description="Target to scan (IP or domain)")
    scan_type: str = Field("auto", example="auto", description="Scan type: auto, fingerprint, ai, custom, workflow, standard")
    templates: Optional[List[str]] = Field(None, example=["cves/", "http/"], description="Template categories to use")
    template_file: Optional[str] = Field(None, example="/path/to/template.yaml", description="Path to custom template file")
    template_content: Optional[str] = Field(None, example="base64_encoded_yaml", description="Base64 encoded template content")
    prompt: Optional[str] = Field(None, example="Scan for XSS vulnerabilities", description="Natural language prompt for AI scan")
    workflow_file: Optional[str] = Field(None, example="/path/to/workflow.yaml", description="Path to workflow file")
    use_fingerprinting: bool = Field(True, example=True, description="Whether to use fingerprinting for OS detection")
    custom_parameters: Optional[Dict[str, Any]] = Field(None, example={"rate_limit": 100}, description="Additional custom parameters")

class ScanResponse(BaseModel):
    task_id: str
    message: str

class CustomTemplateUploadRequest(BaseModel):
    target: str
    template_file: str  # Path or file name

class TemplateGenerationRequest(BaseModel):
    cve_id: str
    description: str

class TemplateGenerationResponse(BaseModel):
    cve_id: str
    template: str

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[dict] = None
    error: Optional[str] = None

class CustomTemplateScanRequest(BaseModel):
    target: str = Field(..., example="example.com")
    template_file: str = Field(..., description="Base64 encoded YAML template content")
    template_filename: Optional[str] = Field(None, example="custom-template.yaml")

class FingerprintRequest(BaseModel):
    target: str = Field(..., example="192.168.1.1", description="Target to fingerprint")

class FingerprintResponse(BaseModel):
    target: str
    task_id: Optional[str] = None
    message: Optional[str] = None
    os_detected: Optional[str] = None
    services: Optional[List[str]] = None
    ports: Optional[List[int]] = None
    recommendations: Optional[List[str]] = None
    error: Optional[str] = None

class TemplateUploadResponse(BaseModel):
    filename: str
    message: str
    task_id: Optional[str] = None
    error: Optional[str] = None

class WorkflowUploadRequest(BaseModel):
    target: str = Field(..., example="example.com")
    workflow_file: str = Field(..., description="Base64 encoded YAML workflow content")
    workflow_filename: Optional[str] = Field(None, example="custom-workflow.yaml")

class ScanResult(BaseModel):
    target: str
    scan_type: str
    templates_used: Optional[List[str]] = None
    vulnerabilities_found: Optional[List[Dict[str, Any]]] = None
    scan_duration: Optional[float] = None
    container_name: Optional[str] = None
    error: Optional[str] = None 