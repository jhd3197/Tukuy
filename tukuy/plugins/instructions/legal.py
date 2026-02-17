"""Legal instruction pack -- AI-powered legal assistance tools.

Provides instructions for contract summarization, clause risk analysis,
terms simplification, compliance checking, and NDA review.

Note: These tools provide informational assistance only and do not
constitute legal advice. Always consult a qualified attorney.
"""

from ...instruction import instruction
from ...manifest import PluginManifest, PluginRequirements
from ..base import TransformerPlugin


# ---------------------------------------------------------------------------
# Instructions
# ---------------------------------------------------------------------------

@instruction(
    name="summarize_contract",
    description="Summarize key terms, obligations, and dates from a contract or agreement",
    prompt=(
        "Summarize the following contract or agreement. Extract key terms, "
        "obligations for each party, important dates, and any unusual clauses.\n\n"
        "Contract Text: {text}\n"
        "Contract Type: {contract_type}\n"
        "Focus Areas: {focus}"
    ),
    system_prompt=(
        "You are a legal analyst specializing in contract review. Extract key information "
        "clearly and flag anything unusual. Always include a disclaimer that this is not legal advice. "
        "Always respond with valid JSON."
    ),
    output_format="json",
    temperature=0.2,
    max_tokens=1000,
    category="legal",
    tags=["contract", "summary", "legal", "review"],
    icon="file-text",
    few_shot_examples=[
        {
            "input": "Contract: Software license agreement between Acme Corp (licensor) and Beta Inc (licensee). 3-year term starting Jan 1 2025. $50k/year. Auto-renews unless 90-day notice. Licensor can terminate for breach with 30-day cure period. Licensee gets source code escrow. Governing law: Delaware. Type: software license. Focus: obligations and termination.",
            "output": '{"contract_type": "Software License Agreement", "parties": {"licensor": "Acme Corp", "licensee": "Beta Inc"}, "key_terms": {"term": "3 years (Jan 1, 2025 - Dec 31, 2027)", "annual_fee": "$50,000", "auto_renewal": "Yes, unless 90-day written notice before expiration", "governing_law": "Delaware"}, "obligations": {"licensor": ["Provide and maintain software license", "Maintain source code escrow"], "licensee": ["Pay $50k annually", "Comply with license usage terms"]}, "termination": {"for_breach": "Either party with 30-day cure period", "for_convenience": "90-day notice before renewal date"}, "notable_clauses": ["Source code escrow protects licensee if licensor ceases operations", "Auto-renewal requires proactive cancellation"], "disclaimer": "This summary is for informational purposes only and does not constitute legal advice."}',
        },
    ],
)
def summarize_contract(text: str, contract_type: str = "general", focus: str = "all key terms"):
    pass


@instruction(
    name="clause_risk_analysis",
    description="Analyze specific contract clauses for potential risks and suggest alternatives",
    prompt=(
        "Analyze the following contract clause for potential risks. Identify what "
        "could go wrong, who bears the risk, and suggest alternative language.\n\n"
        "Clause Text: {clause}\n"
        "Your Role: {role}\n"
        "Contract Context: {context}"
    ),
    system_prompt=(
        "You are a contract negotiation expert. Identify risks with precision and "
        "suggest balanced alternative language. Always include a disclaimer. "
        "Always respond with valid JSON."
    ),
    output_format="json",
    temperature=0.3,
    max_tokens=800,
    category="legal",
    tags=["clause", "risk", "legal", "negotiation"],
    icon="alert-triangle",
    few_shot_examples=[
        {
            "input": "Clause: 'Contractor shall indemnify and hold harmless Client from any and all claims, damages, losses, and expenses, including attorney fees, arising out of or related to the services.' Role: contractor. Context: freelance software development agreement.",
            "output": '{"risk_level": "high", "risks": [{"risk": "Unlimited indemnification scope", "explanation": "The clause covers ANY claims related to the services, not just those caused by contractor negligence. You could be liable for client misuse of your deliverables.", "who_bears_risk": "Contractor (entirely)"}, {"risk": "No cap on liability", "explanation": "Without a liability cap, exposure could far exceed the contract value.", "who_bears_risk": "Contractor"}], "suggested_revision": "Contractor shall indemnify Client from claims arising directly from Contractor gross negligence or willful misconduct in performing the services, subject to a liability cap equal to the total fees paid under this agreement.", "negotiation_tips": ["Request mutual indemnification", "Add a liability cap (typically 1-2x contract value)", "Limit scope to direct damages caused by your negligence"], "disclaimer": "This analysis is for informational purposes only and does not constitute legal advice."}',
        },
    ],
)
def clause_risk_analysis(clause: str, role: str = "reviewing party", context: str = ""):
    pass


