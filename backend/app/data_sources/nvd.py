import httpx
from typing import Optional, Dict, List, Any
from datetime import datetime
import logging
# from ..models.vulnerability import CVSSData  # Placeholder for future model

logger = logging.getLogger("vulnrisk.nvd")

class CVEData:
    """Rich CVE data extracted from NVD API."""
    def __init__(self, data: Dict[str, Any]):
        self.cve_id = data.get('cve_id')
        self.cvss_score = data.get('cvss_score')
        self.cvss_vector = data.get('cvss_vector')
        self.published_date = data.get('published_date')
        self.modified_date = data.get('modified_date')
        self.vulnerability_age_days = data.get('vulnerability_age_days', 0)
        self.description = data.get('description', '')
        self.cpe_configurations = data.get('cpe_configurations', [])
        self.references = data.get('references', [])
        self.cisa_kev = data.get('cisa_kev', False)
        self.has_exploit_references = data.get('has_exploit_references', False)
        self.attack_vector = data.get('attack_vector', 'NETWORK')  # NETWORK, ADJACENT_NETWORK, LOCAL, PHYSICAL
        self.attack_complexity = data.get('attack_complexity', 'LOW')  # LOW, HIGH
        self.privileges_required = data.get('privileges_required', 'NONE')  # NONE, LOW, HIGH
        self.user_interaction = data.get('user_interaction', 'NONE')  # NONE, REQUIRED
        self.scope = data.get('scope', 'UNCHANGED')  # UNCHANGED, CHANGED
        self.confidentiality_impact = data.get('confidentiality_impact', 'NONE')  # NONE, LOW, HIGH
        self.integrity_impact = data.get('integrity_impact', 'NONE')  # NONE, LOW, HIGH
        self.availability_impact = data.get('availability_impact', 'NONE')  # NONE, LOW, HIGH

