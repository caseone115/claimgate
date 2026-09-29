"""Policy: what this organisation is allowed to publish, checked mechanically.

Two things live here, and they are deliberately separate.

1. **Prohibited and restricted claims.** A brand writes down, once, the things
   it may never say and the things it may only say with sign-off. The checker
   enforces that list against every draft. This is the "constitutional layer"
   the industry keeps describing and almost nobody implements, because it is
   unglamorous: it is a list and a matcher.

2. **Disclosure obligations.** From 2 August 2026 the EU AI Act (Article 50)
   requires that AI-generated content be disclosed in specified circumstances,
   and platform rules (Meta, TikTok, Google) additionally require an AI label
   on realistic synthetic media in advertising. A draft that is AI-assisted
   and customer-facing and carries no disclosure is non-compliant regardless
   of how good the copy is — so this is checked as a property of the draft,
   not left to whoever uploads it.

Both produce findings in the same shape as claim findings, so one report
covers everything an editor has to clear.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict, field
from pathlib import Path

from .claims import Claim, CATEGORIES


@dataclass
class Rule:
    id: str
    pattern: str
    category: str          # prohibited | restricted | style
    reason: str
    severity: str = "high"  # prohibited defaults to blocking
    fix: str = ""

    def regex(self):
        return re.compile(self.pattern, re.I)


DEFAULT_RULES: list[Rule] = [
    Rule("no-guarantee", r"\b(?:guarantee|guaranteed|100% (?:safe|effective|"
         r"secure|accurate|reliable))\b", "prohibited",
         "absolute guarantees are unenforceable and are treated as misleading "
         "advertising", "high",
         "state what the product does and the conditions under which it does it"),
    # The medical rule requires a medical *outcome* near the verb. A bare
    # \btreats?\b match fires on ordinary English ("treat the figure as
    # indicative", "treats each draft the same"), which is a false positive on
    # exactly the sort of compliance prose this tool is aimed at — and a
    # false positive on a blocking rule is worse than a missed one, because it
    # teaches the operator to ignore the gate. The outcome must also fall
    # inside the same sentence (no "." between verb and outcome).
    Rule("no-medical", r"\b(?:cures?|treats?|prevents?|diagnoses?)\b"
         r"(?=[^.]{0,60}\b(?:disease|illness|cancer|condition|disorder|"
         r"infection|symptoms?|pain|inflammation|depression|anxiety|adhd|"
         r"diabetes|arthritis|asthma|acne|eczema|migraine|insomnia|injury|"
         r"wound|allergy|obesity)\b)"
         r"|\bclinically proven to\b", "prohibited",
         "medical efficacy claims require regulatory authorisation", "high",
         "describe the product's function, not a medical outcome"),
    Rule("no-financial-advice", r"\b(?:guaranteed returns?|risk[- ]free "
         r"investment|will (?:make|earn) you \$?\d|guaranteed (?:profit|"
         r"income|returns?))\b", "prohibited",
         "financial return claims require licensing and disclosure", "high",
         "add the required risk statement or remove the return claim"),
    Rule("no-superlative-unsourced", r"\b(?:the|our) (?:best|number one|#1|"
         r"world[- ]class|industry[- ]leading|market[- ]leading)\b",
         "restricted",
         "a leadership claim needs a dated, named third-party ranking", "medium",
         "attach the ranking and its date, or soften to a specific advantage"),
    Rule("no-competitor-named", r"\b(?:unlike|better than|worse than) "
         r"(?:[A-Z][\w]+)(?:\b|\s)", "restricted",
         "naming a competitor invites a comparative-advertising challenge",
         "medium", "compare to a category or to the customer's status quo"),
    Rule("no-synthetic-undisclosed", r"\b(?:photo-?realistic|realistic|"
         r"lifelike)\b", "restricted",
         "realistic synthetic media requires an AI disclosure on the asset",
         "medium", "apply the AI label before publishing"),
    Rule("no-personal-data", r"\b(?:social security|ssn|passport number|"
         r"credit card number|date of birth)\b", "prohibited",
         "publishing personal identifiers creates a data-protection breach",
         "high", "remove it"),
    Rule("no-unverified-award", r"\b(?:award[- ]winning|awarded|winner of)\b",
         "restricted", "award claims must name the awarding body and the year",
         "medium", "name the award, the body and the year"),
]


@dataclass
class PolicyFinding:
    kind: str              # prohibited | restricted | disclosure | style
    rule_id: str
    text: str
    reason: str
    severity: str
    fix: str = ""
    start: int = -1
    end: int = -1

    @property
    def blocking(self) -> bool:
        return self.severity == "high"

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class Policy:
    name: str = "default"
    rules: list[Rule] = field(default_factory=lambda: list(DEFAULT_RULES))
    # Set by the customer. `ai_assisted` says whether the draft was produced
    # with AI at all — which decides whether disclosure is even in scope.
    ai_assisted: bool = True
    customer_facing: bool = True
    jurisdictions: list[str] = field(default_factory=lambda: ["EU", "AU"])
    require_disclosure: bool | None = None   # None = derive from the above
    required_terms: list[str] = field(default_factory=list)
    min_disclosure: str = "AI-assisted"

    @property
    def disclosure_required(self) -> bool:
        if self.require_disclosure is not None:
            return self.require_disclosure
        # Article 50 bites on AI-generated content published to the public in
        # the EU; platform labelling rules are wider but the EU/UK/AU set is
        # the one that carries a reporting obligation today.
        return (self.ai_assisted and self.customer_facing
                and bool({"EU", "AU", "UK"} & set(self.jurisdictions)))

    @classmethod
    def load(cls, path: str | Path) -> "Policy":
        data = json.loads(Path(path).read_text())
        rules = [Rule(**r) for r in data.get("rules", [])] or list(DEFAULT_RULES)
        known = {f for f in cls.__dataclass_fields__} - {"rules"}
        kwargs = {k: v for k, v in data.items() if k in known}
        return cls(rules=rules, **kwargs)

    def save(self, path: str | Path) -> None:
        data = {
            "name": self.name,
            "ai_assisted": self.ai_assisted,
            "customer_facing": self.customer_facing,
            "jurisdictions": self.jurisdictions,
            "require_disclosure": self.require_disclosure,
            "required_terms": self.required_terms,
            "min_disclosure": self.min_disclosure,
            "rules": [asdict(r) for r in self.rules],
        }
        Path(path).write_text(json.dumps(data, indent=2))


def check_policy(text: str, policy: Policy) -> list[PolicyFinding]:
    """Every policy breach in the draft, plus any missing disclosure."""
    findings: list[PolicyFinding] = []
    for rule in policy.rules:
        for m in rule.regex().finditer(text):
            findings.append(PolicyFinding(
                kind=rule.category, rule_id=rule.id, text=m.group(0),
                reason=rule.reason, severity=rule.severity, fix=rule.fix,
                start=m.start(), end=m.end()))

    if policy.disclosure_required:
        low = text.lower()
        marked = (policy.min_disclosure.lower() in low
                  or "ai-generated" in low or "generated with ai" in low
                  or "made with ai" in low or "synthetic" in low)
        if not marked:
            findings.append(PolicyFinding(
                kind="disclosure", rule_id="ai-disclosure", text="",
                reason=("this draft is AI-assisted and customer-facing, and "
                        "carries no AI disclosure — required under EU AI Act "
                        "Article 50 (in force 2 Aug 2026) and by platform "
                        "labelling rules"),
                severity="high",
                fix=(f"add a plain disclosure containing "
                     f"\"{policy.min_disclosure}\" to the published asset, "
                     f"in the caption or the asset description")))

    for term in policy.required_terms:
        if term.lower() not in text.lower():
            findings.append(PolicyFinding(
                kind="style", rule_id=f"required:{term}", text="",
                reason=f"the policy requires the term {term!r} in every asset",
                severity="medium", fix=f"add {term!r}"))

    findings.sort(key=lambda f: 0 if f.severity == "high" else 1)
    return findings


def all_findings(claims: list[Claim], findings: list[PolicyFinding]) -> dict:
    """One combined view, which is what the report and the gate both read."""
    blocked = [c for c in claims if c.category in ("attribution", "efficacy",
                                                   "guarantee")]
    return {
        "claims": len(claims),
        "policy_findings": len(findings),
        "blocking_policy": sum(1 for f in findings if f.blocking),
        "blocking_claims": len(blocked),
        "clear": not findings and not blocked,
    }
