from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class TrainerSettings:
    service_name: str = "trainer-agent"
