#!/usr/bin/env python3
"""
Comprehensive test script for the enhanced Nuclei API with all scan types.
This script demonstrates the new comprehensive scan functionality.
"""

import requests
import json
import time
import base64
import sys
import os
from typing import Dict, Any

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
WAIT_FOR_COMPLETION = os.getenv("SCENARIO_WAIT_FOR_COMPLETION", "false").lower() in {"1", "true", "yes"}
TEST_TARGETS = [
    "example.com",
    "192.168.1.1",
    "google.com"
]
FAILED_SCENARIOS = []


def record_failure(name: str, detail: str):
    FAILED_SCENARIOS.append({"name": name, "detail": detail})
    print(f"❌ {name}: {detail}")

def make_request(endpoint: str, method: str = "GET", data: Dict = None, files: Dict = None) -> Dict[str, Any]:
    """Make HTTP request to the API."""
    url = f"{API_BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url)
        elif method.upper() == "POST":
            if files:
                response = requests.post(url, files=files)
            else:
                response = requests.post(url, json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response.raise_for_status()
        content_type = response.headers.get("content-type", "").lower()
        if "application/json" in content_type:
            return response.json()
        return {"status_code": response.status_code, "text": response.text}
    
    except (requests.exceptions.RequestException, ValueError) as e:
        print(f"Request failed: {e}")
        return {"error": str(e)}

def get_error(result: Dict[str, Any]) -> str | None:
    """Return a normalized error string when a request/task failed."""
    error = result.get("error")
    if isinstance(error, str) and error.strip():
        return error
    if error:
        return str(error)
    return None

def wait_for_task_completion(task_id: str, max_wait: int = 300) -> Dict[str, Any]:
    """Wait for a task to complete and return the result."""
    print(f"Waiting for task {task_id} to complete...")
    
    start_time = time.time()
    while time.time() - start_time < max_wait:
        result = make_request(f"/nuclei/tasks/{task_id}")
        
        if result.get("status") in ["SUCCESS", "FAILURE"]:
            print(f"Task {task_id} completed with status: {result.get('status')}")
            return result
        
        print(f"Task {task_id} status: {result.get('status')}")
        time.sleep(5)
    
    print(f"Task {task_id} timed out after {max_wait} seconds")
    return {"error": "Task timed out"}

def test_comprehensive_scan():
    """Test the comprehensive scan endpoint with different scan types."""
    print("\n" + "="*60)
    print("TESTING COMPREHENSIVE SCAN ENDPOINT")
    print("="*60)
    
    scan_types = [
        {
            "name": "Auto Scan",
            "scan_type": "auto",
            "target": "example.com",
            "use_fingerprinting": True
        },
        {
            "name": "Fingerprint Scan",
            "scan_type": "fingerprint",
            "target": "google.com",
            "templates": ["http/", "cves/"]
        },
        {
            "name": "AI Scan",
            "scan_type": "ai",
            "target": "example.com",
            "prompt": "Scan for XSS vulnerabilities and SQL injection"
        },
        {
            "name": "Standard Scan",
            "scan_type": "standard",
            "target": "google.com",
            "templates": ["http/"]
        }
    ]
    
    for scan_config in scan_types:
        print(f"\n--- Testing {scan_config['name']} ---")
        
        # Prepare scan request
        scan_request = {
            "target": scan_config["target"],
            "scan_type": scan_config["scan_type"]
        }
        
        # Add optional parameters
        if "templates" in scan_config:
            scan_request["templates"] = scan_config["templates"]
        if "prompt" in scan_config:
            scan_request["prompt"] = scan_config["prompt"]
        if "use_fingerprinting" in scan_config:
            scan_request["use_fingerprinting"] = scan_config["use_fingerprinting"]
        
        # Make request
        result = make_request("/nuclei/scans", "POST", scan_request)
        
        if not get_error(result):
            task_id = result.get("task_id")
            print(f"✅ {scan_config['name']} started successfully")
            print(f"   Task ID: {task_id}")
            print(f"   Message: {result.get('message')}")
            
            if WAIT_FOR_COMPLETION:
                task_result = wait_for_task_completion(task_id)
                task_error = get_error(task_result)
                if not task_error:
                    print(f"   Result: {json.dumps(task_result.get('result', {}), indent=2)}")
                else:
                    record_failure(scan_config["name"], task_error)
        else:
            record_failure(scan_config["name"], get_error(result) or "Unknown request error")

def test_individual_scan_endpoints():
    """Test individual scan endpoints."""
    print("\n" + "="*60)
    print("TESTING INDIVIDUAL SCAN ENDPOINTS")
    print("="*60)
    
    # Test auto scan
    print("\n--- Testing Auto Scan Endpoint ---")
    auto_scan_data = {
        "target": "example.com",
        "templates": ["http/", "cves/"],
        "use_fingerprinting": True
    }
    result = make_request("/nuclei/scans", "POST", {"scan_type": "auto", **auto_scan_data})
    if not get_error(result):
        print(f"✅ Auto scan started: {result.get('task_id')}")
    else:
        record_failure("Auto Scan Endpoint", get_error(result) or "Unknown request error")
    
    # Test fingerprint scan
    print("\n--- Testing Fingerprint Scan Endpoint ---")
    fingerprint_data = {
        "target": "google.com",
        "templates": ["http/"]
    }
    result = make_request("/nuclei/scans", "POST", {"scan_type": "fingerprint", **fingerprint_data})
    if not get_error(result):
        print(f"✅ Fingerprint scan started: {result.get('task_id')}")
    else:
        record_failure("Fingerprint Scan Endpoint", get_error(result) or "Unknown request error")
    
    # Test AI scan
    print("\n--- Testing AI Scan Endpoint ---")
    ai_scan_data = {
        "target": "example.com",
        "prompt": "Find open ports and common vulnerabilities"
    }
    result = make_request("/nuclei/scans/ai", "POST", ai_scan_data)
    if not get_error(result):
        print(f"✅ AI scan started: {result.get('task_id')}")
    else:
        record_failure("AI Scan Endpoint", get_error(result) or "Unknown request error")

def test_fingerprinting():
    """Test fingerprinting functionality."""
    print("\n" + "="*60)
    print("TESTING FINGERPRINTING")
    print("="*60)
    
    for target in TEST_TARGETS:
        print(f"\n--- Fingerprinting {target} ---")
        
        fingerprint_data = {"target": target}
        result = make_request("/nuclei/fingerprints", "POST", fingerprint_data)
        
        if not get_error(result):
            task_id = result.get("task_id")
            print(f"✅ Fingerprinting started for {target}")
            print(f"   Task ID: {task_id}")
            print("   Background fingerprint scan accepted (completion check skipped by design)")
        else:
            record_failure(f"Fingerprint {target}", get_error(result) or "Unknown request error")

def test_template_validation():
    """Test template validation functionality."""
    print("\n" + "="*60)
    print("TESTING TEMPLATE VALIDATION")
    print("="*60)
    
    # Valid template
    valid_template = """
id: test-template
info:
  name: Test Template
  author: test
  severity: medium
  description: Test template for validation
requests:
  - method: GET
    path:
      - "{{BaseURL}}/test"
    matchers:
      - type: word
        words:
          - "test"
        part: body
"""
    
    # Invalid template
    invalid_template = """
id: invalid-template
info:
  name: Invalid Template
  # Missing required fields
requests:
  # Invalid structure
"""
    
    templates_to_test = [
        {"name": "Valid Template", "content": valid_template, "expected": True},
        {"name": "Invalid Template", "content": invalid_template, "expected": False}
    ]
    
    for template_test in templates_to_test:
        print(f"\n--- Testing {template_test['name']} ---")
        
        # Encode template content
        encoded_content = base64.b64encode(template_test["content"].encode()).decode()
        
        validation_data = {
            "template_content": encoded_content,
            "template_filename": f"{template_test['name'].lower().replace(' ', '-')}.yaml"
        }
        
        result = make_request("/nuclei/templates/validate", "POST", validation_data)
        
        if not get_error(result):
            task_id = result.get("task_id")
            print(f"✅ Template validation started")
            print(f"   Task ID: {task_id}")
            
            if WAIT_FOR_COMPLETION:
                task_result = wait_for_task_completion(task_id)
                task_error = get_error(task_result)
                if not task_error:
                    validation_result = task_result.get("result", {})
                    is_valid = validation_result.get("status") == "success"
                    print(f"   Is Valid: {is_valid}")
                    if not is_valid:
                        print(f"   Error: {validation_result.get('error', 'Unknown error')}")
                    
                    if is_valid == template_test["expected"]:
                        print(f"   ✅ Expected result: {template_test['expected']}")
                    else:
                        record_failure(
                            f"Template Validation {template_test['name']}",
                            f"expected {template_test['expected']}, got {is_valid}"
                        )
                else:
                    record_failure(f"Template Validation {template_test['name']}", task_error)
        else:
            record_failure(f"Template Validation {template_test['name']}", get_error(result) or "Unknown request error")

def test_custom_template_scan():
    """Test custom template scan functionality."""
    print("\n" + "="*60)
    print("TESTING CUSTOM TEMPLATE SCAN")
    print("="*60)
    
    # Create a simple custom template
    custom_template = """
id: custom-test-template
info:
  name: Custom Test Template
  author: test-user
  severity: low
  description: Custom template for testing
requests:
  - method: GET
    path:
      - "{{BaseURL}}/"
    matchers:
      - type: word
        words:
          - "html"
        part: body
        condition: or
"""
    
    # Encode template content
    encoded_content = base64.b64encode(custom_template.encode()).decode()
    
    custom_scan_data = {
        "target": "example.com",
        "scan_type": "custom",
        "template_content": encoded_content,
        "template_file": "custom-test-template.yaml"
    }
    
    result = make_request("/nuclei/scans", "POST", custom_scan_data)
    
    if not get_error(result):
        task_id = result.get("task_id")
        print(f"✅ Custom template scan started")
        print(f"   Task ID: {task_id}")
        print(f"   Target: {custom_scan_data['target']}")
        print(f"   Template: custom-test-template.yaml")
        
        if WAIT_FOR_COMPLETION:
            task_result = wait_for_task_completion(task_id)
            task_error = get_error(task_result)
            if not task_error:
                print(f"   Result: {json.dumps(task_result.get('result', {}), indent=2)}")
            else:
                record_failure("Custom Template Scan", task_error)
    else:
        record_failure("Custom Template Scan", get_error(result) or "Unknown request error")

def test_legacy_endpoints():
    """Test legacy endpoints for backward compatibility."""
    print("\n" + "="*60)
    print("TESTING LEGACY ENDPOINTS")
    print("="*60)
    
    # Test legacy scan endpoint
    print("\n--- Testing Legacy Scan Endpoint ---")
    legacy_scan_data = {
        "target": "example.com",
        "templates": ["http/"]
    }
    result = make_request("/nuclei/scan", "POST", legacy_scan_data)
    if not get_error(result):
        print(f"✅ Legacy scan started: {result.get('task_id')}")
    else:
        record_failure("Legacy Scan Endpoint", get_error(result) or "Unknown request error")
    
    # AI endpoint
    print("\n--- Testing AI Scan Endpoint ---")
    ai_data = {
        "target": "google.com",
        "prompt": "Find common web vulnerabilities"
    }
    result = make_request("/nuclei/scans/ai", "POST", ai_data)
    if not get_error(result):
        print(f"✅ AI scan started: {result.get('task_id')}")
    else:
        record_failure("AI Endpoint", get_error(result) or "Unknown request error")

def test_template_upload():
    """Test template upload functionality."""
    print("\n" + "="*60)
    print("TESTING TEMPLATE UPLOAD")
    print("="*60)
    
    # Create a test template file
    test_template_content = """
id: uploaded-test-template
info:
  name: Uploaded Test Template
  author: test-upload
  severity: medium
  description: Template uploaded via API
requests:
  - method: GET
    path:
      - "{{BaseURL}}/upload-test"
    matchers:
      - type: word
        words:
          - "upload"
        part: body
"""
    
    # Create temporary file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
        temp_file.write(test_template_content)
        temp_file_path = temp_file.name
    
    try:
        # Upload template
        with open(temp_file_path, 'rb') as f:
            files = {'template_file': ('test-template.yaml', f, 'application/x-yaml')}
            result = make_request("/nuclei/templates/upload", "POST", files=files)
        
        if not get_error(result):
            print(f"✅ Template uploaded successfully")
            print(f"   Filename: {result.get('filename')}")
            print(f"   Message: {result.get('message')}")
        else:
            record_failure("Template Upload", get_error(result) or "Unknown request error")
    
    finally:
        # Clean up temporary file
        import os
        try:
            os.unlink(temp_file_path)
        except:
            pass

def main():
    """Main test function."""
    print("🧪 COMPREHENSIVE NUCLEI API TEST SUITE")
    print("Testing enhanced scan functionality with all scan types")
    
    # Check if API is available
    try:
        health_check = make_request("/")
        if get_error(health_check):
            print("❌ API is not available. Please ensure the server is running.")
            sys.exit(1)
        if health_check.get("ping") != "pong!":
            print(f"❌ API ping returned unexpected payload: {health_check}")
            sys.exit(1)
        print("✅ API is available")
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        sys.exit(1)
    
    # Run all tests
    test_comprehensive_scan()
    test_individual_scan_endpoints()
    test_fingerprinting()
    test_template_validation()
    test_custom_template_scan()
    test_legacy_endpoints()
    test_template_upload()

    if FAILED_SCENARIOS:
        print("\nFailures:")
        for idx, failure in enumerate(FAILED_SCENARIOS, 1):
            print(f"{idx}. {failure['name']}: {failure['detail']}")
        sys.exit(1)

    print("\n✅ All scenario checks passed")
    sys.exit(0)

if __name__ == "__main__":
    main() 
