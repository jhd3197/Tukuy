"""Product instruction pack -- AI-powered product management tools.

Provides instructions for PRD outlines, user story writing, feature
prioritization, release notes, and bug report structuring.
"""

from ...instruction import instruction
from ...manifest import PluginManifest, PluginRequirements
from ..base import TransformerPlugin


# ---------------------------------------------------------------------------
# Instructions
# ---------------------------------------------------------------------------

@instruction(
    name="prd_outline",
    description="Generate a product requirements document outline for a feature or product",
    prompt=(
        "Create a PRD outline for the following feature or product. Include all "
        "essential sections a cross-functional team needs to build and ship.\n\n"
        "Feature/Product: {feature}\n"
        "Problem Statement: {problem}\n"
        "Target Users: {users}\n"
        "Success Metrics: {metrics}\n"
        "Constraints: {constraints}"
    ),
    system_prompt=(
        "You are a senior product manager at a top tech company. Write PRDs that are "
        "clear enough for engineering to scope and specific enough to prevent scope creep. "
        "Always respond with valid JSON."
    ),
    output_format="json",
    temperature=0.5,
    max_tokens=1000,
    category="product",
    tags=["prd", "requirements", "product", "planning"],
    icon="clipboard",
    few_shot_examples=[
        {
            "input": "Feature: In-app notification center. Problem: Users miss important updates and rely on email. Users: All active users, power users especially. Metrics: reduce email dependency 50%, increase feature adoption 20%. Constraints: must work on mobile and web, no push notifications for v1.",
            "output": '{"title": "PRD: In-App Notification Center", "sections": [{"section": "Problem Statement", "content": "Users currently rely on email for all platform notifications. 60% of action-required emails go unread, leading to missed deadlines and low feature adoption."}, {"section": "Goals & Success Metrics", "content": "Primary: Reduce reliance on email notifications by 50%. Secondary: Increase feature adoption by 20% through in-context notifications. Metric: notification open rate > 40%."}, {"section": "User Stories", "content": "As a user, I want to see all my notifications in one place so I do not miss important updates. As a power user, I want to filter and manage notifications so I can focus on what matters."}, {"section": "Scope & Requirements", "subsections": [{"name": "In Scope (v1)", "items": ["Notification bell icon with unread count", "Notification feed with read/unread state", "Filter by notification type", "Mark all as read", "Web and mobile responsive"]}, {"name": "Out of Scope (v1)", "items": ["Push notifications", "Notification preferences/settings", "Notification grouping/threading"]}]}, {"section": "Technical Considerations", "content": "Requires WebSocket or polling for real-time updates. Notification storage and retrieval API. Consider pagination for heavy users."}, {"section": "Design Requirements", "content": "Notification panel slides in from right. Each notification shows: icon, title, description, timestamp, read state. Mobile: full-screen overlay."}, {"section": "Rollout Plan", "content": "Phase 1: Internal dogfood (1 week). Phase 2: 10% beta rollout. Phase 3: GA with monitoring."}, {"section": "Open Questions", "items": ["Should notifications have expiration dates?", "Do we need notification sounds on web?"]}]}',
        },
    ],
)
def prd_outline(feature: str, problem: str, users: str = "", metrics: str = "", constraints: str = ""):
    pass


@instruction(
    name="write_user_stories",
    description="Write user stories with acceptance criteria in standard format",
    prompt=(
        "Write user stories for the following feature. Use the standard format "
        "and include clear acceptance criteria for each story.\n\n"
        "Feature: {feature}\n"
        "User Personas: {personas}\n"
        "Context: {context}\n"
        "Number of Stories: {num_stories}"
    ),
    system_prompt=(
        "You are a product owner who writes user stories that development teams love. "
        "Each story should be independent, testable, and appropriately sized. "
        "Always respond with valid JSON."
    ),
    output_format="json",
    temperature=0.5,
    max_tokens=800,
    category="product",
    tags=["user-stories", "agile", "product", "requirements"],
    icon="users",
    few_shot_examples=[
        {
            "input": "Feature: Shopping cart. Personas: casual shopper, power buyer. Context: e-commerce platform, mobile-first. Stories: 3.",
            "output": '{"stories": [{"id": "CART-001", "story": "As a casual shopper, I want to add items to my cart so I can purchase them later.", "acceptance_criteria": ["Clicking Add to Cart adds the item with default quantity of 1", "Cart icon shows updated item count", "Adding a duplicate item increments quantity instead of creating a new entry", "Works on both mobile and desktop views"], "priority": "must-have", "points": 3}, {"id": "CART-002", "story": "As a power buyer, I want to adjust quantities in my cart so I can order the right amount without re-browsing.", "acceptance_criteria": ["Quantity selector allows values from 1 to max stock", "Changing quantity updates line total and cart total in real-time", "Setting quantity to 0 removes the item with a confirmation prompt", "Changes persist across sessions for logged-in users"], "priority": "must-have", "points": 2}, {"id": "CART-003", "story": "As a casual shopper, I want to see my cart total including estimated shipping so I know what I will pay before checkout.", "acceptance_criteria": ["Cart displays subtotal, estimated shipping, and estimated tax", "Shipping estimate uses default location or logged-in address", "Total updates in real-time when cart contents change"], "priority": "should-have", "points": 2}]}',
        },
    ],
)
def write_user_stories(feature: str, personas: str = "", context: str = "", num_stories: str = "5"):
    pass


