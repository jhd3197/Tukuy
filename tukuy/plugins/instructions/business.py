"""Business instruction pack -- AI-powered business strategy tools.

Provides instructions for SWOT analysis, elevator pitch drafting,
meeting agenda creation, OKR formulation, and competitive briefs.
"""

from ...instruction import instruction
from ...manifest import PluginManifest, PluginRequirements
from ..base import TransformerPlugin


# ---------------------------------------------------------------------------
# Instructions
# ---------------------------------------------------------------------------

@instruction(
    name="swot_analysis",
    description="Generate a SWOT analysis (Strengths, Weaknesses, Opportunities, Threats) for a business or product",
    prompt=(
        "Perform a SWOT analysis for the following business, product, or initiative. "
        "Identify key strengths, weaknesses, opportunities, and threats with "
        "brief explanations for each.\n\n"
        "Subject: {subject}\n"
        "Industry/Context: {context}\n"
        "Additional Details: {details}"
    ),
    system_prompt=(
        "You are a business strategy consultant with expertise in competitive analysis. "
        "Provide actionable, specific insights — not generic platitudes. "
        "Always respond with valid JSON."
    ),
    output_format="json",
    temperature=0.5,
    max_tokens=800,
    category="business",
    tags=["swot", "strategy", "analysis", "business"],
    icon="layout",
    few_shot_examples=[
        {
            "input": "Subject: Small local bakery expanding to online orders. Industry: food & beverage. Details: 10-year reputation, no current web presence.",
            "output": '{"strengths": ["Strong 10-year local reputation and loyal customer base", "Proven product quality and recipes", "Low overhead compared to chain competitors"], "weaknesses": ["No existing web presence or e-commerce infrastructure", "Limited technical expertise for online operations", "Perishable products complicate shipping logistics"], "opportunities": ["Growing demand for artisanal and local food delivery", "Social media marketing can amplify word-of-mouth at low cost", "Partnerships with local delivery services"], "threats": ["Established online bakeries and meal-kit competitors", "Rising ingredient and shipping costs", "Food safety regulations for shipped goods"], "summary": "The bakery has a solid foundation to build on but needs to invest in e-commerce infrastructure and solve the shipping logistics challenge before scaling online."}',
        },
    ],
)
def swot_analysis(subject: str, context: str = "", details: str = ""):
    pass


@instruction(
    name="elevator_pitch",
    description="Craft a concise elevator pitch for a business, product, or idea",
    prompt=(
        "Write a compelling elevator pitch (30-60 seconds when spoken) for the "
        "following business, product, or idea. Make it memorable, clear, and "
        "action-oriented.\n\n"
        "What: {what}\n"
        "Target Audience: {audience}\n"
        "Key Differentiator: {differentiator}\n"
        "Desired Outcome: {outcome}"
    ),
    system_prompt=(
        "You are an expert pitch coach who has helped startups raise millions. "
        "Write pitches that are concise, compelling, and memorable. "
        "Always respond with valid JSON."
    ),
    output_format="json",
    temperature=0.7,
    max_tokens=500,
    category="business",
    tags=["pitch", "startup", "communication", "business"],
    icon="trending-up",
    few_shot_examples=[
        {
            "input": "What: AI-powered recipe app that reduces food waste. Audience: busy parents. Differentiator: scans your fridge with phone camera. Outcome: get users to download the app.",
            "output": '{"pitch": "Every year, the average family throws away $1,500 in groceries. We built FridgeScan — just point your phone at your fridge and our AI instantly suggests delicious meals from what you already have. No more forgotten leftovers, no more last-minute grocery runs. Over 50,000 families have already cut their food waste in half. Download FridgeScan free today and start saving.", "word_count": 58, "estimated_duration_seconds": 25, "hook": "The $1,500 problem every family ignores", "closing_cta": "Download FridgeScan free today"}',
        },
    ],
)
def elevator_pitch(what: str, audience: str, differentiator: str = "", outcome: str = "generate interest"):
    pass


@instruction(
    name="meeting_agenda",
    description="Create a structured meeting agenda with time allocations and objectives",
    prompt=(
        "Create a structured meeting agenda with time allocations, responsible "
        "parties, and clear objectives for each item.\n\n"
        "Meeting Purpose: {purpose}\n"
        "Duration: {duration}\n"
        "Attendees: {attendees}\n"
        "Key Topics: {topics}"
    ),
    system_prompt=(
        "You are a productivity expert specializing in effective meetings. "
        "Create agendas that respect everyone's time and drive decisions. "
        "Always respond with valid JSON."
    ),
    output_format="json",
    temperature=0.4,
    max_tokens=600,
    category="business",
    tags=["meetings", "productivity", "agenda", "business"],
    icon="calendar",
    few_shot_examples=[
        {
            "input": "Purpose: Q1 product roadmap review. Duration: 60 minutes. Attendees: product team, engineering leads, design lead. Topics: Q4 retrospective, Q1 priorities, resource allocation.",
            "output": '{"title": "Q1 Product Roadmap Review", "duration_minutes": 60, "objective": "Align on Q1 priorities and resource allocation based on Q4 learnings", "items": [{"time": "0-5 min", "topic": "Opening & Context Setting", "owner": "Product Lead", "objective": "Set the stage and review agenda"}, {"time": "5-20 min", "topic": "Q4 Retrospective", "owner": "Product Lead", "objective": "Review key wins, misses, and lessons learned"}, {"time": "20-40 min", "topic": "Q1 Priority Discussion", "owner": "All Leads", "objective": "Present and debate proposed Q1 initiatives"}, {"time": "40-55 min", "topic": "Resource Allocation", "owner": "Engineering Lead", "objective": "Map team capacity to agreed priorities"}, {"time": "55-60 min", "topic": "Action Items & Wrap-up", "owner": "Product Lead", "objective": "Summarize decisions and assign next steps"}], "pre_work": ["Review Q4 metrics dashboard", "Submit Q1 initiative proposals by Monday"]}',
        },
    ],
)
def meeting_agenda(purpose: str, duration: str, attendees: str = "", topics: str = ""):
    pass


