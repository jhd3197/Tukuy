"""Data instruction pack -- AI-powered data analysis tools.

Provides instructions for data cleaning suggestions, chart description,
dataset summarization, outlier interpretation, and report generation.
"""

from ...instruction import instruction
from ...manifest import PluginManifest, PluginRequirements
from ..base import TransformerPlugin


# ---------------------------------------------------------------------------
# Instructions
# ---------------------------------------------------------------------------

@instruction(
    name="suggest_data_cleaning",
    description="Analyze a dataset description and suggest data cleaning steps",
    prompt=(
        "Analyze the following dataset description and suggest specific data "
        "cleaning steps. Prioritize by impact on analysis quality.\n\n"
        "Dataset Description: {description}\n"
        "Columns: {columns}\n"
        "Known Issues: {issues}\n"
        "Intended Analysis: {analysis}"
    ),
    system_prompt=(
        "You are a data engineering expert. Suggest practical, prioritized cleaning "
        "steps with specific code snippets where helpful. "
        "Always respond with valid JSON."
    ),
    output_format="json",
    temperature=0.3,
    max_tokens=800,
    category="data",
    tags=["data-cleaning", "data-quality", "data", "analysis"],
    icon="filter",
    few_shot_examples=[
        {
            "input": "Description: E-commerce transactions CSV, 50k rows. Columns: order_id, customer_email, amount, date, country, product_category. Issues: some amounts are negative, dates in mixed formats, 5% missing emails. Analysis: customer segmentation by purchase behavior.",
            "output": '{"cleaning_steps": [{"priority": 1, "issue": "Mixed date formats", "impact": "high", "action": "Standardize all dates to ISO 8601 (YYYY-MM-DD)", "code_hint": "pd.to_datetime(df[\"date\"], infer_datetime_format=True, errors=\"coerce\")"}, {"priority": 2, "issue": "Negative amounts", "impact": "high", "action": "Investigate if negatives represent refunds. If so, flag with a separate column; if errors, convert to absolute value or remove.", "code_hint": "df[\"is_refund\"] = df[\"amount\"] < 0"}, {"priority": 3, "issue": "Missing customer emails (5%)", "impact": "medium", "action": "For segmentation, rows without emails cannot be linked to customers. Either fill from order history or exclude from customer-level analysis.", "code_hint": "df_clean = df.dropna(subset=[\"customer_email\"])"}, {"priority": 4, "issue": "Duplicate order IDs", "impact": "medium", "action": "Check for and remove exact duplicates; investigate near-duplicates.", "code_hint": "df.drop_duplicates(subset=[\"order_id\"], keep=\"first\", inplace=True)"}], "validation_checks": ["Verify all amounts are positive after cleaning (or properly flagged)", "Confirm date range is within expected business period", "Check unique customer count matches expectations"]}',
        },
    ],
)
def suggest_data_cleaning(description: str, columns: str, issues: str = "", analysis: str = ""):
    pass


@instruction(
    name="describe_chart",
    description="Generate a natural-language description and insights from chart data",
    prompt=(
        "Generate a clear description of the following chart or visualization. "
        "Include what it shows, key trends, and actionable insights.\n\n"
        "Chart Type: {chart_type}\n"
        "Data Summary: {data}\n"
        "Context: {context}\n"
        "Audience: {audience}"
    ),
    system_prompt=(
        "You are a data storytelling expert. Describe charts in a way that highlights "
        "the most important patterns and their business implications. "
        "Always respond with valid JSON."
    ),
    output_format="json",
    temperature=0.4,
    max_tokens=600,
    category="data",
    tags=["visualization", "charts", "data", "storytelling"],
    icon="bar-chart",
    few_shot_examples=[
        {
            "input": "Chart type: line chart. Data: Monthly revenue Jan-Jun: $120k, $115k, $135k, $140k, $128k, $155k. Context: B2B SaaS company, launched new pricing tier in March. Audience: board of directors.",
            "output": '{"description": "Monthly revenue for H1 shows an overall upward trend from $120k to $155k, a 29% increase, with a notable dip in May.", "key_trends": ["Revenue grew 29% from January ($120k) to June ($155k)", "March saw a 17% jump coinciding with the new pricing tier launch", "May dipped 9% before recovering strongly in June"], "insights": ["The new pricing tier appears to have positively impacted revenue starting in March", "The May dip warrants investigation — could be seasonal, churn, or one-time event", "June recovery suggests underlying growth momentum is healthy"], "recommendation": "Investigate the May dip to determine if it is a recurring seasonal pattern. If not, the overall trajectory supports continued investment in the new pricing strategy.", "headline": "Revenue up 29% in H1, driven by new pricing tier launch in March"}',
        },
    ],
)
def describe_chart(chart_type: str, data: str, context: str = "", audience: str = "general"):
    pass