@instruction(
    name="prioritize_features",
    description="Prioritize a list of features using a structured framework like RICE or ICE",
    prompt=(
        "Prioritize the following features using the specified framework. "
        "Score each feature and provide a ranked recommendation.\n\n"
        "Features: {features}\n"
        "Framework: {framework}\n"
        "Team Context: {context}\n"
        "Time Horizon: {time_horizon}"
    ),
    system_prompt=(
        "You are a product strategist who helps teams make tough prioritization decisions. "
        "Be objective, data-driven, and transparent about assumptions. "
        "Always respond with valid JSON."
    ),
    output_format="json",
    temperature=0.4,
    max_tokens=800,
    category="product",
    tags=["prioritization", "roadmap", "product", "strategy"],
    icon="list",
    few_shot_examples=[
        {
            "input": "Features: (1) Dark mode, (2) CSV export, (3) SSO/SAML login, (4) Mobile app. Framework: RICE. Context: B2B SaaS, 200 customers, 5-person eng team. Time horizon: next quarter.",
            "output": '{"framework": "RICE (Reach, Impact, Confidence, Effort)", "scores": [{"feature": "SSO/SAML Login", "reach": 80, "impact": 3, "confidence": 90, "effort": 3, "rice_score": 72, "reasoning": "Required by enterprise prospects. High reach among target segment, high impact on deal closure, moderate effort."}, {"feature": "CSV Export", "reach": 150, "impact": 2, "confidence": 95, "effort": 1, "rice_score": 285, "reasoning": "Most-requested feature. High reach, moderate impact per user, very low effort — clear quick win."}, {"feature": "Dark Mode", "reach": 100, "impact": 1, "confidence": 70, "effort": 2, "rice_score": 35, "reasoning": "Nice-to-have. Broad reach but low individual impact. Lower confidence it drives retention."}, {"feature": "Mobile App", "reach": 60, "impact": 3, "confidence": 50, "effort": 8, "rice_score": 11, "reasoning": "High impact for mobile users but low confidence in adoption, and very high effort for a 5-person team."}], "ranked_recommendation": ["CSV Export (quick win, ship first)", "SSO/SAML Login (strategic, ship second)", "Dark Mode (low effort, backlog)", "Mobile App (defer to next half)"], "assumptions": "Reach estimated from feature request data and customer segments. Effort in person-weeks."}',
        },
    ],
)
def prioritize_features(features: str, framework: str = "RICE", context: str = "", time_horizon: str = "next quarter"):
    pass


