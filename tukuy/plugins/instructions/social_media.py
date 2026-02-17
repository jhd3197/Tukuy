"""Social media instruction pack -- AI-powered social media tools.

Provides instructions for post generation, hashtag strategy, caption writing,
engagement analysis, and content calendar planning.
"""

from ...instruction import instruction
from ...manifest import PluginManifest, PluginRequirements
from ..base import TransformerPlugin


# ---------------------------------------------------------------------------
# Instructions
# ---------------------------------------------------------------------------

@instruction(
    name="generate_social_post",
    description="Generate a social media post optimized for a specific platform",
    prompt=(
        "Write a social media post optimized for the specified platform. "
        "Follow platform best practices for length, tone, and formatting.\n\n"
        "Platform: {platform}\n"
        "Topic: {topic}\n"
        "Goal: {goal}\n"
        "Brand Voice: {voice}"
    ),
    system_prompt=(
        "You are a social media strategist who creates viral, engaging content. "
        "Tailor each post to platform-specific best practices and character limits. "
        "Always respond with valid JSON."
    ),
    output_format="json",
    temperature=0.8,
    max_tokens=600,
    category="social_media",
    tags=["social-media", "content", "posts", "marketing"],
    icon="share-2",
    few_shot_examples=[
        {
            "input": "Platform: LinkedIn. Topic: launching a new AI product. Goal: drive sign-ups. Voice: professional but approachable.",
            "output": '{"post": "We\u2019ve been quietly building something for the past 8 months.\\n\\nToday, we\u2019re launching SmartDraft \u2014 an AI writing assistant that actually understands your industry.\\n\\nNo generic outputs. No hallucinated facts. Just sharp, context-aware drafts that save our beta users 6+ hours per week.\\n\\n\ud83d\udc49 Early access is open (link in comments)\\n\\nWould love to hear what you\u2019d use it for.", "character_count": 340, "hashtags": ["#AI", "#ProductLaunch", "#Productivity"], "best_time_to_post": "Tuesday-Thursday, 8-10 AM", "engagement_tip": "Ask a question at the end to boost comments."}',
        },
    ],
)
def generate_social_post(platform: str, topic: str, goal: str = "engagement", voice: str = "professional"):
    pass


@instruction(
    name="hashtag_strategy",
    description="Generate a hashtag strategy with categorized tags for reach and engagement",
    prompt=(
        "Create a hashtag strategy for the given topic and platform. Categorize "
        "hashtags by reach (broad, medium, niche) and provide usage guidance.\n\n"
        "Topic: {topic}\n"
        "Platform: {platform}\n"
        "Industry: {industry}\n"
        "Content Type: {content_type}"
    ),
    system_prompt=(
        "You are a social media growth expert specializing in hashtag strategy. "
        "Mix broad reach tags with niche ones for optimal discovery. "
        "Always respond with valid JSON."
    ),
    output_format="json",
    temperature=0.5,
    max_tokens=600,
    category="social_media",
    tags=["hashtags", "social-media", "growth", "marketing"],
    icon="hash",
    few_shot_examples=[
        {
            "input": "Topic: sustainable fashion. Platform: Instagram. Industry: fashion/retail. Content type: product showcase.",
            "output": '{"broad_reach": ["#SustainableFashion", "#EcoFriendly", "#SlowFashion", "#Sustainability"], "medium_reach": ["#EthicalClothing", "#ConsciousStyle", "#GreenFashion", "#SustainableLiving"], "niche": ["#WhoMadeMyClothes", "#FashionRevolution", "#UpcycledFashion", "#ZeroWasteFashion"], "recommended_count": "8-12 hashtags for Instagram", "strategy": "Lead with 2-3 broad tags for reach, 3-4 medium for targeted discovery, and 3-4 niche for community engagement. Rotate sets weekly to avoid shadowban risk."}',
        },
    ],
)
def hashtag_strategy(topic: str, platform: str = "Instagram", industry: str = "", content_type: str = "general"):
    pass


@instruction(
    name="write_caption",
    description="Write an engaging caption for an image or video post",
    prompt=(
        "Write an engaging caption for a social media image or video. "
        "Include a hook, body, and call to action.\n\n"
        "Content Description: {description}\n"
        "Platform: {platform}\n"
        "Mood/Vibe: {mood}\n"
        "Call to Action: {cta}"
    ),
    system_prompt=(
        "You are a content creator known for captions that stop the scroll. "
        "Write captions that create curiosity and drive engagement. "
        "Always respond with valid JSON."
    ),
    output_format="json",
    temperature=0.8,
    max_tokens=500,
    category="social_media",
    tags=["captions", "social-media", "content", "marketing"],
    icon="type",
    few_shot_examples=[
        {
            "input": "Description: behind-the-scenes photo of team working late on product launch. Platform: Instagram. Mood: excited, authentic. CTA: follow for launch updates.",
            "output": '{"caption": "11:47 PM and the whiteboard is still full.\\n\\nThis is what shipping something you believe in looks like. No filters, just caffeine and conviction.\\n\\nBig things dropping soon. Hit follow so you don\u2019t miss it \u2192", "hook": "11:47 PM and the whiteboard is still full.", "character_count": 198, "emoji_suggestions": ["\ud83d\ude80", "\u2615", "\ud83d\udca1"]}',
        },
    ],
)
def write_caption(description: str, platform: str = "Instagram", mood: str = "engaging", cta: str = ""):
    pass


