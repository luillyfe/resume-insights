from pydantic import BaseModel, Field
from typing import Optional, List


# Candidate Data Structure Definition (output definition)
class Candidate(BaseModel):
    name: Optional[str] = Field(None, description="The full name of the candidate")
    email: Optional[str] = Field(None, description="The email of the candidate")
    age: Optional[int] = Field(
        None,
        description="The age of the candidate. If not explicitly stated, estimate based on education or work experience.",
    )
    skills: Optional[list[str]] = Field(
        None, description="A list of skills possessed by the candidate"
    )


class Skill(BaseModel):
    relevance: Optional[str] = Field(
        None, description="How relevant is the skill to the job position"
    )
    reasoning: Optional[str] = Field(
        None,
        description="Why this skill is relevant to the job position",
    )


class JobSkill(BaseModel):
    skill: Optional[List[Skill]] = Field(None, description="Skill")
