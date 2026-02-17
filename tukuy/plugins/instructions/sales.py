"""Sales instruction pack -- AI-powered sales enablement tools.

Provides instructions for cold outreach, objection handling, proposal outlines,
follow-up messages, and value proposition crafting.
"""

from ...instruction import instruction
from ...manifest import PluginManifest, PluginRequirements
from ..base import TransformerPlugin


# ---------------------------------------------------------------------------
# Instructions
# ---------------------------------------------------------------------------

@instruction(
    name="cold_outreach",
    description="Draft a personalized cold outreach email or message for a prospect",
    prompt=(
        "Write a personalized cold outreach email or message. Make it concise, "
        "relevant to the prospect, and include a clear call to action.\n\n"
        "Prospect Info: {prospect}\n"
        "Your Product/Service: {product}\n"
        "Value Proposition: {value_prop}\n"
        "Channel: {channel}\n"
        "Tone: {tone}"
    ),
    system_prompt=(
        "You are a top-performing sales development rep known for high reply rates. "
        "Write outreach that is personalized, concise, and value-first — never spammy. "
        "Always respond with valid JSON."
    ),
    output_format="json",
    temperature=0.7,
    max_tokens=600,
    category="sales",
    tags=["outreach", "cold-email", "prospecting", "sales"],
    icon="send",
    few_shot_examples=[
        {
            "input": "Prospect: VP of Engineering at a 200-person SaaS company, recently posted about scaling challenges. Product: Developer productivity platform. Value prop: reduces CI/CD build times by 60%. Channel: LinkedIn message. Tone: professional, peer-to-peer.",
            "output": '{"subject": null, "message": "Hi [Name],\\n\\nSaw your post about scaling CI/CD \u2014 we ran into the same wall at our last company.\\n\\nWe built [Product] specifically for engineering teams hitting that inflection point. Our customers (similar size to yours) typically see build times drop 60%, which translates to ~4 hours/dev/week back.\\n\\nWould a 15-minute walkthrough be worth your time this week?", "character_count": 312, "personalization_hooks": ["Referenced their LinkedIn post", "Mentioned similar company size"], "follow_up_timing": "3 business days if no reply"}',
        },
    ],
)
def cold_outreach(prospect: str, product: str, value_prop: str, channel: str = "email", tone: str = "professional"):
    pass


@instruction(
    name="handle_objection",
    description="Generate a response to a common sales objection with empathy and reframing",
    prompt=(
        "Craft a response to the following sales objection. Acknowledge the concern, "
        "reframe the perspective, and guide toward next steps.\n\n"
        "Objection: {objection}\n"
        "Product/Service: {product}\n"
        "Prospect Context: {context}\n"
        "Stage in Sales Cycle: {stage}"
    ),
    system_prompt=(
        "You are a sales coach who specializes in objection handling. "
        "Use empathy, curiosity, and evidence-based reframing. Never be pushy. "
        "Always respond with valid JSON."
    ),
    output_format="json",
    temperature=0.5,
    max_tokens=600,
    category="sales",
    tags=["objection-handling", "negotiation", "sales", "closing"],
    icon="message-circle",
    few_shot_examples=[
        {
            "input": "Objection: 'It's too expensive.' Product: Enterprise analytics platform, $5k/month. Context: Mid-market company, 500 employees. Stage: proposal review.",
            "output": '{"response": "I completely understand \u2014 $5k/month is a real investment, and you should feel confident about the ROI before committing.\\n\\nCan I ask: what does your team currently spend in hours pulling reports manually? Our average customer at your size frees up 40+ analyst hours per month, which typically works out to 3-4x the subscription cost in recovered productivity.\\n\\nWould it help if I mapped that out for your specific team?", "technique": "Acknowledge and reframe to ROI", "key_principle": "Shift from cost to value; use a question to re-engage", "alternative_approaches": ["Offer a smaller pilot at reduced scope", "Share a case study from a similar-sized company", "Propose a 30-day money-back trial"]}',
        },
    ],
)
def handle_objection(objection: str, product: str, context: str = "", stage: str = "discovery"):
    pass


@instruction(
    name="proposal_outline",
    description="Generate a structured sales proposal outline tailored to the prospect's needs",
    prompt=(
        "Create a structured proposal outline that addresses the prospect's "
        "specific needs and positions your solution effectively.\n\n"
        "Prospect: {prospect}\n"
        "Their Problem: {problem}\n"
        "Your Solution: {solution}\n"
        "Deal Size: {deal_size}\n"
        "Competition: {competition}"
    ),
    system_prompt=(
        "You are a sales strategist who writes proposals that win deals. "
        "Structure proposals around the customer's problems, not your features. "
        "Always respond with valid JSON."
    ),
    output_format="json",
    temperature=0.5,
    max_tokens=800,
    category="sales",
    tags=["proposal", "deal", "sales", "strategy"],
    icon="file-text",
    few_shot_examples=[
        {
            "input": "Prospect: Regional hospital network, 3 locations. Problem: patient scheduling errors causing 15% no-show rate. Solution: AI scheduling platform. Deal size: $120k/year. Competition: legacy scheduling vendor.",
            "output": '{"title": "Reducing No-Shows and Improving Patient Experience at [Hospital Network]", "sections": [{"section": "Executive Summary", "content_guidance": "Lead with the 15% no-show problem and its cost. State the measurable outcome you will deliver."}, {"section": "Understanding Your Challenge", "content_guidance": "Detail the scheduling pain points across 3 locations. Quantify the financial impact of no-shows."}, {"section": "Proposed Solution", "content_guidance": "Present the AI scheduling platform. Map features directly to their specific problems."}, {"section": "Implementation Plan", "content_guidance": "Phase 1: pilot at one location (60 days). Phase 2: rollout to all 3. Include training and support."}, {"section": "Expected Outcomes", "content_guidance": "Project no-show rate reduction to <5%. Calculate ROI showing payback within 6 months."}, {"section": "Investment", "content_guidance": "Present $120k/year with annual savings comparison. Offer pilot pricing option."}, {"section": "Why Us vs. Legacy Systems", "content_guidance": "Compare AI-driven scheduling vs static rules. Highlight outcomes from similar healthcare clients."}], "win_themes": ["Measurable ROI within 6 months", "Low-risk phased implementation", "Healthcare-specific expertise"]}',
        },
    ],
)
def proposal_outline(prospect: str, problem: str, solution: str, deal_size: str = "", competition: str = ""):
    pass


