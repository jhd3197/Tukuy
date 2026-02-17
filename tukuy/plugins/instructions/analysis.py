"""Analysis instruction pack -- AI-powered text analysis tools.

Provides instructions for sentiment analysis, entity extraction,
intent classification, action item extraction, and option comparison.
"""

from typing import Optional

from ...instruction import instruction
from ...manifest import PluginManifest, PluginRequirements
from ..base import TransformerPlugin


# ---------------------------------------------------------------------------
# Instructions
# ---------------------------------------------------------------------------

@instruction(
    name="analyze_sentiment",
    description="Analyze the sentiment of text as positive, negative, or neutral with confidence score",
    prompt=(
        "Analyze the sentiment of the following text. Determine if it is "
        "positive, negative, or neutral, and provide a confidence score "
        "from 0.0 to 1.0.\n\nText: {text}"
    ),
    system_prompt="You are a sentiment analysis expert. Always respond with valid JSON.",
    output_format="json",
    temperature=0.3,
    max_tokens=200,
    category="analysis",
    tags=["sentiment", "nlp", "analysis"],
    icon="bar-chart",
    few_shot_examples=[
        {
            "input": "I love this product! It exceeded all my expectations.",
            "output": '{"sentiment": "positive", "confidence": 0.95, "reasoning": "Strong positive language with emphatic praise"}',
        },
        {
            "input": "The service was okay, nothing special.",
            "output": '{"sentiment": "neutral", "confidence": 0.72, "reasoning": "Lukewarm assessment without strong positive or negative indicators"}',
        },
    ],
)
def analyze_sentiment(text: str):
    pass


@instruction(
    name="extract_entities",
    description="Extract named entities (people, organizations, locations, dates, amounts) from text",
    prompt=(
        "Extract all named entities from the following text. Identify people, "
        "organizations, locations, dates, and monetary amounts.\n\nText: {text}"
    ),
    system_prompt="You are a named entity recognition expert. Extract entities precisely. Always respond with valid JSON.",
    output_format="json",
    temperature=0.2,
    max_tokens=500,
    category="analysis",
    tags=["ner", "entities", "nlp", "analysis"],
    icon="search",
    few_shot_examples=[
        {
            "input": "Tim Cook announced that Apple will invest $1 billion in a new campus in Austin, Texas by March 2025.",
            "output": '{"entities": {"people": ["Tim Cook"], "organizations": ["Apple"], "locations": ["Austin, Texas"], "dates": ["March 2025"], "monetary_amounts": ["$1 billion"]}}',
        },
    ],
)
def extract_entities(text: str):
    pass


@instruction(
    name="classify_intent",
    description="Classify the intent of a user message and determine what action the user wants",
    prompt=(
        "Classify the intent of the following user message. Determine what "
        "action the user wants to perform.\n\nMessage: {message}"
    ),
    system_prompt="You are an intent classification expert. Respond with valid JSON containing the intent, confidence, extracted entities, and a suggested action.",
    output_format="json",
    temperature=0.3,
    max_tokens=300,
    category="analysis",
    tags=["intent", "classification", "nlp", "analysis"],
    icon="crosshair",
    few_shot_examples=[
        {
            "input": "Can you book me a flight to New York next Friday?",
            "output": '{"intent": "book_travel", "confidence": 0.93, "entities": {"destination": "New York", "date": "next Friday", "travel_type": "flight"}, "suggested_action": "Search for flights to New York for the upcoming Friday"}',
        },
    ],
)
def classify_intent(message: str):
    pass


@instruction(
    name="extract_action_items",
    description="Extract action items, tasks, and to-dos from meeting notes or conversations",
    prompt=(
        "Extract all action items, tasks, and to-dos from the following text. "
        "For each item, identify the assignee (if mentioned), the task description, "
        "the deadline (if mentioned), and the priority (high/medium/low).\n\nText: {text}"
    ),
    system_prompt="You are an expert at extracting actionable items from unstructured text. Always respond with valid JSON.",
    output_format="json",
    temperature=0.3,
    max_tokens=500,
    category="analysis",
    tags=["action-items", "tasks", "meetings", "analysis"],
    icon="check-square",
    few_shot_examples=[
        {
            "input": "John will send the proposal by Friday. Sarah needs to review the budget ASAP. We should schedule a follow-up meeting next week.",
            "output": '{"action_items": [{"assignee": "John", "task": "Send the proposal", "deadline": "Friday", "priority": "medium"}, {"assignee": "Sarah", "task": "Review the budget", "deadline": null, "priority": "high"}, {"assignee": "Team", "task": "Schedule a follow-up meeting", "deadline": "next week", "priority": "medium"}]}',
        },
    ],
)
def extract_action_items(text: str):
    pass


@instruction(
    name="compare_options",
    description="Create a decision matrix comparing options against criteria with scores from 1-10",
    prompt=(
        "Create a decision matrix comparing the given options against the "
        "specified criteria. Score each option from 1-10 for each criterion "
        "and provide a total weighted score.\n\n"
        "Options: {options}\n"
        "Criteria: {criteria}\n"
        "Context: {context}"
    ),
    system_prompt="You are a decision analysis expert. Create thorough, fair comparisons. Always respond with valid JSON.",
    output_format="json",
    temperature=0.5,
    max_tokens=800,
    category="analysis",
    tags=["decision", "comparison", "matrix", "analysis"],
    icon="columns",
    few_shot_examples=[
        {
            "input": "Options: Python, JavaScript, Go. Criteria: ease of learning, performance, ecosystem. Context: Choosing a language for a new web API.",
            "output": '{"matrix": {"Python": {"ease_of_learning": 9, "performance": 6, "ecosystem": 9}, "JavaScript": {"ease_of_learning": 7, "performance": 7, "ecosystem": 10}, "Go": {"ease_of_learning": 6, "performance": 9, "ecosystem": 6}}, "totals": {"Python": 24, "JavaScript": 24, "Go": 21}, "recommendation": "Python and JavaScript are tied; Python is recommended for its strong web framework ecosystem (Django, FastAPI)."}',
        },
    ],
)
def compare_options(options: str, criteria: str, context: str = ""):
    pass


# ---------------------------------------------------------------------------
# Plugin class
# ---------------------------------------------------------------------------

class AnalysisInstructionPack(TransformerPlugin):
    """AI-powered text analysis instructions: sentiment, entities, intent, action items, comparison."""

    def __init__(self):
        super().__init__("instructions_analysis")

    @property
    def transformers(self):
        return {}

    @property
    def instructions(self):
        return {
            "analyze_sentiment": analyze_sentiment.__instruction__,
            "extract_entities": extract_entities.__instruction__,
            "classify_intent": classify_intent.__instruction__,
            "extract_action_items": extract_action_items.__instruction__,
            "compare_options": compare_options.__instruction__,
        }

    @property
    def manifest(self):
        return PluginManifest(
            name="instructions_analysis",
            display_name="Analysis Instructions",
            description="AI-powered text analysis: sentiment, entities, intent, action items, and decision comparison.",
            icon="brain",
            group="Instructions",
            requires=PluginRequirements(network=True),
        )
