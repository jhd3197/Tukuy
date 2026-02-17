"""Customer support instruction pack -- AI-powered support tools.

Provides instructions for response drafting, FAQ generation, escalation
assessment, satisfaction analysis, and knowledge base article creation.
"""

from ...instruction import instruction
from ...manifest import PluginManifest, PluginRequirements
from ..base import TransformerPlugin


# ---------------------------------------------------------------------------
# Instructions
# ---------------------------------------------------------------------------

@instruction(
    name="draft_support_response",
    description="Draft a professional customer support response to a ticket or inquiry",
    prompt=(
        "Draft a professional support response to the following customer inquiry. "
        "Be empathetic, clear, and solution-oriented.\n\n"
        "Customer Message: {message}\n"
        "Product/Service: {product}\n"
        "Customer Tier: {tier}\n"
        "Known Context: {context}\n"
        "Tone: {tone}"
    ),
    system_prompt=(
        "You are a senior customer support agent known for high satisfaction scores. "
        "Write responses that acknowledge the issue, provide clear solutions, and "
        "leave the customer feeling valued. Always respond with valid JSON."
    ),
    output_format="json",
    temperature=0.5,
    max_tokens=600,
    category="customer_support",
    tags=["support", "response", "customer-service", "tickets"],
    icon="message-circle",
    few_shot_examples=[
        {
            "input": "Message: 'I was charged twice for my subscription this month. This is the second time this has happened and I am really frustrated.' Product: SaaS project management tool. Tier: premium. Context: billing issue, previous double charge 3 months ago. Tone: empathetic and professional.",
            "output": '{"response": "Hi [Customer Name],\\n\\nI completely understand your frustration, and I sincerely apologize that this has happened again. A double charge is never acceptable, especially when it is a recurring issue.\\n\\nI have already initiated a refund for the duplicate charge of [amount]. You should see it reflected in your account within 3-5 business days.\\n\\nI have also escalated this to our billing engineering team with a flag on your account to investigate why this recurred. I want to make sure this is permanently resolved, not just patched.\\n\\nAs a premium customer, your experience matters deeply to us. I will personally follow up within 48 hours with an update from the engineering team.\\n\\nThank you for your patience, and please do not hesitate to reach out if you need anything else.\\n\\nBest regards,\\n[Agent Name]", "sentiment_detected": "frustrated, repeat issue", "actions_taken": ["Initiated refund", "Escalated to billing engineering", "Flagged account for investigation"], "follow_up_needed": true, "follow_up_timeline": "48 hours"}',
        },
    ],
)
def draft_support_response(message: str, product: str = "", tier: str = "standard", context: str = "", tone: str = "empathetic and professional"):
    pass


@instruction(
    name="generate_faq",
    description="Generate FAQ entries from common support topics or product documentation",
    prompt=(
        "Generate FAQ entries for the given topic or product. Each entry should "
        "have a clear question and a concise, helpful answer.\n\n"
        "Product/Topic: {topic}\n"
        "Target Audience: {audience}\n"
        "Common Issues: {issues}\n"
        "Number of FAQs: {num_faqs}"
    ),
    system_prompt=(
        "You are a technical writer who creates clear, helpful FAQ content. "
        "Anticipate what customers actually ask, not what you wish they would ask. "
        "Always respond with valid JSON."
    ),
    output_format="json",
    temperature=0.5,
    max_tokens=800,
    category="customer_support",
    tags=["faq", "documentation", "customer-service", "knowledge-base"],
    icon="help-circle",
    few_shot_examples=[
        {
            "input": "Topic: password reset for a mobile banking app. Audience: non-technical users. Issues: forgot password, locked out, 2FA problems. FAQs: 3.",
            "output": '{"faqs": [{"question": "How do I reset my password?", "answer": "Tap \"Forgot Password\" on the login screen, enter your registered email, and follow the link in the email we send you. The link expires in 30 minutes. If you do not receive the email, check your spam folder.", "category": "account_access"}, {"question": "My account is locked after too many failed attempts. What do I do?", "answer": "For your security, accounts lock after 5 failed login attempts. Wait 30 minutes and try again, or tap \"Forgot Password\" to reset. If you are still locked out, contact support at [phone number] with your account email ready.", "category": "account_access"}, {"question": "I lost access to my two-factor authentication app. How do I log in?", "answer": "If you saved your backup codes during setup, use one to log in. If not, contact our support team at [phone number] — we will verify your identity and help you regain access. This process takes 1-2 business days for security reasons.", "category": "security"}]}',
        },
    ],
)
def generate_faq(topic: str, audience: str = "general users", issues: str = "", num_faqs: str = "5"):
    pass