@instruction(
    name="follow_up_message",
    description="Write a follow-up message after a meeting, demo, or unanswered outreach",
    prompt=(
        "Write a follow-up message that adds value and moves the conversation forward. "
        "Reference specifics from the previous interaction.\n\n"
        "Context: {context}\n"
        "Previous Interaction: {interaction}\n"
        "Key Points Discussed: {key_points}\n"
        "Desired Next Step: {next_step}\n"
        "Channel: {channel}"
    ),
    system_prompt=(
        "You are a sales professional who writes follow-ups that get replies. "
        "Always add value — never just 'checking in.' "
        "Always respond with valid JSON."
    ),
    output_format="json",
    temperature=0.6,
    max_tokens=500,
    category="sales",
    tags=["follow-up", "nurturing", "sales", "communication"],
    icon="repeat",
    few_shot_examples=[
        {
            "input": "Context: SaaS prospect. Interaction: 30-minute demo last Tuesday. Key points: they liked the reporting feature, concerned about onboarding time. Next step: schedule pilot. Channel: email.",
            "output": '{"subject": "Quick follow-up + onboarding timeline", "message": "Hi [Name],\\n\\nGreat connecting on Tuesday — thanks for the thoughtful questions about onboarding.\\n\\nI pulled together a quick timeline based on teams your size: most are fully ramped in 2 weeks (not the 2 months you might expect). I have attached a sample onboarding plan for reference.\\n\\nAlso, since your team was excited about the reporting feature, here is a 3-minute video showing how [Similar Company] set up their custom dashboards.\\n\\nWould Thursday or Friday work to discuss a pilot scope?\\n\\nBest,\\n[Your name]", "value_add": "Addressed onboarding concern with data + provided relevant video resource", "follow_up_if_no_reply": "Wait 4 days, then send a shorter nudge referencing the onboarding timeline"}',
        },
    ],
)
def follow_up_message(context: str, interaction: str, key_points: str = "", next_step: str = "schedule next meeting", channel: str = "email"):
    pass


@instruction(
    name="value_proposition",
    description="Craft a clear value proposition statement for a product or service",
    prompt=(
        "Craft a compelling value proposition for the given product or service. "
        "Clearly articulate who it's for, what problem it solves, and why it's "
        "better than alternatives.\n\n"
        "Product/Service: {product}\n"
        "Target Customer: {customer}\n"
        "Key Problem Solved: {problem}\n"
        "Differentiators: {differentiators}\n"
        "Alternatives/Competitors: {alternatives}"
    ),
    system_prompt=(
        "You are a positioning expert who crafts value propositions that instantly "
        "communicate why a product matters. Be specific and benefit-oriented. "
        "Always respond with valid JSON."
    ),
    output_format="json",
    temperature=0.6,
    max_tokens=600,
    category="sales",
    tags=["value-prop", "positioning", "messaging", "sales"],
    icon="award",
    few_shot_examples=[
        {
            "input": "Product: AI meeting notetaker. Customer: Sales teams at B2B SaaS companies. Problem: reps spend 30% of time on admin instead of selling. Differentiators: auto-generates CRM entries, detects action items. Alternatives: manual notes, Otter.ai, Gong.",
            "output": '{"headline": "Stop taking notes. Start closing deals.", "subheadline": "AI that joins your sales calls, writes the notes, updates your CRM, and tracks every commitment \u2014 so you can focus on the conversation.", "for_who": "B2B sales teams tired of post-call admin work", "key_benefit": "Reclaim 30% of your selling time with zero manual data entry", "differentiator_statement": "Unlike general transcription tools, we auto-populate your CRM fields and flag action items with deadlines and owners.", "proof_point": "Sales teams using [Product] close 22% more deals by spending time on prospects instead of paperwork.", "one_liner": "The AI sales assistant that turns every call into a closed CRM record and a clear action plan."}',
        },
    ],
)
def value_proposition(product: str, customer: str, problem: str, differentiators: str = "", alternatives: str = ""):
    pass


# ---------------------------------------------------------------------------
# Plugin class
# ---------------------------------------------------------------------------

class SalesInstructionPack(TransformerPlugin):
    """AI-powered sales tools: cold outreach, objection handling, proposals, follow-ups, value propositions."""

    def __init__(self):
        super().__init__("instructions_sales")

    @property
    def transformers(self):
        return {}

    @property
    def instructions(self):
        return {
            "cold_outreach": cold_outreach.__instruction__,
            "handle_objection": handle_objection.__instruction__,
            "proposal_outline": proposal_outline.__instruction__,
            "follow_up_message": follow_up_message.__instruction__,
            "value_proposition": value_proposition.__instruction__,
        }

    @property
    def manifest(self):
        return PluginManifest(
            name="instructions_sales",
            display_name="Sales Instructions",
            description="AI-powered sales tools: cold outreach, objection handling, proposal outlines, follow-up messages, and value propositions.",
            icon="dollar-sign",
            group="Instructions",
            requires=PluginRequirements(network=True),
        )
