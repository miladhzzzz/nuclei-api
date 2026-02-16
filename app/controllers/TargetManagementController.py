import json
import logging
import redis
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import ipaddress
import random
import asyncio
import aiohttp
from urllib.parse import urlparse
import dns.resolver
from helpers.config import Config

logger = logging.getLogger(__name__)

class TargetManagementController:
    def __init__(self):
        conf = Config()
        self.redis_client = redis.Redis.from_url(conf.redis_url, decode_responses=True)
        self.target_db_key = "vulnerable_targets"
        self.target_metadata_key = "target_metadata"
        self.target_test_results_key = "target_test_results"
        
    def add_target(self, target: Dict[str, Any]) -> bool:
        """Add a discovered target to the target database"""
        try:
            target_id = self._generate_target_id(target)
            target["id"] = target_id
            target["discovered_at"] = datetime.now().isoformat()
            target["last_tested"] = None
            target["test_count"] = 0
            target["success_rate"] = 0.0
            
            # Store target data
            self.redis_client.hset(self.target_db_key, target_id, json.dumps(target))
            
            # Store metadata for quick lookups
            metadata = {
                "ip": target.get("ip"),
                "domain": target.get("domain"),
                "service": target.get("service"),
                "product": target.get("product"),
                "vulnerabilities": target.get("vulnerabilities", []),
                "discovery_source": target.get("discovery_source"),
                "confidence_score": target.get("confidence_score", 0.0)
            }
            self.redis_client.hset(self.target_metadata_key, target_id, json.dumps(metadata))
            
            logger.info(f"Added target {target_id} to database")
            return True
            
        except Exception as e:
            logger.error(f"Error adding target: {e}")
            return False
    
    def get_target(self, target_id: str) -> Optional[Dict]:
        """Get a specific target by ID"""
        try:
            target_data = self.redis_client.hget(self.target_db_key, target_id)
            if target_data:
                return json.loads(target_data)
            return None
        except Exception as e:
            logger.error(f"Error getting target {target_id}: {e}")
            return None
    
    def get_targets_by_criteria(self, criteria: Dict[str, Any]) -> List[Dict]:
        """Get targets matching specific criteria"""
        try:
            all_targets = self.redis_client.hgetall(self.target_db_key)
            matching_targets = []
            
            for target_id, target_data in all_targets.items():
                target = json.loads(target_data)
                
                # Check if target matches all criteria
                matches = True
                for key, value in criteria.items():
                    if key == "vulnerabilities":
                        # Check if any vulnerability matches
                        target_vulns = target.get("vulnerabilities", [])
                        if isinstance(value, list):
                            if not any(vuln in target_vulns for vuln in value):
                                matches = False
                        else:
                            if value not in target_vulns:
                                matches = False
                    elif key == "service":
                        # Check service type
                        if target.get("service") != value:
                            matches = False
                    elif key == "product":
                        # Check product name (case insensitive)
                        if target.get("product", "").lower() != value.lower():
                            matches = False
                    elif key == "discovery_source":
                        # Check discovery source
                        if target.get("discovery_source") != value:
                            matches = False
                    elif key == "min_confidence":
                        # Check minimum confidence score
                        if target.get("confidence_score", 0) < value:
                            matches = False
                    elif key == "max_confidence":
                        # Check maximum confidence score
                        if target.get("confidence_score", 0) > value:
                            matches = False
                    else:
                        # Direct field comparison
                        if target.get(key) != value:
                            matches = False
                
                if matches:
                    matching_targets.append(target)
            
            return matching_targets
            
        except Exception as e:
            logger.error(f"Error getting targets by criteria: {e}")
            return []
    
    def get_targets_for_testing(self, limit: int = 10, min_confidence: float = 0.5) -> List[Dict]:
        """Get targets suitable for testing (high confidence, not recently tested)"""
        try:
            all_targets = self.redis_client.hgetall(self.target_db_key)
            suitable_targets = []
            
            for target_id, target_data in all_targets.items():
                target = json.loads(target_data)
                
                # Check confidence score
                if target.get("confidence_score", 0) < min_confidence:
                    continue
                
                # Check if not tested recently (within last 24 hours)
                last_tested = target.get("last_tested")
                if last_tested:
                    last_tested_dt = datetime.fromisoformat(last_tested)
                    if datetime.now() - last_tested_dt < timedelta(hours=24):
                        continue
                
                suitable_targets.append(target)
            
            # Sort by confidence score (highest first) and limit results
            suitable_targets.sort(key=lambda x: x.get("confidence_score", 0), reverse=True)
            return suitable_targets[:limit]
            
        except Exception as e:
            logger.error(f"Error getting targets for testing: {e}")
            return []
    
    def update_target_test_result(self, target_id: str, test_result: Dict[str, Any]) -> bool:
        """Update target with test results"""
        try:
            target = self.get_target(target_id)
            if not target:
                return False
            
            # Update test statistics
            target["test_count"] = target.get("test_count", 0) + 1
            target["last_tested"] = datetime.now().isoformat()
            
            # Calculate success rate
            test_results = self.get_target_test_results(target_id)
            test_results.append(test_result)
            
            # Keep only last 10 test results
            if len(test_results) > 10:
                test_results = test_results[-10:]
            
            # Calculate success rate
            successful_tests = sum(1 for result in test_results if result.get("success", False))
            target["success_rate"] = successful_tests / len(test_results) if test_results else 0.0
            
            # Store updated target
            self.redis_client.hset(self.target_db_key, target_id, json.dumps(target))
            
            # Store test results
            self.redis_client.hset(self.target_test_results_key, target_id, json.dumps(test_results))
            
            logger.info(f"Updated target {target_id} with test result")
            return True
            
        except Exception as e:
            logger.error(f"Error updating target test result: {e}")
            return False
    
    def get_target_test_results(self, target_id: str) -> List[Dict]:
        """Get test results for a specific target"""
        try:
            results_data = self.redis_client.hget(self.target_test_results_key, target_id)
            if results_data:
                return json.loads(results_data)
            return []
        except Exception as e:
            logger.error(f"Error getting test results for target {target_id}: {e}")
            return []
    
    def remove_target(self, target_id: str) -> bool:
        """Remove a target from the database"""
        try:
            # Remove from all storage locations
            self.redis_client.hdel(self.target_db_key, target_id)
            self.redis_client.hdel(self.target_metadata_key, target_id)
            self.redis_client.hdel(self.target_test_results_key, target_id)
            
            logger.info(f"Removed target {target_id} from database")
            return True
            
        except Exception as e:
            logger.error(f"Error removing target {target_id}: {e}")
            return False
    
    def get_target_statistics(self) -> Dict[str, Any]:
        """Get statistics about stored targets"""
        try:
            all_targets = self.redis_client.hgetall(self.target_db_key)
            
            if not all_targets:
                return {
                    "total_targets": 0,
                    "by_service": {},
                    "by_discovery_source": {},
                    "by_confidence": {"high": 0, "medium": 0, "low": 0},
                    "average_confidence": 0.0,
                    "average_success_rate": 0.0
                }
            
            stats = {
                "total_targets": len(all_targets),
                "by_service": {},
                "by_discovery_source": {},
                "by_confidence": {"high": 0, "medium": 0, "low": 0},
                "total_confidence": 0.0,
                "total_success_rate": 0.0
            }
            
            for target_id, target_data in all_targets.items():
                target = json.loads(target_data)
                
                # Service breakdown
                service = target.get("service", "unknown")
                stats["by_service"][service] = stats["by_service"].get(service, 0) + 1
                
                # Discovery source breakdown
                source = target.get("discovery_source", "unknown")
                stats["by_discovery_source"][source] = stats["by_discovery_source"].get(source, 0) + 1
                
                # Confidence breakdown
                confidence = target.get("confidence_score", 0.0)
                stats["total_confidence"] += confidence
                
                if confidence >= 0.8:
                    stats["by_confidence"]["high"] += 1
                elif confidence >= 0.5:
                    stats["by_confidence"]["medium"] += 1
                else:
                    stats["by_confidence"]["low"] += 1
                
                # Success rate
                success_rate = target.get("success_rate", 0.0)
                stats["total_success_rate"] += success_rate
            
            # Calculate averages
            stats["average_confidence"] = stats["total_confidence"] / len(all_targets)
            stats["average_success_rate"] = stats["total_success_rate"] / len(all_targets)
            
            # Remove totals from final stats
            del stats["total_confidence"]
            del stats["total_success_rate"]
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting target statistics: {e}")
            return {"error": str(e)}
    
    def cleanup_old_targets(self, days_old: int = 30) -> int:
        """Remove targets that haven't been tested recently"""
        try:
            all_targets = self.redis_client.hgetall(self.target_db_key)
            cutoff_date = datetime.now() - timedelta(days=days_old)
            removed_count = 0
            
            for target_id, target_data in all_targets.items():
                target = json.loads(target_data)
                discovered_at = target.get("discovered_at")
                
                if discovered_at:
                    discovered_dt = datetime.fromisoformat(discovered_at)
                    if discovered_dt < cutoff_date:
                        if self.remove_target(target_id):
                            removed_count += 1
            
            logger.info(f"Cleaned up {removed_count} old targets")
            return removed_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old targets: {e}")
            return 0
    
    def _generate_target_id(self, target: Dict[str, Any]) -> str:
        """Generate a unique target ID"""
        ip = target.get("ip", "")
        port = target.get("port", "")
        service = target.get("service", "")
        
        # Create a hash-based ID
        import hashlib
        id_string = f"{ip}:{port}:{service}:{datetime.now().timestamp()}"
        return hashlib.md5(id_string.encode()).hexdigest()[:12]
    
    async def discover_targets_from_network(self, network_range: str, ports: List[int] = None) -> List[Dict]:
        """Discover targets from a network range using port scanning"""
        if ports is None:
            ports = [80, 443, 22, 21, 3306, 5432, 8080, 8443]
        
        discovered_targets = []
        
        try:
            # Parse network range
            network = ipaddress.IPv4Network(network_range, strict=False)
            
            # Limit the number of hosts to scan
            hosts_to_scan = list(network.hosts())[:50]  # Limit to 50 hosts
            
            for host in hosts_to_scan:
                host_ip = str(host)
                
                # Simulate port scanning (in real implementation, use nmap)
                open_ports = random.sample(ports, random.randint(0, 3))  # 0-3 open ports per host
                
                for port in open_ports:
                    target = {
                        "ip": host_ip,
                        "port": port,
                        "service": self._get_service_name(port),
                        "discovery_source": "network_scan",
                        "discovery_method": "port_scanning",
                        "confidence_score": random.uniform(0.7, 1.0),
                        "network_range": network_range
                    }
                    
                    discovered_targets.append(target)
                    
        except Exception as e:
            logger.error(f"Error discovering targets from network {network_range}: {e}")
        
        return discovered_targets
    
    def _get_service_name(self, port: int) -> str:
        """Get service name for common ports"""
        service_map = {
            21: "ftp",
            22: "ssh",
            23: "telnet",
            25: "smtp",
            53: "dns",
            80: "http",
            110: "pop3",
            143: "imap",
            443: "https",
            993: "imaps",
            995: "pop3s",
            3306: "mysql",
            3389: "rdp",
            5432: "postgresql",
            8080: "http-proxy",
            8443: "https-alt"
        }
        return service_map.get(port, "unknown")
    
    async def validate_target_connectivity(self, target: Dict[str, Any]) -> Dict[str, Any]:
        """Validate if a target is still reachable and vulnerable"""
        validation_result = {
            "target_id": target.get("id"),
            "reachable": False,
            "service_responding": False,
            "vulnerability_confirmed": False,
            "validation_time": datetime.now().isoformat(),
            "details": {}
        }
        
        try:
            ip = target.get("ip")
            port = target.get("port", 80)
            service = target.get("service", "http")
            
            # Basic connectivity check
            connectivity = await self._check_connectivity(ip, port)
            validation_result["reachable"] = connectivity.get("reachable", False)
            validation_result["details"]["connectivity"] = connectivity
            
            if connectivity.get("reachable", False):
                # Service validation
                service_validation = await self._validate_service(ip, port, service)
                validation_result["service_responding"] = service_validation.get("service_running", False)
                validation_result["details"]["service"] = service_validation
                
                # Vulnerability validation (simplified)
                if target.get("vulnerabilities"):
                    vuln_validation = await self._validate_vulnerabilities(ip, port, target["vulnerabilities"])
                    validation_result["vulnerability_confirmed"] = any(
                        vuln.get("exists", False) for vuln in vuln_validation.values()
                    )
                    validation_result["details"]["vulnerabilities"] = vuln_validation
                
        except Exception as e:
            logger.error(f"Error validating target connectivity: {e}")
            validation_result["error"] = str(e)
        
        return validation_result
    
    async def _check_connectivity(self, ip: str, port: int) -> Dict:
        """Check if target is reachable"""
        try:
            # Use asyncio to check connectivity
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port),
                timeout=5.0
            )
            writer.close()
            await writer.wait_closed()
            
            return {
                "reachable": True,
                "response_time": 0.1  # Placeholder
            }
        except Exception as e:
            return {
                "reachable": False,
                "error": str(e)
            }
    
    async def _validate_service(self, ip: str, port: int, service: str) -> Dict:
        """Validate if the expected service is running"""
        try:
            # Basic service validation
            if service in ["http", "https"]:
                protocol = "https" if service == "https" else "http"
                url = f"{protocol}://{ip}:{port}"
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=10) as response:
                        return {
                            "service_running": True,
                            "response_code": response.status,
                            "server_header": response.headers.get("Server", ""),
                            "content_type": response.headers.get("Content-Type", "")
                        }
            else:
                # For non-HTTP services, just check if port is open
                return {
                    "service_running": True,
                    "port_open": True
                }
                
        except Exception as e:
            return {
                "service_running": False,
                "error": str(e)
            }
    
    async def _validate_vulnerabilities(self, ip: str, port: int, vulnerabilities: List[str]) -> Dict:
        """Validate if specific vulnerabilities exist"""
        validation_results = {}
        
        for vuln in vulnerabilities:
            try:
                # This would integrate with actual vulnerability scanning
                # For now, we'll simulate validation
                validation_results[vuln] = {
                    "exists": random.choice([True, False]),
                    "confidence": random.uniform(0.5, 1.0),
                    "details": f"Simulated validation for {vuln}"
                }
            except Exception as e:
                validation_results[vuln] = {
                    "exists": False,
                    "error": str(e)
                }
        
        return validation_results 