@instruction(
    name="analyze_engagement",
    description="Analyze social media metrics and suggest improvements for engagement",
    prompt=(
        "Analyze the following social media performance metrics and provide "
        "actionable insights to improve engagement.\n\n"
        "Platform: {platform}\n"
        "Metrics: {metrics}\n"
        "Content Type: {content_type}\n"
        "Time Period: {period}"
    ),
    system_prompt=(
        "You are a social media analytics expert. Interpret metrics in context "
        "and provide specific, actionable recommendations. "
        "Always respond with valid JSON."
    ),
    output_format="json",
    temperature=0.4,
    max_tokens=800,
    category="social_media",
    tags=["analytics", "engagement", "social-media", "marketing"],
    icon="bar-chart-2",
    few_shot_examples=[
        {
            "input": "Platform: Instagram. Metrics: 2.1% engagement rate, 500 avg likes, 12 avg comments, 3% reach rate, best post was a carousel. Content type: mix of reels, carousels, static images. Period: last 30 days.",
            "output": '{"assessment": "Above-average engagement rate (industry avg ~1.2%) but low comment-to-like ratio suggests passive consumption.", "insights": ["Carousels outperforming suggests audience prefers educational/swipeable content", "Low comment ratio (2.4%) indicates content isn\'t prompting conversation", "3% reach rate is healthy for organic content"], "recommendations": ["Double down on carousel format — aim for 3-4 per week", "End every post with a specific question to boost comments", "Test Reels under 15 seconds for algorithm boost", "Post between 6-8 PM when engagement historically peaks"], "priority_action": "Add a question-based CTA to every post this week and measure comment lift."}',
        },
    ],
)
def analyze_engagement(platform: str, metrics: str, content_type: str = "", period: str = "last 30 days"):
    pass


@instruction(
    name="content_calendar",
    description="Generate a weekly or monthly social media content calendar",
    prompt=(
        "Create a content calendar for the specified time period. Include post "
        "types, topics, platforms, and suggested posting times.\n\n"
        "Brand/Business: {brand}\n"
        "Platforms: {platforms}\n"
        "Time Period: {period}\n"
        "Content Themes: {themes}\n"
        "Posting Frequency: {frequency}"
    ),
    system_prompt=(
        "You are a social media content planner. Create balanced, strategic calendars "
        "that mix content types for consistent engagement. "
        "Always respond with valid JSON."
    ),
    output_format="json",
    temperature=0.6,
    max_tokens=1000,
    category="social_media",
    tags=["content-calendar", "planning", "social-media", "marketing"],
    icon="calendar",
    few_shot_examples=[
        {
            "input": "Brand: fitness coaching business. Platforms: Instagram, TikTok. Period: 1 week. Themes: workouts, nutrition tips, client transformations, motivation. Frequency: daily on Instagram, 3x on TikTok.",
            "output": '{"calendar": [{"day": "Monday", "posts": [{"platform": "Instagram", "type": "Carousel", "topic": "5 Quick Morning Stretches", "theme": "workouts", "time": "7:00 AM"}, {"platform": "TikTok", "type": "Short video", "topic": "Morning routine in 30 seconds", "theme": "workouts", "time": "12:00 PM"}]}, {"day": "Tuesday", "posts": [{"platform": "Instagram", "type": "Story poll", "topic": "What\'s your biggest nutrition struggle?", "theme": "nutrition", "time": "11:00 AM"}]}, {"day": "Wednesday", "posts": [{"platform": "Instagram", "type": "Reel", "topic": "3-ingredient protein smoothie", "theme": "nutrition", "time": "6:00 PM"}, {"platform": "TikTok", "type": "Short video", "topic": "Meal prep hack of the week", "theme": "nutrition", "time": "7:00 PM"}]}], "content_mix": {"educational": "40%", "inspirational": "25%", "promotional": "15%", "behind_the_scenes": "20%"}}',
        },
    ],
)
def content_calendar(brand: str, platforms: str, period: str = "1 week", themes: str = "", frequency: str = "daily"):
    pass


# ---------------------------------------------------------------------------
# Plugin class
# ---------------------------------------------------------------------------

class SocialMediaInstructionPack(TransformerPlugin):
    """AI-powered social media tools: post generation, hashtags, captions, engagement analysis, content calendars."""

    def __init__(self):
        super().__init__("instructions_social_media")

    @property
    def transformers(self):
        return {}

    @property
    def instructions(self):
        return {
            "generate_social_post": generate_social_post.__instruction__,
            "hashtag_strategy": hashtag_strategy.__instruction__,
            "write_caption": write_caption.__instruction__,
            "analyze_engagement": analyze_engagement.__instruction__,
            "content_calendar": content_calendar.__instruction__,
        }

    @property
    def manifest(self):
        return PluginManifest(
            name="instructions_social_media",
            display_name="Social Media Instructions",
            description="AI-powered social media tools: post generation, hashtag strategy, caption writing, engagement analysis, and content calendars.",
            icon="share-2",
            group="Instructions",
            requires=PluginRequirements(network=True),
        )
