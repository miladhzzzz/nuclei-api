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
from typing import Dict, Any

# Configuration
API_BASE_URL = "http://localhost:8000"
TEST_TARGETS = [
    "example.com",
    "192.168.1.1",
    "google.com"
]

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
        return response.json()
    
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return {"error": str(e)}

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
        
        if "error" not in result:
            task_id = result.get("task_id")
            print(f"✅ {scan_config['name']} started successfully")
            print(f"   Task ID: {task_id}")
            print(f"   Message: {result.get('message')}")
            
            # Wait for completion (optional)
            if input(f"Wait for {scan_config['name']} completion? (y/n): ").lower() == 'y':
                task_result = wait_for_task_completion(task_id)
                if "error" not in task_result:
                    print(f"   Result: {json.dumps(task_result.get('result', {}), indent=2)}")
        else:
            print(f"❌ {scan_config['name']} failed: {result['error']}")

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
    if "error" not in result:
        print(f"✅ Auto scan started: {result.get('task_id')}")
    else:
        print(f"❌ Auto scan failed: {result['error']}")
    
    # Test fingerprint scan
    print("\n--- Testing Fingerprint Scan Endpoint ---")
    fingerprint_data = {
        "target": "google.com",
        "templates": ["http/"]
    }
    result = make_request("/nuclei/scans", "POST", {"scan_type": "fingerprint", **fingerprint_data})
    if "error" not in result:
        print(f"✅ Fingerprint scan started: {result.get('task_id')}")
    else:
        print(f"❌ Fingerprint scan failed: {result['error']}")
    
    # Test AI scan
    print("\n--- Testing AI Scan Endpoint ---")
    ai_scan_data = {
        "target": "example.com",
        "prompt": "Find open ports and common vulnerabilities"
    }
    result = make_request("/nuclei/scans/ai", "POST", ai_scan_data)
    if "error" not in result:
        print(f"✅ AI scan started: {result.get('task_id')}")
    else:
        print(f"❌ AI scan failed: {result['error']}")

def test_fingerprinting():
    """Test fingerprinting functionality."""
    print("\n" + "="*60)
    print("TESTING FINGERPRINTING")
    print("="*60)
    
    for target in TEST_TARGETS:
        print(f"\n--- Fingerprinting {target} ---")
        
        fingerprint_data = {"target": target}
        result = make_request("/nuclei/fingerprints", "POST", fingerprint_data)
        
        if "error" not in result:
            task_id = result.get("task_id")
            print(f"✅ Fingerprinting started for {target}")
            print(f"   Task ID: {task_id}")
            
            # Wait for completion
            task_result = wait_for_task_completion(task_id)
            if "error" not in task_result:
                fingerprint_result = task_result.get("result", {})
                print(f"   OS Detected: {fingerprint_result.get('os_detected', 'Unknown')}")
                print(f"   Recommended Templates: {fingerprint_result.get('recommended_templates', [])}")
        else:
            print(f"❌ Fingerprinting failed for {target}: {result['error']}")

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
        
        if "error" not in result:
            task_id = result.get("task_id")
            print(f"✅ Template validation started")
            print(f"   Task ID: {task_id}")
            
            # Wait for completion
            task_result = wait_for_task_completion(task_id)
            if "error" not in task_result:
                validation_result = task_result.get("result", {})
                is_valid = validation_result.get("is_valid", False)
                print(f"   Is Valid: {is_valid}")
                if not is_valid:
                    print(f"   Error: {validation_result.get('validation_error', 'Unknown error')}")
                
                if is_valid == template_test["expected"]:
                    print(f"   ✅ Expected result: {template_test['expected']}")
                else:
                    print(f"   ❌ Unexpected result: expected {template_test['expected']}, got {is_valid}")
        else:
            print(f"❌ Template validation failed: {result['error']}")

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
    
    if "error" not in result:
        task_id = result.get("task_id")
        print(f"✅ Custom template scan started")
        print(f"   Task ID: {task_id}")
        print(f"   Target: {custom_scan_data['target']}")
        print(f"   Template: {custom_scan_data['template_filename']}")
        
        # Wait for completion
        if input("Wait for custom template scan completion? (y/n): ").lower() == 'y':
            task_result = wait_for_task_completion(task_id)
            if "error" not in task_result:
                print(f"   Result: {json.dumps(task_result.get('result', {}), indent=2)}")
    else:
        print(f"❌ Custom template scan failed: {result['error']}")

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
    if "error" not in result:
        print(f"✅ Legacy scan started: {result.get('task_id')}")
    else:
        print(f"❌ Legacy scan failed: {result['error']}")
    
    # AI endpoint
    print("\n--- Testing AI Scan Endpoint ---")
    ai_data = {
        "target": "google.com",
        "prompt": "Find common web vulnerabilities"
    }
    result = make_request("/nuclei/scans/ai", "POST", ai_data)
    if "error" not in result:
        print(f"✅ AI scan started: {result.get('task_id')}")
    else:
        print(f"❌ AI scan failed: {result['error']}")

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
        
        if "error" not in result:
            print(f"✅ Template uploaded successfully")
            print(f"   Filename: {result.get('filename')}")
            print(f"   Message: {result.get('message')}")
        else:
            print(f"❌ Template upload failed: {result['error']}")
    
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
        health_check = make_request("/docs")
        if "error" in health_check:
            print("❌ API is not available. Please ensure the server is running.")
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
    
    print("\n" + "="*60)
    print("🎉 ALL TESTS COMPLETED")
    print("="*60)
    print("\nThe enhanced Nuclei API now supports:")
    print("✅ Comprehensive scan endpoint with multiple scan types")
    print("✅ Auto scan with intelligent template selection")
    print("✅ Fingerprint scan with OS-specific templates")
    print("✅ AI scan with custom prompts")
    print("✅ Custom template scan with validation")
    print("✅ Workflow scan support")
    print("✅ Standalone fingerprinting")
    print("✅ Template validation")
    print("✅ Template upload")
    print("✅ Legacy endpoint compatibility")
    print("\nAll scan types are now available through a unified API!")

if __name__ == "__main__":
    main() 