@instruction(
    name="write_release_notes",
    description="Write user-facing release notes for a product update",
    prompt=(
        "Write user-facing release notes for the following product update. "
        "Make them clear, scannable, and focused on user value.\n\n"
        "Version: {version}\n"
        "Changes: {changes}\n"
        "Product: {product}\n"
        "Audience: {audience}\n"
        "Tone: {tone}"
    ),
    system_prompt=(
        "You are a product communications expert. Write release notes that users "
        "actually want to read — highlight value, not just features. "
        "Always respond with valid JSON."
    ),
    output_format="json",
    temperature=0.5,
    max_tokens=600,
    category="product",
    tags=["release-notes", "changelog", "product", "communication"],
    icon="tag",
    few_shot_examples=[
        {
            "input": "Version: 2.5.0. Changes: added dark mode, fixed CSV export bug for large files, improved dashboard load time by 40%, deprecated legacy API v1. Product: analytics dashboard. Audience: technical users. Tone: concise and professional.",
            "output": '{"version": "2.5.0", "release_date": "[Date]", "headline": "Faster dashboards, dark mode, and reliability fixes", "sections": [{"category": "New", "items": [{"title": "Dark Mode", "description": "Switch between light and dark themes from Settings > Appearance. Your preference syncs across devices."}]}, {"category": "Improved", "items": [{"title": "Dashboard Performance", "description": "Dashboards now load up to 40% faster, especially for workspaces with 50+ widgets."}]}, {"category": "Fixed", "items": [{"title": "CSV Export for Large Datasets", "description": "Exports over 100k rows no longer time out. Files are now generated in the background and delivered via notification."}]}, {"category": "Deprecated", "items": [{"title": "Legacy API v1", "description": "API v1 is now deprecated and will be removed on [Date]. Please migrate to API v2. See our migration guide for details."}]}]}',
        },
    ],
)
def write_release_notes(version: str, changes: str, product: str = "", audience: str = "end users", tone: str = "professional"):
    pass


@instruction(
    name="structure_bug_report",
    description="Structure a bug report from unstructured information into a clear, actionable format",
    prompt=(
        "Take the following unstructured bug information and organize it into a "
        "clear, actionable bug report.\n\n"
        "Raw Information: {info}\n"
        "Product: {product}\n"
        "Reporter: {reporter}\n"
        "Environment: {environment}"
    ),
    system_prompt=(
        "You are a QA engineer who writes bug reports that developers can act on immediately. "
        "Include clear reproduction steps and distinguish facts from assumptions. "
        "Always respond with valid JSON."
    ),
    output_format="json",
    temperature=0.3,
    max_tokens=600,
    category="product",
    tags=["bug-report", "qa", "product", "development"],
    icon="alert-circle",
    few_shot_examples=[
        {
            "input": "Info: 'Hey the dashboard is broken again. When I click on the sales chart it just spins forever. Happened after I changed the date to last year. My coworker says it works for her though. I am on Chrome.' Product: analytics dashboard. Reporter: Sales Manager. Environment: production.",
            "output": '{"title": "Dashboard sales chart infinite loading when date range set to previous year", "severity": "medium", "priority": "high", "environment": {"app": "Analytics Dashboard (production)", "browser": "Chrome (version TBD)", "os": "TBD"}, "steps_to_reproduce": ["1. Log in to the analytics dashboard", "2. Navigate to the sales chart widget", "3. Change the date range to the previous year (e.g., 2024)", "4. Click on the sales chart", "5. Observe: chart shows infinite loading spinner"], "expected_behavior": "Sales chart should load and display data for the selected year.", "actual_behavior": "Chart shows an infinite loading spinner and never resolves.", "additional_context": ["Issue may be user-specific — another user reports the chart works for them", "Could be related to permissions, data volume, or account-specific date range"], "investigation_notes": ["Confirm Chrome version and check if reproducible on other browsers", "Compare data volume between reporter and coworker accounts", "Check network tab for failed API requests when spinner appears"]}',
        },
    ],
)
def structure_bug_report(info: str, product: str = "", reporter: str = "", environment: str = "production"):
    pass


# ---------------------------------------------------------------------------
# Plugin class
# ---------------------------------------------------------------------------

class ProductInstructionPack(TransformerPlugin):
    """AI-powered product tools: PRDs, user stories, feature prioritization, release notes, bug reports."""

    def __init__(self):
        super().__init__("instructions_product")

    @property
    def transformers(self):
        return {}

    @property
    def instructions(self):
        return {
            "prd_outline": prd_outline.__instruction__,
            "write_user_stories": write_user_stories.__instruction__,
            "prioritize_features": prioritize_features.__instruction__,
            "write_release_notes": write_release_notes.__instruction__,
            "structure_bug_report": structure_bug_report.__instruction__,
        }

    @property
    def manifest(self):
        return PluginManifest(
            name="instructions_product",
            display_name="Product Instructions",
            description="AI-powered product tools: PRD outlines, user stories, feature prioritization, release notes, and bug report structuring.",
            icon="package",
            group="Instructions",
            requires=PluginRequirements(network=True),
        )
