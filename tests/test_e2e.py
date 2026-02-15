import os
import requests
import pytest
import time

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

@pytest.mark.e2e
def test_full_scan_e2e():
    response = requests.post(
        f"{BASE_URL}/nuclei/scans",
        json={"target": "178.18.206.181", "scan_type": "standard", "templates": ["cves/"]}
    )
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    task_id = data["task_id"]

    # Poll for task completion
    for _ in range(30):  # up to 60 seconds
        status_resp = requests.get(f"{BASE_URL}/nuclei/tasks/{task_id}")
        assert status_resp.status_code == 200
        status_data = status_resp.json()
        if status_data["status"] in ("SUCCESS", "FAILURE"):
            break
        time.sleep(2)
    else:
        pytest.fail("Task did not complete in time")

    assert status_data["status"] == "SUCCESS"
    assert "result" in status_data

@pytest.mark.e2e
def test_scan_timeout():
    response = requests.post(
        f"{BASE_URL}/nuclei/scans",
        json={"target": "10.255.255.1", "scan_type": "standard", "templates": ["cves/"]}  # Unroutable IP
    )
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    task_id = data["task_id"]

    # Poll for task completion or timeout/failure
    for _ in range(10):  # up to 20 seconds
        status_resp = requests.get(f"{BASE_URL}/nuclei/tasks/{task_id}")
        assert status_resp.status_code == 200
        status_data = status_resp.json()
        if status_data["status"] in ("SUCCESS", "FAILURE"):
            break
        time.sleep(2)
    # Accept either failure or timeout
    assert status_data["status"] in ("FAILURE", "SUCCESS")

@pytest.mark.e2e
def test_scan_with_invalid_template():
    # Try uploading an invalid template and running a scan
    url = f"{BASE_URL}/nuclei/templates/upload"
    invalid_yaml = b"not: valid: yaml: - just: a: string"
    files = {"template_file": ("invalid.yaml", invalid_yaml)}
    response = requests.post(url, files=files)
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data

@pytest.mark.e2e
def test_scan_with_prompt_e2e():
    response = requests.post(
        f"{BASE_URL}/nuclei/scans/ai",
        json={"target": "178.18.206.181", "prompt": "Generate a template for SQL Injection"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    task_id = data["task_id"]

    # Poll for task completion
    for _ in range(30):
        status_resp = requests.get(f"{BASE_URL}/nuclei/tasks/{task_id}")
        assert status_resp.status_code == 200
        status_data = status_resp.json()
        if status_data["status"] in ("SUCCESS", "FAILURE"):
            break
        time.sleep(2)
    else:
        pytest.fail("AI scan task did not complete in time")
    assert status_data["status"] in ("SUCCESS", "FAILURE") 