@instruction(
    name="summarize_dataset",
    description="Generate a summary overview of a dataset with statistics and observations",
    prompt=(
        "Summarize the following dataset. Provide an overview, key statistics, "
        "data quality observations, and initial hypotheses for analysis.\n\n"
        "Dataset Name: {name}\n"
        "Row Count: {rows}\n"
        "Columns: {columns}\n"
        "Sample Data: {sample}\n"
        "Purpose: {purpose}"
    ),
    system_prompt=(
        "You are a data scientist who provides clear, insightful dataset summaries. "
        "Highlight what is interesting, what needs attention, and what analyses are possible. "
        "Always respond with valid JSON."
    ),
    output_format="json",
    temperature=0.3,
    max_tokens=800,
    category="data",
    tags=["dataset", "summary", "data", "eda"],
    icon="database",
    few_shot_examples=[
        {
            "input": "Name: customer_churn. Rows: 10,000. Columns: customer_id, tenure_months, monthly_charges, total_charges, contract_type (month-to-month/annual/two-year), churn (yes/no). Sample: [id=1, tenure=12, charges=70, total=840, contract=month-to-month, churn=yes]. Purpose: predict customer churn.",
            "output": '{"overview": "Customer churn dataset with 10,000 records capturing tenure, billing, contract type, and churn outcome. Suitable for binary classification modeling.", "key_observations": ["Mix of contract types allows comparison of churn rates by commitment level", "Tenure and charges provide behavioral signals for churn prediction", "Total charges should correlate with tenure * monthly charges — verify consistency"], "suggested_statistics": ["Churn rate (% of yes vs no)", "Average tenure for churned vs retained customers", "Churn rate by contract type", "Distribution of monthly charges"], "data_quality_checks": ["Verify total_charges approximately equals tenure_months * monthly_charges", "Check for missing values in all columns", "Look for outliers in monthly_charges and tenure"], "analysis_recommendations": ["Start with churn rate by contract_type as a quick win", "Build a logistic regression or random forest classifier", "Feature engineer: charges_per_month_of_tenure ratio"]}',
        },
    ],
)
def summarize_dataset(name: str, rows: str, columns: str, sample: str = "", purpose: str = ""):
    pass


@instruction(
    name="interpret_outliers",
    description="Analyze outliers in data and suggest whether to keep, investigate, or remove them",
    prompt=(
        "Analyze the following outliers found in a dataset. For each, determine "
        "whether it is likely a genuine value, data error, or requires investigation.\n\n"
        "Dataset Context: {context}\n"
        "Outliers Found: {outliers}\n"
        "Detection Method: {method}\n"
        "Business Context: {business_context}"
    ),
    system_prompt=(
        "You are a data quality analyst. Assess outliers carefully — not all outliers "
        "are errors, and removing genuine values can bias analysis. "
        "Always respond with valid JSON."
    ),
    output_format="json",
    temperature=0.3,
    max_tokens=800,
    category="data",
    tags=["outliers", "data-quality", "data", "analysis"],
    icon="alert-circle",
    few_shot_examples=[
        {
            "input": "Context: Employee salary dataset, 500 records, US-based tech company. Outliers: $12,000/year (entry-level role), $850,000/year (senior engineer), $0/year (marketing manager). Method: IQR. Business: Salaries should range $50k-$300k for this company.",
            "output": '{"analysis": [{"value": "$12,000/year", "role": "Entry-level", "verdict": "likely_error", "reasoning": "Well below minimum wage for full-time US employment. Probably a data entry error (monthly salary entered as annual?) or a part-time/intern record mislabeled.", "action": "Investigate source record. If monthly value, multiply by 12. If intern, recategorize."}, {"value": "$850,000/year", "verdict": "investigate", "role": "Senior Engineer", "reasoning": "High but possible for a VP/C-level or if total compensation includes equity. Exceeds stated range but could be legitimate.", "action": "Verify role title and whether this includes equity/bonuses. Keep if confirmed, correct if data entry error."}, {"value": "$0/year", "role": "Marketing Manager", "verdict": "likely_error", "reasoning": "A salaried marketing manager at $0 is almost certainly a missing value recorded as zero.", "action": "Replace with NULL/NaN and treat as missing data. Do not impute with mean as it would bias results."}], "general_guidance": "Do not blindly remove outliers. Each requires context-specific assessment. For this dataset, review all values outside $40k-$400k individually."}',
        },
    ],
)
def interpret_outliers(context: str, outliers: str, method: str = "IQR", business_context: str = ""):
    pass


