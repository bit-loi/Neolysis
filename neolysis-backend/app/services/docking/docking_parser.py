import re
from dataclasses import dataclass


@dataclass
class ParsedDockingOutput:
    binding_affinity: float
    pose_rank: int
    rmsd_lb: float | None
    rmsd_ub: float | None
    raw_table: str


class DockingOutputParser:
    TABLE_ROW = re.compile(
        r"^\s*(?P<rank>\d+)\s+(?P<affinity>-?\d+(?:\.\d+)?)\s+(?P<rmsd_lb>-?\d+(?:\.\d+)?)?\s*(?P<rmsd_ub>-?\d+(?:\.\d+)?)?"
    )

    def parse_vina_like_output(self, output: str) -> ParsedDockingOutput:
        rows: list[tuple[int, float, float | None, float | None, str]] = []
        for line in output.splitlines():
            match = self.TABLE_ROW.match(line)
            if not match:
                continue
            rank = int(match.group("rank"))
            affinity = float(match.group("affinity"))
            rmsd_lb = self._optional_float(match.group("rmsd_lb"))
            rmsd_ub = self._optional_float(match.group("rmsd_ub"))
            rows.append((rank, affinity, rmsd_lb, rmsd_ub, line))

        if not rows:
            raise ValueError("Could not parse a Vina-style affinity table from docking output.")

        rows.sort(key=lambda item: (item[0], item[1]))
        rank, affinity, rmsd_lb, rmsd_ub, _ = rows[0]
        raw_table = "\n".join(item[4] for item in rows)
        return ParsedDockingOutput(
            binding_affinity=affinity,
            pose_rank=rank,
            rmsd_lb=rmsd_lb,
            rmsd_ub=rmsd_ub,
            raw_table=raw_table,
        )

    @staticmethod
    def _optional_float(value: str | None) -> float | None:
        return float(value) if value not in {None, ""} else None