class NVDClient:
    def __init__(self, api_key: Optional[str] = None):
        self.base_url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
        self.api_key = api_key
        self.client = httpx.AsyncClient()
        # CISA KEV list for cross-referencing
        self.cisa_kev_url = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
        self._cisa_kev_cache = None

    async def get_cvss_score(self, cve_id: str) -> Optional[float]:
        """Fetch CVSS score from NVD API for a given CVE ID."""
        cve_data = await self.get_rich_cve_data(cve_id)
        return cve_data.cvss_score if cve_data else None

    async def get_rich_cve_data(self, cve_id: str) -> Optional[CVEData]:
        """Fetch comprehensive CVE data from NVD API."""
        try:
            headers = {}
            if self.api_key:
                headers['apiKey'] = self.api_key

            response = await self.client.get(
                f"{self.base_url}",
                params={"cveId": cve_id},
                headers=headers
            )

            logger.info(f"NVD API status: {response.status_code}")
            try:
                logger.info(f"NVD API response: {response.text[:500]}")
            except Exception:
                pass

            if response.status_code == 200:
                data = response.json()
                return await self._parse_rich_cve_data(data, cve_id)
            return None
        except Exception as e:
            logger.error(f"Error fetching CVE data for {cve_id}: {e}")
            return None

    async def _parse_rich_cve_data(self, nvd_data: dict, cve_id: str) -> Optional[CVEData]:
        """Parse comprehensive CVE data from NVD response."""
        try:
            items = nvd_data.get("vulnerabilities", [])
            if not items:
                return None
            
            vuln_item = items[0]
            cve_info = vuln_item.get("cve", {})
            metrics = cve_info.get("metrics", {})
            
            # Extract CVSS data (prefer v3.1 > v3.0 > v2.0)
            cvss_data = None
            cvss_score = None
            cvss_vector = None
            
            for version in ["cvssMetricV31", "cvssMetricV30", "cvssMetricV2"]:
                if version in metrics:
                    cvss_data = metrics[version][0]["cvssData"]
                    cvss_score = cvss_data.get("baseScore")
                    cvss_vector = cvss_data.get("vectorString", "")
                    break
            
            if not cvss_score:
                return None
            
            # Extract dates and calculate age
            published_date = cve_info.get("published")
            modified_date = cve_info.get("lastModified")
            vulnerability_age_days = 0
            
            if published_date:
                pub_date = datetime.fromisoformat(published_date.replace('Z', '+00:00'))
                vulnerability_age_days = (datetime.now(pub_date.tzinfo) - pub_date).days
            
            # Extract description
            descriptions = cve_info.get("descriptions", [])
            description = ""
            for desc in descriptions:
                if desc.get("lang") == "en":
                    description = desc.get("value", "")
                    break
            
            # Extract CPE configurations
            cpe_configs = []
            configurations = vuln_item.get("configurations", [])
            for config in configurations:
                for node in config.get("nodes", []):
                    for cpe_match in node.get("cpeMatch", []):
                        if cpe_match.get("vulnerable", False):
                            cpe_configs.append(cpe_match.get("criteria", ""))
            
            # Extract references and check for exploit indicators
            references = []
            has_exploit_refs = False
            ref_list = cve_info.get("references", [])
            
            for ref in ref_list:
                ref_url = ref.get("url", "")
                references.append(ref_url)
                
                # Check for exploit-related references
                exploit_indicators = [
                    "exploit", "poc", "metasploit", "exploit-db", "exploitdb",
                    "github.com", "proof-of-concept", "vulnerability-lab"
                ]
                if any(indicator in ref_url.lower() for indicator in exploit_indicators):
                    has_exploit_refs = True
            
            # Check CISA KEV status
            cisa_kev = await self._check_cisa_kev(cve_id)
            
            # Extract CVSS vector components for intelligent context determination
            attack_vector = "NETWORK"
            attack_complexity = "LOW"
            privileges_required = "NONE"
            user_interaction = "NONE"
            scope = "UNCHANGED"
            confidentiality_impact = "NONE"
            integrity_impact = "NONE"
            availability_impact = "NONE"
            
            if cvss_data:
                attack_vector = cvss_data.get("attackVector", "NETWORK")
                attack_complexity = cvss_data.get("attackComplexity", "LOW")
                privileges_required = cvss_data.get("privilegesRequired", "NONE")
                user_interaction = cvss_data.get("userInteraction", "NONE")
                scope = cvss_data.get("scope", "UNCHANGED")
                confidentiality_impact = cvss_data.get("confidentialityImpact", "NONE")
                integrity_impact = cvss_data.get("integrityImpact", "NONE")
                availability_impact = cvss_data.get("availabilityImpact", "NONE")
            
            return CVEData({
                'cve_id': cve_id,
                'cvss_score': cvss_score,
                'cvss_vector': cvss_vector,
                'published_date': published_date,
                'modified_date': modified_date,
                'vulnerability_age_days': vulnerability_age_days,
                'description': description,
                'cpe_configurations': cpe_configs,
                'references': references,
                'cisa_kev': cisa_kev,
                'has_exploit_references': has_exploit_refs,
                'attack_vector': attack_vector,
                'attack_complexity': attack_complexity,
                'privileges_required': privileges_required,
                'user_interaction': user_interaction,
                'scope': scope,
                'confidentiality_impact': confidentiality_impact,
                'integrity_impact': integrity_impact,
                'availability_impact': availability_impact
            })
            
        except Exception as e:
            logger.error(f"Error parsing CVE data: {e}")
            return None

    async def _check_cisa_kev(self, cve_id: str) -> bool:
        """Check if CVE is in CISA Known Exploited Vulnerabilities catalog."""
        try:
            # Cache CISA KEV data to avoid repeated API calls
            if self._cisa_kev_cache is None:
                response = await self.client.get(self.cisa_kev_url)
                if response.status_code == 200:
                    kev_data = response.json()
                    self._cisa_kev_cache = set(
                        vuln.get("cveID", "") for vuln in kev_data.get("vulnerabilities", [])
                    )
                else:
                    self._cisa_kev_cache = set()
            
            return cve_id in self._cisa_kev_cache
            
        except Exception as e:
            logger.error(f"Error checking CISA KEV for {cve_id}: {e}")
            return False

    def _parse_cvss_score(self, nvd_data: dict) -> Optional[float]:
        """Legacy method for backward compatibility."""
        try:
            items = nvd_data.get("vulnerabilities", [])
            if not items:
                return None
            metrics = items[0].get("cve", {}).get("metrics", {})
            # Try CVSS v3.1, then v3.0, then v2.0
            for version in ["cvssMetricV31", "cvssMetricV30", "cvssMetricV2"]:
                if version in metrics:
                    return metrics[version][0]["cvssData"]["baseScore"]
            return None
        except Exception:
            return None 