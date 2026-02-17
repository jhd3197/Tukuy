"""Finance instruction pack -- AI-powered financial analysis tools.

Provides instructions for invoice analysis, budget planning, financial
summaries, expense categorization, and ROI calculations.

Note: These tools provide informational assistance only and do not
constitute financial advice. Always consult a qualified professional.
"""

from ...instruction import instruction
from ...manifest import PluginManifest, PluginRequirements
from ..base import TransformerPlugin


# ---------------------------------------------------------------------------
# Instructions
# ---------------------------------------------------------------------------

@instruction(
    name="analyze_invoice",
    description="Extract and validate key information from an invoice",
    prompt=(
        "Extract key information from the following invoice and validate it for "
        "common issues like math errors or missing fields.\n\n"
        "Invoice Data: {invoice}\n"
        "Expected Vendor: {vendor}\n"
        "Purchase Order: {po_number}"
    ),
    system_prompt=(
        "You are an accounts payable specialist. Extract invoice data precisely "
        "and flag any discrepancies or missing information. "
        "Always respond with valid JSON."
    ),
    output_format="json",
    temperature=0.2,
    max_tokens=600,
    category="finance",
    tags=["invoice", "accounts-payable", "finance", "validation"],
    icon="file-text",
    few_shot_examples=[
        {
            "input": "Invoice: From CloudHost Inc, Invoice #CH-2024-0892, dated Dec 15 2024. Line items: Server hosting (12 months) $4,800, SSL certificate $120, Premium support $600. Subtotal $5,520, Tax (8%) $441.60, Total $5,961.60. Payment terms: Net 30. Vendor: CloudHost Inc. PO: PO-2024-445.",
            "output": '{"invoice_number": "CH-2024-0892", "vendor": "CloudHost Inc", "date": "2024-12-15", "po_match": true, "line_items": [{"description": "Server hosting (12 months)", "amount": 4800.00}, {"description": "SSL certificate", "amount": 120.00}, {"description": "Premium support", "amount": 600.00}], "subtotal": 5520.00, "tax_rate": "8%", "tax_amount": 441.60, "total": 5961.60, "payment_terms": "Net 30", "due_date": "2025-01-14", "validation": {"math_correct": true, "all_fields_present": true, "issues": []}}',
        },
    ],
)
def analyze_invoice(invoice: str, vendor: str = "", po_number: str = ""):
    pass


@instruction(
    name="budget_plan",
    description="Create a budget plan or breakdown for a project, department, or period",
    prompt=(
        "Create a budget plan for the following project or department. "
        "Break down costs by category and include contingency recommendations.\n\n"
        "Purpose: {purpose}\n"
        "Total Budget: {budget}\n"
        "Time Period: {period}\n"
        "Known Costs: {known_costs}\n"
        "Priorities: {priorities}"
    ),
    system_prompt=(
        "You are a financial planner who creates clear, realistic budgets. "
        "Account for hidden costs and always include contingency. "
        "Always respond with valid JSON."
    ),
    output_format="json",
    temperature=0.4,
    max_tokens=800,
    category="finance",
    tags=["budget", "planning", "finance", "allocation"],
    icon="dollar-sign",
    few_shot_examples=[
        {
            "input": "Purpose: Launch marketing campaign for new product. Budget: $50,000. Period: Q1 2025. Known costs: influencer fees ($15k committed). Priorities: digital ads, content creation, events.",
            "output": '{"title": "Q1 2025 Product Launch Marketing Budget", "total_budget": 50000, "allocations": [{"category": "Digital Advertising", "amount": 18000, "percentage": "36%", "breakdown": ["Google Ads: $8,000", "Social media ads: $7,000", "Retargeting: $3,000"], "notes": "Front-load spend in month 1 for launch momentum"}, {"category": "Influencer Marketing", "amount": 15000, "percentage": "30%", "breakdown": ["Committed influencer fees: $15,000"], "notes": "Already committed — ensure deliverables and timelines are contracted"}, {"category": "Content Creation", "amount": 8000, "percentage": "16%", "breakdown": ["Video production: $4,000", "Photography: $2,000", "Copywriting and design: $2,000"], "notes": "Reuse content across channels to maximize value"}, {"category": "Events", "amount": 4000, "percentage": "8%", "breakdown": ["Launch event venue and catering: $3,000", "Promotional materials: $1,000"], "notes": "Consider co-hosting with a partner to share costs"}, {"category": "Contingency", "amount": 5000, "percentage": "10%", "breakdown": ["Unplanned opportunities or overruns"], "notes": "Industry standard is 10-15%. Do not allocate until needed."}], "monthly_breakdown": {"January": "$22,000 (heavy launch spend)", "February": "$16,000 (sustain momentum)", "March": "$12,000 (optimize based on results)"}, "risks": ["Influencer deliverables delayed could waste ad spend timing", "Ad costs may increase during Q1 competitive season"]}',
        },
    ],
)
def budget_plan(purpose: str, budget: str, period: str = "", known_costs: str = "", priorities: str = ""):
    pass


