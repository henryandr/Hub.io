import json
import ssl
import urllib.request
from typing import Dict, Tuple

from gateway.config import BackendConfig


class FhirClient:
    def __init__(self, config: BackendConfig) -> None:
        self.config = config

    def send_bundle(self, bundle: Dict[str, object]) -> Tuple[int, str]:
        data = json.dumps(bundle).encode("utf-8")
        request = urllib.request.Request(
            self.config.endpoint_url,
            data=data,
            method="POST",
            headers={
                "Content-Type": "application/fhir+json",
                "Accept": "application/fhir+json",
            },
        )

        if self.config.auth_token:
            request.add_header("Authorization", f"Bearer {self.config.auth_token}")

        context = None
        if self.config.endpoint_url.startswith("https") and not self.config.verify_tls:
            context = ssl._create_unverified_context()

        with urllib.request.urlopen(request, timeout=self.config.timeout_seconds, context=context) as response:
            body = response.read().decode("utf-8", errors="ignore")
            return response.status, body
