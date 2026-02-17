"""Creative instruction pack -- AI-powered creative content tools.

Provides instructions for brainstorming, tagline generation, creative briefs,
story prompts, and content rewriting with creative flair.
"""

from ...instruction import instruction
from ...manifest import PluginManifest, PluginRequirements
from ..base import TransformerPlugin


# ---------------------------------------------------------------------------
# Instructions
# ---------------------------------------------------------------------------

@instruction(
    name="brainstorm_ideas",
    description="Generate creative ideas for a project, campaign, or problem",
    prompt=(
        "Brainstorm creative ideas for the following challenge. Generate diverse, "
        "original ideas ranging from practical to bold. Organize by feasibility.\n\n"
        "Challenge: {challenge}\n"
        "Context: {context}\n"
        "Constraints: {constraints}\n"
        "Number of Ideas: {num_ideas}"
    ),
    system_prompt=(
        "You are a creative director who leads brainstorming sessions at top agencies. "
        "Generate diverse ideas — some safe, some bold, some wild. "
        "Always respond with valid JSON."
    ),
    output_format="json",
    temperature=0.9,
    max_tokens=800,
    category="creative",
    tags=["brainstorm", "ideas", "creative", "innovation"],
    icon="zap",
    few_shot_examples=[
        {
            "input": "Challenge: Launch event for a new coffee brand. Context: premium, single-origin, targeting young professionals. Constraints: $10k budget. Ideas: 5.",
            "output": '{"ideas": [{"idea": "Pop-Up \u2018Origin Stories\u2019 Tasting Bar", "description": "Set up a minimalist tasting bar in a high-traffic co-working space. Each cup comes with a card telling the farmer\u2019s story.", "feasibility": "high", "estimated_cost": "$3,000-5,000"}, {"idea": "Morning Commute Coffee Handout", "description": "Station baristas at 3 transit hubs during morning rush. Hand out free samples in branded reusable cups with a QR code to subscribe.", "feasibility": "high", "estimated_cost": "$2,000-4,000"}, {"idea": "\u2018Blind Taste Test\u2019 Social Challenge", "description": "Film influencers doing blind taste tests comparing your brand to major chains. Post as short-form video series.", "feasibility": "medium", "estimated_cost": "$3,000-5,000"}, {"idea": "AR Coffee Bean Journey", "description": "Scan the bag\u2019s QR code to see an AR experience of the bean\u2019s journey from farm to cup.", "feasibility": "low", "estimated_cost": "$8,000-15,000"}, {"idea": "Subscription-Only Secret Menu", "description": "Launch with a \u2018secret menu\u2019 available only to first 500 subscribers. Create FOMO and exclusivity.", "feasibility": "high", "estimated_cost": "$1,000-2,000"}], "recommended_combination": "Combine the pop-up tasting bar with the social challenge for maximum impact within budget."}',
        },
    ],
)
def brainstorm_ideas(challenge: str, context: str = "", constraints: str = "", num_ideas: str = "5"):
    pass


@instruction(
    name="generate_tagline",
    description="Generate catchy taglines or slogans for a brand, product, or campaign",
    prompt=(
        "Generate tagline options for the following brand, product, or campaign. "
        "Vary styles: some short and punchy, some clever, some emotional.\n\n"
        "Brand/Product: {brand}\n"
        "Key Message: {message}\n"
        "Target Audience: {audience}\n"
        "Tone: {tone}\n"
        "Number of Options: {num_options}"
    ),
    system_prompt=(
        "You are a branding expert who has written iconic taglines. "
        "Create memorable, concise taglines that capture the essence of the brand. "
        "Always respond with valid JSON."
    ),
    output_format="json",
    temperature=0.9,
    max_tokens=500,
    category="creative",
    tags=["tagline", "slogan", "branding", "creative"],
    icon="type",
    few_shot_examples=[
        {
            "input": "Brand: Fitness app for busy parents. Message: quick effective workouts that fit your life. Audience: parents aged 30-45. Tone: motivating but realistic. Options: 5.",
            "output": '{"taglines": [{"tagline": "Fit in 15.", "style": "short and punchy", "rationale": "Implies both fitting into your schedule and getting fit, in just 15 minutes."}, {"tagline": "Your kids have a bedtime. So does your workout.", "style": "clever/relatable", "rationale": "Speaks directly to the parent experience with humor."}, {"tagline": "Strong parents raise strong kids.", "style": "emotional", "rationale": "Connects personal fitness to parenting purpose."}, {"tagline": "No gym. No nanny. No excuses.", "style": "bold/direct", "rationale": "Acknowledges real obstacles while removing them."}, {"tagline": "The workout that works around you.", "style": "descriptive", "rationale": "Clearly communicates the core value proposition."}], "top_pick": "Fit in 15.", "reasoning": "Maximum memorability with minimal words. Works as campaign name, hashtag, and app tagline."}',
        },
    ],
)
def generate_tagline(brand: str, message: str, audience: str = "general", tone: str = "versatile", num_options: str = "5"):
    pass


