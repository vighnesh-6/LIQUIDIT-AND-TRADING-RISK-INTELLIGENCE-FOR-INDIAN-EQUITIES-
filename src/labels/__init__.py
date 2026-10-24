"""Labels and Risk-Score computation package (LRS and HRE_5d target)."""

from src.labels.lrs import compute_lrs
from src.labels.targets import construct_hre_target

__all__ = ["compute_lrs", "construct_hre_target"]
