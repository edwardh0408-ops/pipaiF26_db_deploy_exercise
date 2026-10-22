"""Models computed from the placeholder database."""

from dataclasses import dataclass

from backend.database import read_table

LABELS = {
    "programming": "Programming",
    "data_stats": "Data and stats",
    "frontend_design": "Frontend design",
    "business_pitch": "Business pitch",
}


@dataclass(frozen=True)
class CompetencyAverage:
    skill_id: int
    code: str
    label: str
    average: float

    def to_dict(self) -> dict[str, int | str | float]:
        return {
            "skill_id": self.skill_id,
            "code": self.code,
            "label": self.label,
            "average": round(self.average, 2),
        }


class CompetencyModel:
    """Average each competency rating across every student."""

    def averages(self) -> list[CompetencyAverage]:
        skills = read_table("skill")
        ratings: dict[str, list[int]] = {}
        for row in read_table("student_skill"):
            ratings.setdefault(row["skill_id"], []).append(int(row["rating"]))

        results = []
        for skill in skills:
            scores = ratings.get(skill["skill_id"], [])
            average = sum(scores) / len(scores) if scores else 0.0
            code = skill["code"]
            results.append(
                CompetencyAverage(
                    skill_id=int(skill["skill_id"]),
                    code=code,
                    label=LABELS.get(code, code),
                    average=average,
                )
            )
        return results
