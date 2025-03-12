from pydantic import BaseModel, Field
from typing import Optional, Dict, List


# Candidate Data Structure Definition (output definition)
class Candidate(BaseModel):
    name: Optional[str] = Field(None, description="The full name of the candidate")
    email: Optional[str] = Field(None, description="The email of the candidate")
    age: Optional[int] = Field(
        None,
        description="The age of the candidate. If not explicitly stated, estimate based on education or work experience.",
    )
    skills: Optional[Dict[str, 'SkillDetail']] = Field(
        None, description="A dictionary of skills possessed by the candidate with detailed information"
    )


class Skill(BaseModel):
    relevance: Optional[str] = Field(
        None, description="How relevant is the skill to the job position"
    )
    reasoning: Optional[str] = Field(
        None,
        description="Why this skill is relevant to the job position",
    )
    proficiency: Optional[int] = Field(
        None,
        description="Based on the year's he worked using this skill, please provide an  proficiency level",
    )


class SkillDetail(BaseModel):
    skill_name: str = Field(description="The name of the skill")
    category: Optional[str] = Field(None, description="Category of the skill (Technical, Soft Skill, Domain Knowledge, etc.)")
    proficiency: Optional[float] = Field(None, description="Proficiency level on a 0-100 scale")
    years_experience: Optional[float] = Field(None, description="Years of experience with this skill")
    mentions: Optional[List[str]] = Field(None, description="Contexts where the skill was mentioned")
    related_skills: Optional[List[str]] = Field(None, description="List of related skills")


class JobSkill(BaseModel):
    skills: Dict[str, Skill] = Field(None, description="Skill")
    jobName: str = Field(None, description="Job position name")
