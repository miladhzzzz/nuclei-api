import requests
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class FingerprintController:
    def __init__(self):
        self.fingerprint_url = "http://nuclei-fingerprint:3000/"
        
    def fingerprint_target(self, target: str) -> Optional[str]:
        """Basic fingerprinting using the fingerprint service"""
        data = {
            "ip": target,
            "scanType": "quickOsAndPorts"
        }
        headers = {'Content-Type': 'application/json'}
        try:
            response = requests.post(self.fingerprint_url + "scan/ip/", json=data, headers=headers, timeout=2000)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": f"Request failed with status {e.response.status_code if e.response else 'unknown'}"}
    
    def comprehensive_fingerprint(self, target: str) -> Dict:
        """Comprehensive fingerprinting using the fingerprint service"""
        data = {
            "ip": target,
            "scanType": "aggressiveOsAndPort"
        }
        headers = {'Content-Type': 'application/json'}
        try:
            response = requests.post(self.fingerprint_url + "scan/ip/", json=data, headers=headers, timeout=3000)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": f"Request failed with status {e.response.status_code if e.response else 'unknown'}"}
    
    def get_os_family(self, fingerprint_result: Dict) -> str:
        """Extract OS family from fingerprint result"""
        try:
            if "data" in fingerprint_result and fingerprint_result["data"]:
                # Parse nmap output to determine OS family
                nmap_output = str(fingerprint_result["data"])
                
                if any(os_name in nmap_output.lower() for os_name in ['windows', 'microsoft']):
                    return "windows"
                elif any(os_name in nmap_output.lower() for os_name in ['linux', 'ubuntu', 'debian', 'centos', 'redhat', 'fedora']):
                    return "linux"
                elif any(os_name in nmap_output.lower() for os_name in ['macos', 'darwin', 'apple']):
                    return "macos"
                elif any(os_name in nmap_output.lower() for os_name in ['bsd', 'freebsd', 'openbsd']):
                    return "bsd"
            
            return "unknown"
        except Exception as e:
            logger.error(f"Error extracting OS family: {e}")
            return "unknown"
    
    def get_open_ports(self, fingerprint_result: Dict) -> list:
        """Extract open ports from fingerprint result"""
        try:
            open_ports = []
            if "data" in fingerprint_result and fingerprint_result["data"]:
                # Parse nmap output to extract open ports
                nmap_output = str(fingerprint_result["data"])
                
                # Simple regex to find open ports (this is a basic implementation)
                import re
                port_matches = re.findall(r'(\d+)/tcp\s+open', nmap_output)
                for port in port_matches:
                    open_ports.append(int(port))
            
            return open_ports
        except Exception as e:
            logger.error(f"Error extracting open ports: {e}")
            return []
    
    def get_services(self, fingerprint_result: Dict) -> list:
        """Extract services from fingerprint result"""
        try:
            services = []
            if "data" in fingerprint_result and fingerprint_result["data"]:
                # Parse nmap output to extract services
                nmap_output = str(fingerprint_result["data"])
                
                # Simple regex to find services (this is a basic implementation)
                import re
                service_matches = re.findall(r'(\d+)/tcp\s+open\s+(\w+)', nmap_output)
                for port, service in service_matches:
                    services.append({
                        "port": int(port),
                        "service": service
                    })
            
            return services
        except Exception as e:
            logger.error(f"Error extracting services: {e}")
            return []