@instruction(
    name="simplify_terms",
    description="Rewrite legal text in plain, easy-to-understand language",
    prompt=(
        "Rewrite the following legal text in plain language that a non-lawyer can "
        "easily understand. Preserve the meaning but remove jargon.\n\n"
        "Legal Text: {text}\n"
        "Audience: {audience}"
    ),
    system_prompt=(
        "You are a plain-language legal writing expert. Translate legal jargon into "
        "clear, everyday language without losing the meaning. "
        "Always respond with valid JSON."
    ),
    output_format="json",
    temperature=0.4,
    max_tokens=800,
    category="legal",
    tags=["plain-language", "simplify", "legal", "clarity"],
    icon="edit",
    few_shot_examples=[
        {
            "input": "Text: 'Notwithstanding any provision herein to the contrary, in no event shall either party be liable to the other for any indirect, incidental, consequential, special, or exemplary damages arising out of or related to this agreement, including but not limited to loss of revenue, loss of profits, loss of business, or loss of data.' Audience: small business owner.",
            "output": '{"plain_language": "Even if something goes wrong under this agreement, neither side can sue the other for indirect losses like lost profits, lost revenue, or lost data. You can only claim direct damages — meaning the actual, immediate cost of what went wrong.", "key_points": ["Neither side pays for indirect or ripple-effect losses", "Only direct, provable damages are recoverable", "This applies no matter what else the contract says"], "terms_explained": [{"term": "consequential damages", "meaning": "Losses that are a secondary result of a problem, like lost profits because a system was down"}, {"term": "notwithstanding", "meaning": "Regardless of / even if other parts of the contract say something different"}, {"term": "exemplary damages", "meaning": "Extra money awarded as punishment, beyond actual losses"}]}',
        },
    ],
)
def simplify_terms(text: str, audience: str = "general public"):
    pass


@instruction(
    name="compliance_checklist",
    description="Generate a compliance checklist for a specific regulation or standard",
    prompt=(
        "Create a compliance checklist for the specified regulation or standard. "
        "Include key requirements, common gaps, and practical steps to achieve compliance.\n\n"
        "Regulation/Standard: {regulation}\n"
        "Business Type: {business_type}\n"
        "Current Status: {current_status}\n"
        "Priority Areas: {priorities}"
    ),
    system_prompt=(
        "You are a compliance consultant. Create actionable checklists that help "
        "businesses understand and meet regulatory requirements. Be specific and practical. "
        "Always include a disclaimer. Always respond with valid JSON."
    ),
    output_format="json",
    temperature=0.3,
    max_tokens=1000,
    category="legal",
    tags=["compliance", "regulation", "legal", "checklist"],
    icon="check-square",
    few_shot_examples=[
        {
            "input": "Regulation: GDPR. Business type: SaaS startup processing EU customer data. Current status: no formal compliance program. Priorities: data collection, consent, breach notification.",
            "output": '{"regulation": "GDPR (General Data Protection Regulation)", "checklist": [{"category": "Data Collection & Consent", "items": [{"requirement": "Obtain explicit consent before collecting personal data", "status": "to_do", "priority": "high", "action": "Implement cookie consent banner and update sign-up forms with clear consent checkboxes"}, {"requirement": "Maintain records of consent", "status": "to_do", "priority": "high", "action": "Set up a consent management system that logs when and how consent was obtained"}]}, {"category": "Breach Notification", "items": [{"requirement": "Notify supervisory authority within 72 hours of a breach", "status": "to_do", "priority": "high", "action": "Create an incident response plan with notification templates and escalation contacts"}, {"requirement": "Notify affected individuals if breach poses high risk", "status": "to_do", "priority": "high", "action": "Draft notification templates and define risk assessment criteria"}]}], "common_gaps": ["No Data Protection Officer appointed", "Privacy policy missing or outdated", "No data processing agreements with third-party vendors"], "disclaimer": "This checklist is for guidance only and does not constitute legal advice. Consult a qualified data protection officer or attorney."}',
        },
    ],
)
def compliance_checklist(regulation: str, business_type: str, current_status: str = "unknown", priorities: str = ""):
    pass