@instruction(
    name="draft_okrs",
    description="Draft OKRs (Objectives and Key Results) for a team or initiative",
    prompt=(
        "Draft OKRs for the given team or initiative. Each objective should be "
        "ambitious but achievable, and each key result should be measurable "
        "and time-bound.\n\n"
        "Team/Initiative: {team}\n"
        "Time Period: {period}\n"
        "Focus Areas: {focus}\n"
        "Context: {context}"
    ),
    system_prompt=(
        "You are an OKR coach who has guided organizations from startups to Fortune 500 "
        "companies. Write OKRs that are specific, measurable, and inspiring. "
        "Always respond with valid JSON."
    ),
    output_format="json",
    temperature=0.5,
    max_tokens=800,
    category="business",
    tags=["okr", "goals", "planning", "business"],
    icon="target",
    few_shot_examples=[
        {
            "input": "Team: Customer Success. Period: Q2 2025. Focus: reduce churn, improve NPS. Context: churn is currently 8% monthly, NPS is 32.",
            "output": '{"objectives": [{"objective": "Dramatically reduce customer churn through proactive engagement", "key_results": ["Reduce monthly churn rate from 8% to 4%", "Implement automated health-score alerts for 100% of accounts", "Conduct quarterly business reviews with top 50 accounts"]}, {"objective": "Elevate customer satisfaction to best-in-class levels", "key_results": ["Increase NPS from 32 to 50", "Achieve 95% support ticket resolution within 24 hours", "Launch customer advisory board with 10 founding members"]}], "notes": "These OKRs are stretch goals. Hitting 70% would represent significant progress from current baselines."}',
        },
    ],
)
def draft_okrs(team: str, period: str, focus: str, context: str = ""):
    pass


@instruction(
    name="competitive_brief",
    description="Create a competitive analysis brief comparing your offering against competitors",
    prompt=(
        "Create a competitive analysis brief. Compare the subject against the "
        "listed competitors across key dimensions relevant to the target market.\n\n"
        "Your Offering: {offering}\n"
        "Competitors: {competitors}\n"
        "Target Market: {market}\n"
        "Key Dimensions: {dimensions}"
    ),
    system_prompt=(
        "You are a competitive intelligence analyst. Provide objective, evidence-based "
        "comparisons. Highlight both advantages and disadvantages honestly. "
        "Always respond with valid JSON."
    ),
    output_format="json",
    temperature=0.4,
    max_tokens=1000,
    category="business",
    tags=["competitive", "analysis", "strategy", "business"],
    icon="shield",
    few_shot_examples=[
        {
            "input": "Offering: Our project management SaaS. Competitors: Asana, Monday.com, Jira. Market: mid-size tech companies. Dimensions: pricing, ease of use, integrations, reporting.",
            "output": '{"comparison": {"pricing": {"our_offering": "Mid-range, per-user pricing with free tier", "Asana": "Premium tier expensive for large teams", "Monday.com": "Competitive but add-ons increase cost", "Jira": "Low per-user cost but complex licensing"}, "ease_of_use": {"our_offering": "Modern UI, low learning curve", "Asana": "Clean interface, good onboarding", "Monday.com": "Highly visual, easy for non-technical users", "Jira": "Steep learning curve, developer-oriented"}}, "our_advantages": ["More intuitive onboarding than Jira", "Better value at mid-tier pricing"], "our_gaps": ["Fewer integrations than Asana and Monday.com", "Less brand recognition in enterprise segment"], "recommendations": ["Invest in integration marketplace to close the gap", "Target teams migrating away from Jira for simplicity"]}',
        },
    ],
)
def competitive_brief(offering: str, competitors: str, market: str = "", dimensions: str = "pricing, features, ease of use"):
    pass


# ---------------------------------------------------------------------------
# Plugin class
# ---------------------------------------------------------------------------

class BusinessInstructionPack(TransformerPlugin):
    """AI-powered business tools: SWOT, elevator pitches, meeting agendas, OKRs, competitive briefs."""

    def __init__(self):
        super().__init__("instructions_business")

    @property
    def transformers(self):
        return {}

    @property
    def instructions(self):
        return {
            "swot_analysis": swot_analysis.__instruction__,
            "elevator_pitch": elevator_pitch.__instruction__,
            "meeting_agenda": meeting_agenda.__instruction__,
            "draft_okrs": draft_okrs.__instruction__,
            "competitive_brief": competitive_brief.__instruction__,
        }

    @property
    def manifest(self):
        return PluginManifest(
            name="instructions_business",
            display_name="Business Instructions",
            description="AI-powered business tools: SWOT analysis, elevator pitches, meeting agendas, OKR drafting, and competitive briefs.",
            icon="briefcase",
            group="Instructions",
            requires=PluginRequirements(network=True),
        )
