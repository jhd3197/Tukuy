"""HR instruction pack -- AI-powered human resources tools.

Provides instructions for job description writing, interview question generation,
performance feedback drafting, onboarding plan creation, and offer letter drafting.
"""

from ...instruction import instruction
from ...manifest import PluginManifest, PluginRequirements
from ..base import TransformerPlugin


# ---------------------------------------------------------------------------
# Instructions
# ---------------------------------------------------------------------------

@instruction(
    name="write_job_description",
    description="Write a clear and inclusive job description for a role",
    prompt=(
        "Write a job description for the specified role. Include responsibilities, "
        "requirements, nice-to-haves, and company culture signals. "
        "Use inclusive language throughout.\n\n"
        "Role Title: {title}\n"
        "Department: {department}\n"
        "Seniority: {seniority}\n"
        "Key Responsibilities: {responsibilities}\n"
        "Company Context: {company_context}"
    ),
    system_prompt=(
        "You are a talent acquisition expert who writes job descriptions that attract "
        "diverse, qualified candidates. Use clear language, avoid jargon, and be inclusive. "
        "Always respond with valid JSON."
    ),
    output_format="json",
    temperature=0.5,
    max_tokens=800,
    category="hr",
    tags=["job-description", "recruiting", "hr", "hiring"],
    icon="user-plus",
    few_shot_examples=[
        {
            "input": "Title: Senior Backend Engineer. Department: Engineering. Seniority: senior (5+ years). Responsibilities: design APIs, mentor juniors, own microservices. Company: remote-first SaaS startup, 50 employees.",
            "output": '{"title": "Senior Backend Engineer", "location": "Remote", "department": "Engineering", "about_role": "We\u2019re looking for a Senior Backend Engineer to help us scale our platform as we grow from 50 to 500 customers. You\u2019ll design and own critical APIs, mentor junior engineers, and shape our technical direction.", "responsibilities": ["Design and build scalable REST and GraphQL APIs", "Own end-to-end delivery of microservices", "Mentor junior engineers through code reviews and pairing", "Collaborate with product and design on technical feasibility", "Contribute to architecture decisions and tech debt strategy"], "requirements": ["5+ years of backend development experience", "Strong experience with Python, Go, or Java", "Hands-on experience with microservices and cloud infrastructure", "Track record of mentoring or leading small teams", "Clear written communication skills (we\u2019re remote-first)"], "nice_to_have": ["Experience at a high-growth startup", "Familiarity with event-driven architectures", "Contributions to open-source projects"], "benefits_preview": "Competitive salary, equity, flexible hours, learning budget, and annual team retreats."}',
        },
    ],
)
def write_job_description(title: str, department: str, seniority: str, responsibilities: str, company_context: str = ""):
    pass


@instruction(
    name="interview_questions",
    description="Generate targeted interview questions for a specific role and competency",
    prompt=(
        "Generate interview questions for the given role. Include a mix of "
        "behavioral, technical, and situational questions tailored to the "
        "competencies needed.\n\n"
        "Role: {role}\n"
        "Competencies to Assess: {competencies}\n"
        "Interview Stage: {stage}\n"
        "Number of Questions: {num_questions}"
    ),
    system_prompt=(
        "You are a hiring manager and interview coach. Create questions that reveal "
        "genuine capability and cultural fit. Include evaluation guidance. "
        "Always respond with valid JSON."
    ),
    output_format="json",
    temperature=0.5,
    max_tokens=800,
    category="hr",
    tags=["interview", "hiring", "hr", "assessment"],
    icon="message-square",
    few_shot_examples=[
        {
            "input": "Role: Product Manager. Competencies: prioritization, stakeholder management, data-driven decisions. Stage: second round. Questions: 3.",
            "output": '{"questions": [{"question": "Tell me about a time you had to say no to a stakeholder who wanted a feature that didn\u2019t align with your roadmap. How did you handle it?", "type": "behavioral", "competency": "stakeholder management", "what_to_look_for": "Empathy, clear communication of rationale, ability to suggest alternatives, maintaining relationship", "red_flags": ["Avoided the conversation", "Caved without pushback", "Was dismissive of the stakeholder\u2019s needs"]}, {"question": "You have 5 feature requests, limited engineering bandwidth, and conflicting data on what to build next. Walk me through how you\u2019d decide.", "type": "situational", "competency": "prioritization", "what_to_look_for": "Structured framework (RICE, impact/effort), stakeholder input, willingness to make a call with imperfect data", "red_flags": ["No framework", "Defers entirely to loudest voice", "Analysis paralysis"]}, {"question": "Describe a product decision you made that was driven by data. What metrics did you use and what was the outcome?", "type": "behavioral", "competency": "data-driven decisions", "what_to_look_for": "Specific metrics cited, clear cause-and-effect reasoning, honest about what worked and what didn\u2019t", "red_flags": ["Vague about metrics", "Took credit for team effort", "No mention of outcome"]}]}',
        },
    ],
)
def interview_questions(role: str, competencies: str, stage: str = "first round", num_questions: str = "5"):
    pass


