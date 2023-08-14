from dataclasses import dataclass, field

@dataclass
class SensorPrices:
    use_cent: bool = False
    prices: list[list] = field(default_factory=lambda: [])
    currency :str = "sek"

