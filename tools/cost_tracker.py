import threading
from dataclasses import dataclass, field
from typing import Dict

_lock = threading.Lock()

# GPT-4o pricing as of May 2026 — verify at platform.openai.com/pricing
_INPUT_COST_PER_1M = 2.50
_OUTPUT_COST_PER_1M = 10.00


@dataclass
class AgentCost:
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0


@dataclass
class CostTracker:
    breakdown: Dict[str, AgentCost] = field(default_factory=dict)

    def record(self, agent_name: str, prompt_tokens: int, completion_tokens: int) -> None:
        with _lock:
            cost = (
                prompt_tokens * _INPUT_COST_PER_1M
                + completion_tokens * _OUTPUT_COST_PER_1M
            ) / 1_000_000
            self.breakdown[agent_name] = AgentCost(
                tokens_in=prompt_tokens,
                tokens_out=completion_tokens,
                cost_usd=round(cost, 6),
            )

    @property
    def total_cost_usd(self) -> float:
        return round(sum(a.cost_usd for a in self.breakdown.values()), 6)

    def summary(self) -> str:
        if not self.breakdown:
            return "Cost breakdown: no data recorded"
        lines = ["Cost breakdown:"]
        for name, cost in self.breakdown.items():
            lines.append(
                f"  {name:<18} {cost.tokens_in:>7,} in  {cost.tokens_out:>6,} out  ${cost.cost_usd:.4f}"
            )
        lines.append(f"  {'TOTAL':<18}{'':>15}  ${self.total_cost_usd:.4f}")
        return "\n".join(lines)

    def reset(self) -> None:
        self.breakdown.clear()


# Module-level singleton — agents can import and call tracker.record(...)
tracker = CostTracker()
