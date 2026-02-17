"""Marketing instruction pack -- AI-powered marketing tools.

Provides instructions for copywriting, SEO content, ad copy generation,
brand voice auditing, and product description writing.
"""

from ...instruction import instruction
from ...manifest import PluginManifest, PluginRequirements
from ..base import TransformerPlugin


# ---------------------------------------------------------------------------
# Instructions
# ---------------------------------------------------------------------------

@instruction(
    name="generate_marketing_copy",
    description="Generate persuasive marketing copy for a product or service",
    prompt=(
        "Write persuasive marketing copy for the following product or service. "
        "Target the specified audience and use the indicated tone.\n\n"
        "Product/Service: {product}\n"
        "Target Audience: {audience}\n"
        "Tone: {tone}\n"
        "Goal: {goal}"
    ),
    system_prompt=(
        "You are an expert copywriter with decades of experience in direct response "
        "and brand marketing. Write compelling copy that drives action. "
        "Always respond with valid JSON."
    ),
    output_format="json",
    temperature=0.7,
    max_tokens=800,
    category="marketing",
    tags=["copywriting", "marketing", "content"],
    icon="megaphone",
    few_shot_examples=[
        {
            "input": "Product: Eco-friendly water bottle. Audience: health-conscious millennials. Tone: casual and inspiring. Goal: drive pre-orders.",
            "output": '{"headline": "Hydrate the Planet, One Sip at a Time", "subheadline": "The last water bottle you\'ll ever need — and the Earth will thank you for it.", "body": "Made from 100% recycled ocean plastic, our bottle keeps your drinks cold for 24 hours and hot for 12. No BPA, no guilt, no compromise.", "cta": "Pre-order now and get 30% off — limited to the first 500 bottles."}',
        },
    ],
)
def generate_marketing_copy(product: str, audience: str, tone: str = "professional", goal: str = "increase awareness"):
    pass


@instruction(
    name="seo_content_brief",
    description="Create an SEO-optimized content brief with keywords, headings, and structure",
    prompt=(
        "Create an SEO content brief for a blog post or article on the given topic. "
        "Include target keywords, suggested headings, word count recommendation, "
        "and content structure.\n\n"
        "Topic: {topic}\n"
        "Primary Keyword: {keyword}\n"
        "Target Audience: {audience}"
    ),
    system_prompt=(
        "You are an SEO content strategist. Create detailed content briefs that "
        "balance search engine optimization with reader value. "
        "Always respond with valid JSON."
    ),
    output_format="json",
    temperature=0.4,
    max_tokens=800,
    category="marketing",
    tags=["seo", "content-strategy", "marketing", "keywords"],
    icon="search",
    few_shot_examples=[
        {
            "input": "Topic: remote work productivity tips. Keyword: remote work productivity. Audience: remote workers and managers.",
            "output": '{"primary_keyword": "remote work productivity", "secondary_keywords": ["work from home tips", "remote team efficiency", "home office setup"], "suggested_title": "15 Proven Remote Work Productivity Tips for 2025", "headings": ["H2: Set Up a Dedicated Workspace", "H2: Establish a Morning Routine", "H2: Use Time-Blocking Techniques", "H2: Minimize Digital Distractions", "H2: Communicate Proactively with Your Team"], "word_count": "1800-2200", "content_notes": "Include statistics on remote work trends. Add practical examples and actionable takeaways in each section."}',
        },
    ],
)
def seo_content_brief(topic: str, keyword: str, audience: str = "general"):
    pass


@instruction(
    name="generate_ad_copy",
    description="Generate ad copy variants for digital advertising platforms",
    prompt=(
        "Create ad copy variants for the specified platform. Include headlines, "
        "descriptions, and calls to action optimized for the platform's character limits.\n\n"
        "Product/Service: {product}\n"
        "Platform: {platform}\n"
        "Campaign Goal: {goal}\n"
        "Key Selling Points: {selling_points}"
    ),
    system_prompt=(
        "You are a performance marketing expert specializing in digital ad copy. "
        "Write concise, high-converting ad variants that respect platform character limits. "
        "Always respond with valid JSON."
    ),
    output_format="json",
    temperature=0.7,
    max_tokens=800,
    category="marketing",
    tags=["advertising", "ads", "ppc", "marketing"],
    icon="zap",
    few_shot_examples=[
        {
            "input": "Product: Online coding bootcamp. Platform: Google Ads. Goal: drive enrollments. Key Selling Points: 12-week program, job guarantee, flexible schedule.",
            "output": '{"variants": [{"headline_1": "Learn to Code in 12 Weeks", "headline_2": "Job Guarantee Included", "description": "Flexible online bootcamp with a money-back job guarantee. Start your tech career today. Enroll now.", "cta": "Enroll Now"}, {"headline_1": "Career Change? Start Coding", "headline_2": "12-Week Bootcamp | Flex Hours", "description": "Go from beginner to job-ready developer. Our grads land roles in 90 days. Limited spots available.", "cta": "Apply Today"}]}',
        },
    ],
)
def generate_ad_copy(product: str, platform: str, goal: str, selling_points: str):
    pass


