import os
import requests
import pytest

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

@pytest.mark.integration
def test_run_scan_success():
    response = requests.post(
        f"{BASE_URL}/nuclei/scans",
        json={"target": "178.18.206.181", "scan_type": "standard", "templates": ["cves/", "network/"]}
    )
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert "message" in data

@pytest.mark.integration
def test_run_scan_invalid_target():
    response = requests.post(
        f"{BASE_URL}/nuclei/scans",
        json={"target": "invalid_target", "scan_type": "standard", "templates": ["cves/"]}
    )
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data

@pytest.mark.integration
def test_run_scan_with_prompt():
    response = requests.post(
        f"{BASE_URL}/nuclei/scans/ai",
        json={"target": "178.18.206.181", "prompt": "Generate a template for XSS"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert "message" in data

# @pytest.mark.integration
# def test_template_upload():
#     url = f"{BASE_URL}/nuclei/templates/upload"
#     file_path = os.getenv("TEST_TEMPLATE_PATH", "tests/assets/test_template.yaml")
#     if not os.path.exists(file_path):
#         pytest.skip("Test template file not found.")
#     with open(file_path, "rb") as f:
#         files = {"template_file": f}
#         response = requests.post(url, files=files)
#     assert response.status_code in (200, 400)  # Accept 400 for invalid template
#     data = response.json()
#     assert "template_name" in data or "detail" in data 