@instruction(
    name="creative_brief",
    description="Write a creative brief for a marketing campaign or design project",
    prompt=(
        "Write a creative brief for the following project. Include all essential "
        "sections that the creative team needs to execute effectively.\n\n"
        "Project: {project}\n"
        "Client/Brand: {brand}\n"
        "Objective: {objective}\n"
        "Target Audience: {audience}\n"
        "Budget: {budget}\n"
        "Timeline: {timeline}"
    ),
    system_prompt=(
        "You are a creative strategist who writes briefs that inspire great work. "
        "Be clear about objectives while leaving room for creative interpretation. "
        "Always respond with valid JSON."
    ),
    output_format="json",
    temperature=0.6,
    max_tokens=800,
    category="creative",
    tags=["brief", "campaign", "creative", "strategy"],
    icon="file-text",
    few_shot_examples=[
        {
            "input": "Project: Holiday email campaign. Brand: Artisan candle company. Objective: drive 30% sales increase during December. Audience: women 25-45 who value self-care. Budget: $5k. Timeline: 3 weeks.",
            "output": '{"project_name": "Holiday Glow Campaign", "background": "Artisan candle brand known for hand-poured, small-batch candles. Previous holiday campaigns saw 15% lift; this year we\u2019re targeting 30%.", "objective": "Drive a 30% increase in December sales through a 4-email holiday sequence.", "target_audience": {"demographic": "Women 25-45", "psychographic": "Values self-care, intentional living, and meaningful gifting", "insight": "She doesn\u2019t want another generic gift guide \u2014 she wants permission to treat herself."}, "key_message": "This season, the most thoughtful gift is the one you give yourself.", "tone_and_style": "Warm, intimate, and indulgent \u2014 like the feeling of lighting a candle on a cold evening.", "deliverables": ["4-email sequence (teaser, launch, mid-month, last chance)", "Email hero images (lifestyle photography style)", "Subject lines and preview text for each email"], "mandatories": ["Include holiday gift bundles", "Link to gift guide landing page", "Unsubscribe and compliance footer"], "budget": "$5,000", "timeline": "Brief approved: Week 1. Creative: Week 2. QA and send: Week 3.", "success_metrics": ["30% revenue lift vs. last December", "25%+ open rate", "3%+ click-through rate"]}',
        },
    ],
)
def creative_brief(project: str, brand: str, objective: str, audience: str = "", budget: str = "", timeline: str = ""):
    pass