@instruction(
    name="financial_summary",
    description="Generate a financial summary from raw financial data or statements",
    prompt=(
        "Generate a clear financial summary from the following data. Highlight "
        "key metrics, trends, and areas of concern.\n\n"
        "Financial Data: {data}\n"
        "Report Type: {report_type}\n"
        "Comparison Period: {comparison}\n"
        "Audience: {audience}"
    ),
    system_prompt=(
        "You are a financial analyst who makes complex numbers clear for any audience. "
        "Lead with the story the numbers tell, not just the numbers themselves. "
        "Always respond with valid JSON."
    ),
    output_format="json",
    temperature=0.3,
    max_tokens=800,
    category="finance",
    tags=["financial-summary", "reporting", "finance", "analysis"],
    icon="trending-up",
    few_shot_examples=[
        {
            "input": "Data: Q4 2024 — Revenue $2.1M (Q3: $1.8M), COGS $840k, Operating expenses $950k, Net income $310k. Headcount: 45 (Q3: 40). Cash on hand: $1.2M. Report type: quarterly summary. Comparison: Q3 2024. Audience: CEO.",
            "output": '{"title": "Q4 2024 Financial Summary", "headline": "Revenue up 17% to $2.1M with improving margins, but opex growth warrants monitoring.", "key_metrics": [{"metric": "Revenue", "value": "$2.1M", "change": "+17% vs Q3", "status": "positive"}, {"metric": "Gross Margin", "value": "60%", "change": "Stable (Q3: 53%)", "status": "positive"}, {"metric": "Net Income", "value": "$310K", "change": "+$60K vs Q3", "status": "positive"}, {"metric": "Revenue per Employee", "value": "$46.7K", "change": "-4% vs Q3 ($45K)", "status": "watch"}, {"metric": "Cash Position", "value": "$1.2M", "change": "Sufficient for ~4 months opex", "status": "neutral"}], "trends": ["Revenue growing faster than headcount — efficiency improving", "Gross margin improved 7 points suggesting better pricing or lower COGS", "Operating expenses grew 12% while revenue grew 17% — positive leverage"], "concerns": ["Revenue per employee declined slightly with 5 new hires — expected ramp lag", "Cash runway of ~4 months is tight if growth investments increase"], "outlook": "Strong Q4 sets up well for 2025, but maintain discipline on opex as headcount grows."}',
        },
    ],
)
def financial_summary(data: str, report_type: str = "general", comparison: str = "", audience: str = "management"):
    pass


@instruction(
    name="categorize_expenses",
    description="Categorize a list of expenses into standard accounting categories",
    prompt=(
        "Categorize the following expenses into standard accounting categories. "
        "Flag any items that need review or seem unusual.\n\n"
        "Expenses: {expenses}\n"
        "Business Type: {business_type}\n"
        "Categorization Standard: {standard}"
    ),
    system_prompt=(
        "You are a bookkeeper who categorizes expenses accurately. Use standard "
        "accounting categories and flag anything unusual. "
        "Always respond with valid JSON."
    ),
    output_format="json",
    temperature=0.2,
    max_tokens=800,
    category="finance",
    tags=["expenses", "categorization", "finance", "bookkeeping"],
    icon="tag",
    few_shot_examples=[
        {
            "input": "Expenses: $450 team lunch, $1200 Adobe Creative Cloud annual, $89 Uber to client meeting, $15000 new MacBook Pros (3), $250 conference ticket, $45 office coffee supplies. Business type: tech startup. Standard: standard categories.",
            "output": '{"categorized": [{"item": "Team lunch ($450)", "category": "Meals & Entertainment", "subcategory": "Team meals", "tax_deductible": "50% deductible (meals)", "notes": null}, {"item": "Adobe Creative Cloud ($1,200)", "category": "Software & Subscriptions", "subcategory": "Design tools", "tax_deductible": "100% deductible", "notes": null}, {"item": "Uber to client meeting ($89)", "category": "Travel & Transportation", "subcategory": "Local transportation", "tax_deductible": "100% deductible", "notes": "Keep receipt and note client/purpose"}, {"item": "MacBook Pros x3 ($15,000)", "category": "Equipment & Hardware", "subcategory": "Computer equipment", "tax_deductible": "Depreciable asset or Section 179", "notes": "Over $2,500 per unit — may require capitalization rather than expensing"}, {"item": "Conference ticket ($250)", "category": "Professional Development", "subcategory": "Conferences", "tax_deductible": "100% deductible", "notes": null}, {"item": "Office coffee supplies ($45)", "category": "Office Supplies", "subcategory": "Kitchen/break room", "tax_deductible": "100% deductible", "notes": null}], "flags": [{"item": "MacBook Pros ($15,000)", "reason": "High-value purchase — verify capitalization policy. May need to be depreciated over 3-5 years rather than expensed immediately."}], "summary": {"total": 17034, "by_category": {"Meals & Entertainment": 450, "Software & Subscriptions": 1200, "Travel & Transportation": 89, "Equipment & Hardware": 15000, "Professional Development": 250, "Office Supplies": 45}}}',
        },
    ],
)
def categorize_expenses(expenses: str, business_type: str = "general", standard: str = "standard categories"):
    pass