@instruction(
    name="generate_data_report",
    description="Generate a structured data analysis report with sections, findings, and recommendations",
    prompt=(
        "Generate a structured analysis report based on the following data findings. "
        "Include an executive summary, methodology, findings, and recommendations.\n\n"
        "Analysis Topic: {topic}\n"
        "Key Findings: {findings}\n"
        "Data Sources: {sources}\n"
        "Audience: {audience}\n"
        "Time Period: {period}"
    ),
    system_prompt=(
        "You are a data analyst who writes clear, impactful reports for decision-makers. "
        "Lead with insights, support with data, and end with actionable recommendations. "
        "Always respond with valid JSON."
    ),
    output_format="json",
    temperature=0.4,
    max_tokens=1000,
    category="data",
    tags=["report", "analysis", "data", "insights"],
    icon="file-text",
    few_shot_examples=[
        {
            "input": "Topic: Q4 website traffic analysis. Findings: traffic up 25%, bounce rate increased from 40% to 55%, mobile traffic now 70%, top pages shifted from blog to product pages. Sources: Google Analytics. Audience: marketing director. Period: Oct-Dec 2024.",
            "output": '{"title": "Q4 2024 Website Traffic Analysis", "executive_summary": "Website traffic grew 25% in Q4 but quality declined, with bounce rate rising from 40% to 55%. Mobile now accounts for 70% of visits. The shift from blog to product page traffic suggests paid campaigns are driving more commercial intent visits, but the landing experience needs optimization.", "methodology": "Analysis based on Google Analytics data for October-December 2024, compared against Q3 2024 baseline.", "findings": [{"finding": "Traffic volume up 25% quarter-over-quarter", "detail": "Growth driven primarily by mobile users (+35%), with desktop flat.", "significance": "positive"}, {"finding": "Bounce rate increased from 40% to 55%", "detail": "Largest increase on product pages accessed via mobile. Suggests mobile experience friction.", "significance": "negative"}, {"finding": "Traffic mix shifted from blog (60% to 40%) to product pages (25% to 45%)", "detail": "Indicates more commercial-intent traffic, likely from paid campaigns launched in October.", "significance": "mixed"}], "recommendations": [{"priority": "high", "action": "Audit mobile product page experience — 55% bounce rate suggests UX issues on mobile devices", "expected_impact": "Reducing mobile bounce rate to 40% could recover ~15% of lost conversions"}, {"priority": "medium", "action": "A/B test landing page variants for paid traffic sources", "expected_impact": "Better matching ad intent to landing content should improve engagement"}]}',
        },
    ],
)
def generate_data_report(topic: str, findings: str, sources: str = "", audience: str = "stakeholders", period: str = ""):
    pass


# ---------------------------------------------------------------------------
# Plugin class
# ---------------------------------------------------------------------------

class DataInstructionPack(TransformerPlugin):
    """AI-powered data tools: cleaning suggestions, chart descriptions, dataset summaries, outlier analysis, report generation."""

    def __init__(self):
        super().__init__("instructions_data")

    @property
    def transformers(self):
        return {}

    @property
    def instructions(self):
        return {
            "suggest_data_cleaning": suggest_data_cleaning.__instruction__,
            "describe_chart": describe_chart.__instruction__,
            "summarize_dataset": summarize_dataset.__instruction__,
            "interpret_outliers": interpret_outliers.__instruction__,
            "generate_data_report": generate_data_report.__instruction__,
        }

    @property
    def manifest(self):
        return PluginManifest(
            name="instructions_data",
            display_name="Data Instructions",
            description="AI-powered data tools: cleaning suggestions, chart descriptions, dataset summaries, outlier analysis, and report generation.",
            icon="database",
            group="Instructions",
            requires=PluginRequirements(network=True),
        )