@instruction(
    name="assess_escalation",
    description="Assess whether a support ticket needs escalation and determine the appropriate level",
    prompt=(
        "Assess the following support ticket and determine if it needs escalation. "
        "Consider severity, customer impact, and whether frontline can resolve it.\n\n"
        "Ticket: {ticket}\n"
        "Customer Tier: {tier}\n"
        "Issue History: {history}\n"
        "Current Agent Level: {agent_level}"
    ),
    system_prompt=(
        "You are a support operations manager. Assess escalation needs objectively "
        "based on impact, urgency, and resolution capability. "
        "Always respond with valid JSON."
    ),
    output_format="json",
    temperature=0.3,
    max_tokens=600,
    category="customer_support",
    tags=["escalation", "triage", "customer-service", "support"],
    icon="arrow-up-circle",
    few_shot_examples=[
        {
            "input": "Ticket: 'Our entire team of 50 users cannot access the platform. We have a client presentation in 2 hours.' Tier: enterprise. History: no previous issues. Agent level: L1.",
            "output": '{"escalate": true, "urgency": "critical", "escalation_level": "L3 + Engineering On-Call", "reasoning": ["Complete outage affecting 50 users = high impact", "Time-sensitive (2-hour deadline) = high urgency", "Enterprise tier = SLA obligations", "Platform-wide access failure requires engineering investigation"], "recommended_actions": ["Immediately escalate to L3 and page engineering on-call", "Communicate estimated timeline to customer within 15 minutes", "Check system status page for known incidents", "Offer workaround if possible (mobile app, alternative access)"], "sla_note": "Enterprise SLA requires acknowledgment within 15 minutes for critical issues."}',
        },
    ],
)
def assess_escalation(ticket: str, tier: str = "standard", history: str = "", agent_level: str = "L1"):
    pass


@instruction(
    name="analyze_satisfaction",
    description="Analyze customer feedback or survey responses and extract satisfaction insights",
    prompt=(
        "Analyze the following customer feedback and extract satisfaction insights. "
        "Identify themes, sentiment patterns, and actionable improvements.\n\n"
        "Feedback Data: {feedback}\n"
        "Source: {source}\n"
        "Product/Service: {product}\n"
        "Time Period: {period}"
    ),
    system_prompt=(
        "You are a customer experience analyst. Extract actionable insights from "
        "feedback data, not just sentiment scores. Focus on what drives satisfaction. "
        "Always respond with valid JSON."
    ),
    output_format="json",
    temperature=0.4,
    max_tokens=800,
    category="customer_support",
    tags=["satisfaction", "feedback", "customer-service", "analytics"],
    icon="smile",
    few_shot_examples=[
        {
            "input": "Feedback: 5 reviews — (1) 'Love the product but support is slow' (2) 'Great features, terrible onboarding' (3) 'Best tool we have used, very intuitive' (4) 'Support team is amazing but the product crashes too often' (5) 'Good value but took weeks to get set up'. Source: G2 reviews. Product: project management SaaS. Period: Q4 2024.",
            "output": '{"overall_sentiment": "mixed-positive", "average_implied_score": 3.6, "themes": [{"theme": "Product Quality", "sentiment": "positive", "mentions": 4, "evidence": "Users praise features and intuitiveness but report stability issues"}, {"theme": "Onboarding Experience", "sentiment": "negative", "mentions": 2, "evidence": "Multiple users cite slow or poor onboarding process"}, {"theme": "Support Responsiveness", "sentiment": "mixed", "mentions": 2, "evidence": "One user praises support, another says it is slow"}], "top_drivers_of_satisfaction": ["Feature set and product design", "Value for money"], "top_drivers_of_dissatisfaction": ["Onboarding friction", "Product stability/crashes"], "recommendations": [{"priority": "high", "action": "Invest in guided onboarding flow and reduce time-to-value", "expected_impact": "Address the most common negative theme across reviews"}, {"priority": "high", "action": "Fix stability issues causing crashes", "expected_impact": "Prevent positive product sentiment from being undermined by reliability"}]}',
        },
    ],
)
def analyze_satisfaction(feedback: str, source: str = "", product: str = "", period: str = ""):
    pass