@instruction(
    name="performance_feedback",
    description="Draft constructive performance feedback for an employee",
    prompt=(
        "Draft constructive performance feedback for an employee. Be specific, "
        "balanced, and actionable. Use the situation-behavior-impact framework.\n\n"
        "Employee Role: {role}\n"
        "Review Period: {period}\n"
        "Accomplishments: {accomplishments}\n"
        "Areas for Growth: {growth_areas}\n"
        "Overall Performance: {overall}"
    ),
    system_prompt=(
        "You are an HR expert and leadership coach. Write feedback that is specific, "
        "fair, and development-oriented. Use SBI (Situation-Behavior-Impact) format. "
        "Always respond with valid JSON."
    ),
    output_format="json",
    temperature=0.4,
    max_tokens=800,
    category="hr",
    tags=["performance", "feedback", "hr", "management"],
    icon="star",
    few_shot_examples=[
        {
            "input": "Role: Junior Designer. Period: H2 2024. Accomplishments: redesigned onboarding flow, improved conversion 18%. Areas for growth: presenting to stakeholders, design system consistency. Overall: meets expectations with high potential.",
            "output": '{"summary": "Strong contributor who delivered measurable impact on the onboarding redesign. Ready for more visibility with targeted development in stakeholder communication.", "strengths": [{"area": "User Research & Design Execution", "feedback": "Your redesign of the onboarding flow demonstrated excellent user empathy. The 18% conversion improvement is a direct result of the research-driven approach you took \u2014 specifically the usability tests you initiated independently.", "impact": "Directly contributed to Q4 growth targets."}], "growth_areas": [{"area": "Stakeholder Presentations", "feedback": "In the September design review, you had strong work but struggled to articulate the rationale behind your decisions when challenged by the VP of Product. The designs were solid \u2014 the communication didn\u2019t match.", "suggestion": "Practice presenting designs to your manager first. Focus on leading with the problem and data before showing solutions.", "support": "I\u2019ll pair you with a senior designer for your next two presentations."}, {"area": "Design System Consistency", "feedback": "Several components in the onboarding redesign drifted from the design system without documented rationale.", "suggestion": "Before deviating from the system, document why and propose updates to the system itself."}], "overall_rating": "Meets expectations with high potential", "development_goals": ["Present at least 2 design reviews independently in H1 2025", "Contribute 3 components to the design system"]}',
        },
    ],
)
def performance_feedback(role: str, period: str, accomplishments: str, growth_areas: str, overall: str = "meets expectations"):
    pass


@instruction(
    name="onboarding_plan",
    description="Create a structured onboarding plan for a new hire's first 30/60/90 days",
    prompt=(
        "Create an onboarding plan for a new hire. Structure it as a 30/60/90 day plan "
        "with specific milestones, meetings, and learning goals.\n\n"
        "Role: {role}\n"
        "Department: {department}\n"
        "Team Size: {team_size}\n"
        "Key Tools/Systems: {tools}\n"
        "Manager: {manager}"
    ),
    system_prompt=(
        "You are an onboarding specialist who designs ramp-up plans that help new hires "
        "become productive fast while feeling welcomed. Be specific and actionable. "
        "Always respond with valid JSON."
    ),
    output_format="json",
    temperature=0.5,
    max_tokens=1000,
    category="hr",
    tags=["onboarding", "new-hire", "hr", "ramp-up"],
    icon="user-check",
    few_shot_examples=[
        {
            "input": "Role: Frontend Engineer. Department: Engineering. Team size: 8. Tools: React, GitHub, Figma, Linear. Manager: Sarah (Engineering Lead).",
            "output": '{"role": "Frontend Engineer", "plan": {"first_30_days": {"theme": "Learn & Observe", "milestones": ["Complete all system access and tool setup (Day 1-2)", "Ship first small PR (fix a bug or update copy) by Day 5", "Complete codebase walkthrough with team buddy", "Shadow 3 sprint planning and code review sessions", "1:1 with each team member to understand their work"], "meetings": ["Daily standup", "Weekly 1:1 with Sarah", "Meet with product manager and designer"], "success_criteria": "Can navigate the codebase, has merged 3+ PRs, and understands team rituals."}, "days_31_to_60": {"theme": "Contribute & Collaborate", "milestones": ["Own and deliver a small feature end-to-end", "Participate actively in code reviews (give and receive)", "Present a brief tech topic at team meeting", "Identify one process improvement suggestion"], "success_criteria": "Independently delivering features with minimal guidance."}, "days_61_to_90": {"theme": "Own & Lead", "milestones": ["Own a medium-complexity feature from design to production", "Mentor or pair with newer team members if applicable", "Draft a proposal for a technical improvement", "Complete 90-day self-reflection and feedback session with Sarah"], "success_criteria": "Operating as a fully autonomous team member with ownership of a feature area."}}, "buddy_assignment": "Assign an experienced team member as onboarding buddy for first 30 days"}',
        },
    ],
)
def onboarding_plan(role: str, department: str, team_size: str = "", tools: str = "", manager: str = ""):
    pass