@instruction(
    name="review_nda",
    description="Review a non-disclosure agreement and highlight key terms, risks, and missing protections",
    prompt=(
        "Review the following NDA and highlight key terms, potential risks, "
        "and any missing protections.\n\n"
        "NDA Text: {text}\n"
        "Your Role: {role}\n"
        "Purpose of NDA: {purpose}"
    ),
    system_prompt=(
        "You are an NDA review specialist. Identify strengths and weaknesses in "
        "confidentiality agreements with practical recommendations. Always include a disclaimer. "
        "Always respond with valid JSON."
    ),
    output_format="json",
    temperature=0.3,
    max_tokens=800,
    category="legal",
    tags=["nda", "confidentiality", "legal", "review"],
    icon="lock",
    few_shot_examples=[
        {
            "input": "NDA: Mutual NDA between StartupX and BigCorp. 2-year term. Covers all business discussions. No carve-outs for independently developed info. Discloser can seek injunctive relief. Governing law: California. Role: StartupX (smaller party). Purpose: exploring partnership.",
            "output": '{"nda_type": "Mutual", "term": "2 years", "key_terms": {"scope": "All business discussions between parties", "governing_law": "California", "remedies": "Injunctive relief available to disclosing party"}, "strengths": ["Mutual protection benefits both parties equally", "Injunctive relief clause provides enforcement teeth", "Reasonable 2-year duration"], "risks": [{"issue": "No carve-out for independently developed information", "severity": "high", "explanation": "If StartupX independently develops something similar to what BigCorp discloses, BigCorp could claim it was based on confidential information.", "recommendation": "Add standard exclusion: information independently developed without reference to confidential materials"}, {"issue": "Overly broad scope", "severity": "medium", "explanation": "Covering all business discussions could inadvertently capture routine, non-sensitive communications.", "recommendation": "Narrow scope to written materials marked Confidential or information disclosed in designated meetings"}], "missing_protections": ["No definition of what constitutes confidential information", "No residuals clause (important for StartupX engineers who may retain general knowledge)", "No return/destruction of materials clause"], "disclaimer": "This review is for informational purposes only and does not constitute legal advice."}',
        },
    ],
)
def review_nda(text: str, role: str = "reviewing party", purpose: str = ""):
    pass


# ---------------------------------------------------------------------------
# Plugin class
# ---------------------------------------------------------------------------

class LegalInstructionPack(TransformerPlugin):
    """AI-powered legal tools: contract summaries, clause risk analysis, plain-language rewrites, compliance checklists, NDA review."""

    def __init__(self):
        super().__init__("instructions_legal")

    @property
    def transformers(self):
        return {}

    @property
    def instructions(self):
        return {
            "summarize_contract": summarize_contract.__instruction__,
            "clause_risk_analysis": clause_risk_analysis.__instruction__,
            "simplify_terms": simplify_terms.__instruction__,
            "compliance_checklist": compliance_checklist.__instruction__,
            "review_nda": review_nda.__instruction__,
        }

    @property
    def manifest(self):
        return PluginManifest(
            name="instructions_legal",
            display_name="Legal Instructions",
            description="AI-powered legal tools: contract summaries, clause risk analysis, plain-language rewrites, compliance checklists, and NDA review.",
            icon="shield",
            group="Instructions",
            requires=PluginRequirements(network=True),
        )