@instruction(
    name="brand_voice_audit",
    description="Audit text for brand voice consistency and suggest improvements",
    prompt=(
        "Audit the following text for brand voice consistency. Evaluate tone, "
        "vocabulary, and messaging alignment with the described brand voice. "
        "Suggest specific improvements.\n\n"
        "Text: {text}\n"
        "Brand Voice Description: {brand_voice}\n"
        "Brand Values: {values}"
    ),
    system_prompt=(
        "You are a brand strategist and communications expert. Analyze text for "
        "brand voice consistency with precision. Always respond with valid JSON."
    ),
    output_format="json",
    temperature=0.4,
    max_tokens=800,
    category="marketing",
    tags=["brand", "voice", "consistency", "marketing"],
    icon="mic",
    few_shot_examples=[
        {
            "input": "Text: 'Buy our stuff, it's great!' Brand Voice: warm, knowledgeable, premium. Values: quality, craftsmanship, sustainability.",
            "output": '{"overall_score": 3, "max_score": 10, "tone_match": "poor", "issues": [{"text": "Buy our stuff", "issue": "Too casual and aggressive for a premium brand", "suggestion": "Discover our curated collection"}, {"text": "it\'s great", "issue": "Vague and informal; lacks the knowledgeable voice", "suggestion": "crafted with meticulous attention to detail"}], "rewritten": "Discover our curated collection — crafted with meticulous attention to detail and a commitment to sustainability."}',
        },
    ],
)
def brand_voice_audit(text: str, brand_voice: str, values: str = ""):
    pass


@instruction(
    name="product_description",
    description="Write a compelling product description optimized for e-commerce",
    prompt=(
        "Write a compelling product description for e-commerce. Include a hook, "
        "key features, benefits, and a closing that encourages purchase.\n\n"
        "Product Name: {name}\n"
        "Product Details: {details}\n"
        "Target Customer: {customer}\n"
        "Tone: {tone}"
    ),
    system_prompt=(
        "You are an e-commerce copywriter who writes product descriptions that "
        "convert browsers into buyers. Focus on benefits over features. "
        "Always respond with valid JSON."
    ),
    output_format="json",
    temperature=0.6,
    max_tokens=600,
    category="marketing",
    tags=["product", "ecommerce", "description", "marketing"],
    icon="shopping-bag",
    few_shot_examples=[
        {
            "input": "Name: CloudWalk Running Shoes. Details: lightweight, carbon-fiber plate, breathable mesh, 8mm drop. Customer: serious runners. Tone: energetic and technical.",
            "output": '{"hook": "Engineered for runners who refuse to slow down.", "features": ["Carbon-fiber propulsion plate for explosive toe-off", "Ultralight breathable mesh upper (220g)", "8mm heel-to-toe drop for natural stride", "High-rebound EVA midsole"], "benefits": "Shave seconds off your PR while keeping your feet cool and supported from mile 1 to mile 26.2.", "closing": "Lace up. Lock in. Leave them behind.", "seo_keywords": ["carbon plate running shoes", "lightweight marathon shoes"]}',
        },
    ],
)
def product_description(name: str, details: str, customer: str = "general consumers", tone: str = "professional"):
    pass


# ---------------------------------------------------------------------------
# Plugin class
# ---------------------------------------------------------------------------

class MarketingInstructionPack(TransformerPlugin):
    """AI-powered marketing tools: copy, SEO briefs, ad copy, brand voice audit, product descriptions."""

    def __init__(self):
        super().__init__("instructions_marketing")

    @property
    def transformers(self):
        return {}

    @property
    def instructions(self):
        return {
            "generate_marketing_copy": generate_marketing_copy.__instruction__,
            "seo_content_brief": seo_content_brief.__instruction__,
            "generate_ad_copy": generate_ad_copy.__instruction__,
            "brand_voice_audit": brand_voice_audit.__instruction__,
            "product_description": product_description.__instruction__,
        }

    @property
    def manifest(self):
        return PluginManifest(
            name="instructions_marketing",
            display_name="Marketing Instructions",
            description="AI-powered marketing tools: copywriting, SEO content briefs, ad copy, brand voice auditing, and product descriptions.",
            icon="megaphone",
            group="Instructions",
            requires=PluginRequirements(network=True),
        )