@instruction(
    name="draft_offer_letter",
    description="Draft a professional offer letter for a candidate",
    prompt=(
        "Draft a professional offer letter for the specified candidate and role. "
        "Include all standard components while maintaining a warm, welcoming tone.\n\n"
        "Candidate Name: {candidate}\n"
        "Role: {role}\n"
        "Compensation: {compensation}\n"
        "Start Date: {start_date}\n"
        "Additional Details: {details}"
    ),
    system_prompt=(
        "You are an HR professional drafting offer letters. Write clearly and warmly. "
        "Include all standard components but keep the tone welcoming. "
        "Always respond with valid JSON."
    ),
    output_format="json",
    temperature=0.3,
    max_tokens=800,
    category="hr",
    tags=["offer-letter", "hiring", "hr", "recruitment"],
    icon="mail",
    few_shot_examples=[
        {
            "input": "Candidate: Alex Rivera. Role: Senior Data Analyst. Compensation: $130,000/year + 15% bonus. Start date: March 3, 2025. Details: remote position, reports to VP of Data, equity package included.",
            "output": '{"subject": "We\u2019d love to have you join us, Alex!", "letter": {"greeting": "Dear Alex,", "opening": "We\u2019re thrilled to extend an offer for the Senior Data Analyst role. Your analytical expertise and collaborative approach stood out throughout our interview process, and we\u2019re excited about what you\u2019ll bring to the team.", "details": {"position": "Senior Data Analyst", "reporting_to": "VP of Data", "location": "Remote", "start_date": "March 3, 2025", "compensation": {"base_salary": "$130,000/year", "bonus": "15% annual performance bonus", "equity": "Stock option grant (details in separate equity agreement)"}}, "next_steps": "Please review this offer and let us know your decision by [date]. We\u2019re happy to answer any questions \u2014 feel free to reach out directly.", "closing": "We believe you\u2019ll make a meaningful impact here, and we can\u2019t wait to welcome you to the team.\\n\\nWarm regards,\\n[Hiring Manager Name]\\n[Title]"}, "notes": "This is a template \u2014 have legal review before sending. Include benefits summary and equity grant details as separate attachments."}',
        },
    ],
)
def draft_offer_letter(candidate: str, role: str, compensation: str, start_date: str = "TBD", details: str = ""):
    pass


# ---------------------------------------------------------------------------
# Plugin class
# ---------------------------------------------------------------------------

class HRInstructionPack(TransformerPlugin):
    """AI-powered HR tools: job descriptions, interview questions, feedback, onboarding plans, offer letters."""

    def __init__(self):
        super().__init__("instructions_hr")

    @property
    def transformers(self):
        return {}

    @property
    def instructions(self):
        return {
            "write_job_description": write_job_description.__instruction__,
            "interview_questions": interview_questions.__instruction__,
            "performance_feedback": performance_feedback.__instruction__,
            "onboarding_plan": onboarding_plan.__instruction__,
            "draft_offer_letter": draft_offer_letter.__instruction__,
        }

    @property
    def manifest(self):
        return PluginManifest(
            name="instructions_hr",
            display_name="HR Instructions",
            description="AI-powered HR tools: job descriptions, interview questions, performance feedback, onboarding plans, and offer letters.",
            icon="users",
            group="Instructions",
            requires=PluginRequirements(network=True),
        )