@instruction(
    name="calculate_roi",
    description="Calculate and present ROI analysis for a business investment or initiative",
    prompt=(
        "Calculate the ROI for the following investment or initiative. Include "
        "costs, expected returns, payback period, and sensitivity analysis.\n\n"
        "Investment: {investment}\n"
        "Costs: {costs}\n"
        "Expected Benefits: {benefits}\n"
        "Time Horizon: {time_horizon}\n"
        "Risk Factors: {risks}"
    ),
    system_prompt=(
        "You are a financial analyst who presents ROI analyses clearly for decision-makers. "
        "Be transparent about assumptions and include sensitivity scenarios. "
        "Always respond with valid JSON."
    ),
    output_format="json",
    temperature=0.3,
    max_tokens=800,
    category="finance",
    tags=["roi", "investment", "finance", "analysis"],
    icon="percent",
    few_shot_examples=[
        {
            "input": "Investment: Implementing a CRM system. Costs: $30k software license/year, $15k implementation, $5k training. Benefits: 20% increase in sales conversion (currently $500k/year in pipeline), 10 hours/week saved on manual data entry ($50/hr). Time horizon: 2 years. Risks: adoption may be slow, integration with existing tools.",
            "output": '{"investment_summary": "CRM Implementation", "total_cost_year_1": 50000, "total_cost_year_2": 30000, "total_cost_2_year": 80000, "expected_returns": {"increased_revenue": {"calculation": "20% improvement on $500k pipeline = $100k/year additional revenue", "annual_value": 100000}, "time_savings": {"calculation": "10 hrs/week * 52 weeks * $50/hr = $26,000/year", "annual_value": 26000}, "total_annual_benefit": 126000}, "roi_analysis": {"year_1_roi": "152% (($126k - $50k) / $50k)", "year_2_roi": "320% (($126k - $30k) / $30k)", "cumulative_2_year_roi": "215% (($252k - $80k) / $80k)", "payback_period": "4.8 months"}, "sensitivity": {"conservative": {"assumption": "Only 10% conversion improvement, 50% time savings adoption", "annual_benefit": 63000, "year_1_roi": "26%", "payback": "9.5 months"}, "optimistic": {"assumption": "25% conversion improvement, full time savings realized", "annual_benefit": 151000, "year_1_roi": "202%", "payback": "4 months"}}, "recommendation": "Strong positive ROI even in the conservative scenario. Recommend proceeding with a phased rollout to mitigate adoption risk.", "assumptions": ["Conversion improvement based on industry benchmarks for CRM adoption", "Time savings assume current manual processes are fully replaced", "Does not account for opportunity cost of implementation time"]}',
        },
    ],
)
def calculate_roi(investment: str, costs: str, benefits: str, time_horizon: str = "1 year", risks: str = ""):
    pass


# ---------------------------------------------------------------------------
# Plugin class
# ---------------------------------------------------------------------------

class FinanceInstructionPack(TransformerPlugin):
    """AI-powered finance tools: invoice analysis, budget planning, financial summaries, expense categorization, ROI calculations."""

    def __init__(self):
        super().__init__("instructions_finance")

    @property
    def transformers(self):
        return {}

    @property
    def instructions(self):
        return {
            "analyze_invoice": analyze_invoice.__instruction__,
            "budget_plan": budget_plan.__instruction__,
            "financial_summary": financial_summary.__instruction__,
            "categorize_expenses": categorize_expenses.__instruction__,
            "calculate_roi": calculate_roi.__instruction__,
        }

    @property
    def manifest(self):
        return PluginManifest(
            name="instructions_finance",
            display_name="Finance Instructions",
            description="AI-powered finance tools: invoice analysis, budget planning, financial summaries, expense categorization, and ROI calculations.",
            icon="dollar-sign",
            group="Instructions",
            requires=PluginRequirements(network=True),
        )
