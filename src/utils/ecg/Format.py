# Standard library imports
from dataclasses import dataclass
from typing import Iterable, ClassVar

# Application-specific imports
from utils.ecg.Lead import Lead

@dataclass(frozen=True)
class Format:
    """
    Class with the two main formats of an ECG, "Standard format" and
    "Cabrera format".
    """

    STANDARD: ClassVar[Iterable[str]] = [
        Lead.I,
        Lead.II,
        Lead.III,
        Lead.aVR,
        Lead.aVL,
        Lead.aVF,
        Lead.V1,
        Lead.V2,
        Lead.V3,
        Lead.V4,
        Lead.V5,
        Lead.V6,
    ]
    
    CABRERA: ClassVar[Iterable[str]] = [
        Lead.aVL,
        Lead.I,
        Lead.aVR,
        Lead.II,
        Lead.aVF,
        Lead.III,
        Lead.V1,
        Lead.V2,
        Lead.V3,
        Lead.V4,
        Lead.V5,
        Lead.V6,
    ]