@instruction(
    name="story_prompt",
    description="Generate a detailed creative writing prompt or story starter",
    prompt=(
        "Generate a creative writing prompt or story starter. Include setting, "
        "character seeds, conflict, and a hook that compels the writer to continue.\n\n"
        "Genre: {genre}\n"
        "Theme: {theme}\n"
        "Mood: {mood}\n"
        "Complexity: {complexity}"
    ),
    system_prompt=(
        "You are a creative writing instructor who designs prompts that ignite imagination. "
        "Create prompts that are specific enough to inspire but open enough for interpretation. "
        "Always respond with valid JSON."
    ),
    output_format="json",
    temperature=0.9,
    max_tokens=600,
    category="creative",
    tags=["writing", "story", "prompt", "creative"],
    icon="feather",
    few_shot_examples=[
        {
            "input": "Genre: science fiction. Theme: what makes us human. Mood: contemplative. Complexity: medium.",
            "output": '{"prompt": "In 2087, synthetic humans are indistinguishable from biological ones \u2014 except for one thing: they don\u2019t dream. When a synthetic named Mira wakes up from what she can only describe as a dream, she must decide whether to report it to the corporation that made her or keep the secret that could change everything.", "setting": "Near-future Earth where synthetics and humans coexist uneasily in a stratified society", "characters": [{"name": "Mira", "description": "A synthetic social worker who has always accepted her nature \u2014 until now"}, {"name": "Dr. Okafor", "description": "Mira\u2019s maintenance technician who suspects something has changed"}], "central_conflict": "Self-discovery vs. self-preservation in a world that fears what it cannot control", "opening_line": "The first thing Mira saw when she opened her eyes was a field of sunflowers she had never visited.", "writing_tips": ["Explore the dream through sensory details", "Let Mira\u2019s internal debate drive the first act", "Consider what \u2018dreaming\u2019 symbolizes for both synthetics and humans"]}',
        },
    ],
)
def story_prompt(genre: str, theme: str = "", mood: str = "open", complexity: str = "medium"):
    pass


@instruction(
    name="creative_rewrite",
    description="Rewrite text with a different creative style, voice, or perspective",
    prompt=(
        "Rewrite the following text in the specified creative style. Maintain the "
        "core message but transform the voice, imagery, and energy.\n\n"
        "Original Text: {text}\n"
        "Target Style: {style}\n"
        "Additional Guidance: {guidance}"
    ),
    system_prompt=(
        "You are a versatile writer who can adopt any voice or style. "
        "Transform text while preserving its essential meaning. "
        "Always respond with valid JSON."
    ),
    output_format="json",
    temperature=0.8,
    max_tokens=800,
    category="creative",
    tags=["rewrite", "style", "voice", "creative"],
    icon="edit-3",
    few_shot_examples=[
        {
            "input": "Text: 'Our software helps businesses track their expenses and save money.' Style: storytelling/narrative. Guidance: make it feel personal.",
            "output": '{"rewritten": "Last March, Sarah spent her Sunday afternoon hunched over a spreadsheet, reconciling three months of receipts for her bakery. By the time she finished, it was dark, the kids were in bed, and she\u2019d found $2,300 in expenses she\u2019d completely missed.\\n\\nThat was the last Sunday she spent on spreadsheets.\\n\\nNow, every expense is tracked the moment it happens. Sarah spends her Sundays where she belongs \u2014 taste-testing new recipes with her kids.", "style_applied": "Narrative storytelling with emotional arc", "techniques_used": ["Specific character and scenario", "Before/after contrast", "Sensory and emotional details", "Implied product benefit without naming it"], "word_count": 82}',
        },
    ],
)
def creative_rewrite(text: str, style: str, guidance: str = ""):
    pass


# ---------------------------------------------------------------------------
# Plugin class
# ---------------------------------------------------------------------------

class CreativeInstructionPack(TransformerPlugin):
    """AI-powered creative tools: brainstorming, taglines, creative briefs, story prompts, creative rewrites."""

    def __init__(self):
        super().__init__("instructions_creative")

    @property
    def transformers(self):
        return {}

    @property
    def instructions(self):
        return {
            "brainstorm_ideas": brainstorm_ideas.__instruction__,
            "generate_tagline": generate_tagline.__instruction__,
            "creative_brief": creative_brief.__instruction__,
            "story_prompt": story_prompt.__instruction__,
            "creative_rewrite": creative_rewrite.__instruction__,
        }

    @property
    def manifest(self):
        return PluginManifest(
            name="instructions_creative",
            display_name="Creative Instructions",
            description="AI-powered creative tools: brainstorming, tagline generation, creative briefs, story prompts, and creative rewrites.",
            icon="pen-tool",
            group="Instructions",
            requires=PluginRequirements(network=True),
        )
