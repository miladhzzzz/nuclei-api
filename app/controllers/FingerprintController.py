import requests

class FingerprintController:
    def __init__(self):
        self.fingerprint_url = "http://nuclei-fingerprint:3000/"

    def fingerprint_target(self, target: str):
        data = {
            "ip": target,
            "scanType": "quickOsAndPorts"
        }
        headers = {'Content-Type': 'application/json'}
        try:
            response = requests.post(self.fingerprint_url + "scan/ip/", json=data, headers=headers, timeout=2000)
            response.raise_for_status()  # Raises an exception for 4xx/5xx status codes
            return response.json()
        except requests.RequestException as e:
            return {"error": f"Request failed with status {e.response.status_code if e.response else 'unknown'}"}