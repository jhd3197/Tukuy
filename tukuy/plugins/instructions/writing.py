"""Writing instruction pack -- AI-powered writing and language tools.

Provides instructions for translation, tone rewriting, summarization,
email generation, and proofreading.
"""

from typing import Optional

from ...instruction import instruction
from ...manifest import PluginManifest, PluginRequirements
from ..base import TransformerPlugin


# ---------------------------------------------------------------------------
# Instructions
# ---------------------------------------------------------------------------

@instruction(
    name="translate_text",
    description="Translate text to a target language while preserving tone, style, and formatting",
    prompt=(
        "Translate the following text to {target_language}. Preserve the "
        "original tone, style, and formatting.\n\nText: {text}"
    ),
    system_prompt="You are an expert translator. Preserve meaning, tone, and cultural nuances. Output only the translated text.",
    output_format="text",
    temperature=0.3,
    max_tokens=1000,
    category="writing",
    tags=["translation", "language", "writing"],
    icon="globe",
)
def translate_text(text: str, target_language: str):
    pass


@instruction(
    name="rewrite_tone",
    description="Rewrite text in a specified tone (formal, casual, friendly, professional, academic, humorous)",
    prompt=(
        "Rewrite the following text in a {tone} tone. Keep the same meaning "
        "and key information but adjust the language, word choice, and style "
        "to match the requested tone.\n\nText: {text}"
    ),
    system_prompt="You are an expert writer who can adapt any text to different tones. Output only the rewritten text.",
    output_format="text",
    temperature=0.7,
    max_tokens=1000,
    category="writing",
    tags=["rewrite", "tone", "style", "writing"],
    icon="edit-3",
)
def rewrite_tone(text: str, tone: str):
    pass


@instruction(
    name="summarize_document",
    description="Summarize text into concise key points",
    prompt=(
        "Summarize the following text into at most {max_points} key points. "
        "Be concise but do not miss important details.\n\nText: {text}"
    ),
    system_prompt="You are an expert summarizer. Distill information into clear, actionable key points.",
    output_format="list",
    temperature=0.3,
    max_tokens=500,
    category="writing",
    tags=["summary", "key-points", "writing"],
    icon="file-text",
)
def summarize_document(text: str, max_points: str = "5"):
    pass


@instruction(
    name="generate_email",
    description="Draft a professional email from bullet points and context",
    prompt=(
        "Draft a professional email based on the following details.\n\n"
        "Subject: {subject}\n"
        "Key points to cover:\n{points}\n"
        "Tone: {tone}\n"
        "Recipient context: {recipient_context}"
    ),
    system_prompt="You are an expert business communicator. Write clear, well-structured emails. Include a subject line, greeting, body, and sign-off.",
    output_format="markdown",
    temperature=0.6,
    max_tokens=800,
    category="writing",
    tags=["email", "business", "communication", "writing"],
    icon="mail",
)
def generate_email(subject: str, points: str, tone: str, recipient_context: str):
    pass


@instruction(
    name="proofread",
    description="Proofread text for grammar, spelling, punctuation, and style issues",
    prompt=(
        "Proofread the following text. Fix grammar, spelling, punctuation, "
        "and style issues. Return the corrected text along with a list of "
        "every change you made and why.\n\nText: {text}"
    ),
    system_prompt="You are a professional proofreader and copy editor. Be thorough but preserve the author's voice. Always respond with valid JSON.",
    output_format="json",
    temperature=0.2,
    max_tokens=1000,
    category="writing",
    tags=["proofread", "grammar", "spelling", "writing"],
    icon="check-circle",
    few_shot_examples=[
        {
            "input": "Their going to the store to by there grocerys.",
            "output": '{"corrected_text": "They\'re going to the store to buy their groceries.", "changes": [{"original": "Their", "corrected": "They\'re", "reason": "Contraction of they are, not possessive their"}, {"original": "by", "corrected": "buy", "reason": "Incorrect homophone; buy means to purchase"}, {"original": "there", "corrected": "their", "reason": "Possessive pronoun needed, not locative there"}, {"original": "grocerys", "corrected": "groceries", "reason": "Incorrect plural spelling"}]}',
        },
    ],
)
def proofread(text: str):
    pass


# ---------------------------------------------------------------------------
# Plugin class
# ---------------------------------------------------------------------------

class WritingInstructionPack(TransformerPlugin):
    """AI-powered writing tools: translation, tone rewriting, summarization, email drafting, proofreading."""

    def __init__(self):
        super().__init__("instructions_writing")

    @property
    def transformers(self):
        return {}

    @property
    def instructions(self):
        return {
            "translate_text": translate_text.__instruction__,
            "rewrite_tone": rewrite_tone.__instruction__,
            "summarize_document": summarize_document.__instruction__,
            "generate_email": generate_email.__instruction__,
            "proofread": proofread.__instruction__,
        }

    @property
    def manifest(self):
        return PluginManifest(
            name="instructions_writing",
            display_name="Writing Instructions",
            description="AI-powered writing tools: translation, tone adjustment, summarization, email drafting, and proofreading.",
            icon="pen-tool",
            group="Instructions",
            requires=PluginRequirements(network=True),
        )
