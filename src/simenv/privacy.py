from dataclasses import dataclass
from typing import Sequence


@dataclass
class PrivacyScheme:
    SECURITY: float
    O_ENC: float
    O_DEC: float

PrivacySchemeList = Sequence[PrivacyScheme]