@instruction(
    name="write_kb_article",
    description="Write a knowledge base or help center article for a specific topic",
    prompt=(
        "Write a knowledge base article that helps users solve a specific problem "
        "or understand a feature. Include steps, tips, and troubleshooting.\n\n"
        "Topic: {topic}\n"
        "Product: {product}\n"
        "Audience: {audience}\n"
        "Related Issues: {related_issues}"
    ),
    system_prompt=(
        "You are a technical writer who creates self-service help content. Write articles "
        "that reduce support tickets by being clear, scannable, and complete. "
        "Always respond with valid JSON."
    ),
    output_format="json",
    temperature=0.4,
    max_tokens=800,
    category="customer_support",
    tags=["knowledge-base", "documentation", "customer-service", "self-service"],
    icon="book-open",
    few_shot_examples=[
        {
            "input": "Topic: How to export data as CSV. Product: analytics dashboard. Audience: non-technical business users. Related issues: export fails for large datasets, special characters in filenames.",
            "output": '{"title": "How to Export Your Data as CSV", "summary": "Learn how to download your dashboard data as a CSV file for use in Excel, Google Sheets, or other tools.", "steps": [{"step": 1, "instruction": "Navigate to the dashboard or report you want to export.", "tip": null}, {"step": 2, "instruction": "Click the \"Export\" button in the top-right corner of the data table.", "tip": "If you do not see the Export button, check that you have Viewer or Admin permissions."}, {"step": 3, "instruction": "Select \"CSV\" from the format dropdown menu.", "tip": null}, {"step": 4, "instruction": "Choose your date range and any filters, then click \"Download\".", "tip": "Applied filters carry over to the export, so verify your filters first."}], "troubleshooting": [{"issue": "Export fails or times out", "solution": "For datasets over 100,000 rows, narrow your date range or add filters to reduce the export size. Try exporting in smaller batches."}, {"issue": "Special characters appear garbled in Excel", "solution": "When opening the CSV in Excel, use File > Import and select UTF-8 encoding instead of double-clicking the file."}], "related_articles": ["How to schedule automatic exports", "Understanding export permissions"]}',
        },
    ],
)
def write_kb_article(topic: str, product: str = "", audience: str = "end users", related_issues: str = ""):
    pass


# ---------------------------------------------------------------------------
# Plugin class
# ---------------------------------------------------------------------------

class CustomerSupportInstructionPack(TransformerPlugin):
    """AI-powered support tools: response drafting, FAQ generation, escalation assessment, satisfaction analysis, KB articles."""

    def __init__(self):
        super().__init__("instructions_customer_support")

    @property
    def transformers(self):
        return {}

    @property
    def instructions(self):
        return {
            "draft_support_response": draft_support_response.__instruction__,
            "generate_faq": generate_faq.__instruction__,
            "assess_escalation": assess_escalation.__instruction__,
            "analyze_satisfaction": analyze_satisfaction.__instruction__,
            "write_kb_article": write_kb_article.__instruction__,
        }

    @property
    def manifest(self):
        return PluginManifest(
            name="instructions_customer_support",
            display_name="Customer Support Instructions",
            description="AI-powered support tools: response drafting, FAQ generation, escalation assessment, satisfaction analysis, and knowledge base articles.",
            icon="headphones",
            group="Instructions",
            requires=PluginRequirements(network=True),
        )
