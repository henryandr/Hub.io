import asyncio
import logging

from gateway.ble import BleGateway
from gateway.client import FhirClient
from gateway.config import GatewayConfig
from gateway.fhir import FhirBundleBuilder

LOGGER = logging.getLogger(__name__)


class GatewayApplication:
    def __init__(self, config: GatewayConfig) -> None:
        self.config = config
        self.collector = BleGateway(config.ble)
        self.bundle_builder = FhirBundleBuilder(config.patient)
        self.client = FhirClient(config.backend)

    async def run(self) -> None:
        if self.config.run_once:
            await self.run_cycle()
            return

        while True:
            await self.run_cycle()
            await asyncio.sleep(self.config.poll_interval_seconds)

    async def run_cycle(self) -> None:
        readings = await self.collector.collect()
        if not readings:
            LOGGER.info("No biomedical measurements captured in this cycle")
            return

        bundle = self.bundle_builder.build(readings)
        status, body = await asyncio.to_thread(self.client.send_bundle, bundle)
        LOGGER.info("FHIR bundle delivered with status %s", status)
        if body:
            LOGGER.debug("FHIR server response: %s", body)
