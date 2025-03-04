import aiohttp

class FingerprintController:
    def __init__(self):
        self.fingerprint_url = "http://localhost:3330/"

    async def fingerprint_target(self, target: str):
        data = {
            "ip": target,
            "scanType": "quickOsAndPorts"
        }
        headers = {'Content-Type': 'application/json'}
        async with aiohttp.ClientSession() as session:
            async with session.post(self.fingerprint_url + "scan/ip/", json=data, headers=headers, timeout=2000) as response:
                if response.status == 200:
                    return await response.json()
                return {"error": f"Request failed with status {response.status}"}