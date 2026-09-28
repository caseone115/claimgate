"""ClaimGate — a publish gate for AI-assisted marketing content.

The one-sentence version: point it at the copy you are about to publish and
the evidence your organisation holds, and it tells you which claims you
cannot substantiate, which of your own policy rules you are breaking, and
whether the asset is missing a disclosure the law now requires.

Nothing here is a black box. Every finding quotes the text it is about, says
what is missing, and says what to do. A gate that cannot be argued with is a
gate an editor turns off under deadline pressure, which is how organisations
end up with governance on paper and incidents in production.
"""
__version__ = "0.1.0"

from .claims import Claim, CATEGORIES, extract, summarise  # noqa: F401
from .policy import Policy, PolicyFinding, check_policy  # noqa: F401
from .substantiation import (Evidence, Verdict, assess, assess_all,  # noqa: F401
                             report)

__all__ = ["Claim", "CATEGORIES", "extract", "summarise", "Policy",
           "PolicyFinding", "check_policy", "Evidence", "Verdict", "assess",
           "assess_all", "report", "__version__"]
