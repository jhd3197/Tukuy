"""Education instruction pack -- AI-powered educational tools.

Provides instructions for quiz generation, study guide creation,
lesson planning, concept explanation, and flashcard generation.
"""

from ...instruction import instruction
from ...manifest import PluginManifest, PluginRequirements
from ..base import TransformerPlugin


# ---------------------------------------------------------------------------
# Instructions
# ---------------------------------------------------------------------------

@instruction(
    name="generate_quiz",
    description="Generate a quiz with multiple question types from source material",
    prompt=(
        "Generate a quiz based on the following source material. Include a mix "
        "of question types as specified.\n\n"
        "Source Material: {material}\n"
        "Number of Questions: {num_questions}\n"
        "Question Types: {question_types}\n"
        "Difficulty Level: {difficulty}"
    ),
    system_prompt=(
        "You are an expert educator who designs effective assessments. "
        "Create questions that test understanding, not just memorization. "
        "Always respond with valid JSON."
    ),
    output_format="json",
    temperature=0.5,
    max_tokens=1000,
    category="education",
    tags=["quiz", "assessment", "education", "learning"],
    icon="help-circle",
    few_shot_examples=[
        {
            "input": "Material: Photosynthesis converts light energy into chemical energy in plants. Chlorophyll absorbs light, primarily red and blue wavelengths. The process occurs in chloroplasts and produces glucose and oxygen from CO2 and water. Questions: 3. Types: multiple choice, true/false, short answer. Difficulty: intermediate.",
            "output": '{"quiz_title": "Photosynthesis Quiz", "questions": [{"id": 1, "type": "multiple_choice", "question": "Where does photosynthesis primarily take place?", "options": ["Mitochondria", "Chloroplasts", "Cell membrane", "Nucleus"], "correct_answer": "Chloroplasts", "explanation": "Chloroplasts contain chlorophyll and are the organelles where photosynthesis occurs."}, {"id": 2, "type": "true_false", "question": "Chlorophyll primarily absorbs green light wavelengths.", "correct_answer": false, "explanation": "Chlorophyll absorbs red and blue wavelengths; green light is reflected, which is why plants appear green."}, {"id": 3, "type": "short_answer", "question": "What are the two main products of photosynthesis?", "correct_answer": "Glucose and oxygen", "explanation": "Photosynthesis converts CO2 and water into glucose (C6H12O6) and oxygen (O2)."}]}',
        },
    ],
)
def generate_quiz(material: str, num_questions: str = "5", question_types: str = "multiple choice, true/false", difficulty: str = "intermediate"):
    pass


@instruction(
    name="create_study_guide",
    description="Create a structured study guide from source material with key concepts and review questions",
    prompt=(
        "Create a comprehensive study guide from the following material. "
        "Organize by key topics, highlight important concepts, and include "
        "review questions.\n\n"
        "Subject: {subject}\n"
        "Source Material: {material}\n"
        "Target Level: {level}\n"
        "Focus Areas: {focus}"
    ),
    system_prompt=(
        "You are an expert tutor who creates study materials that maximize retention. "
        "Use clear structure, mnemonics where helpful, and active recall prompts. "
        "Always respond with valid JSON."
    ),
    output_format="json",
    temperature=0.4,
    max_tokens=1000,
    category="education",
    tags=["study-guide", "learning", "education", "review"],
    icon="book-open",
    few_shot_examples=[
        {
            "input": "Subject: Cell Biology. Material: Cells are the basic unit of life. Prokaryotes lack a nucleus; eukaryotes have one. Organelles include mitochondria (energy), ribosomes (protein synthesis), and ER (transport). Level: high school. Focus: cell types and organelles.",
            "output": '{"title": "Cell Biology Study Guide", "sections": [{"topic": "Cell Types", "key_concepts": ["Prokaryotes: no nucleus, simpler structure (bacteria)", "Eukaryotes: have a nucleus, more complex (plants, animals, fungi)"], "memory_aid": "Pro = primitive (no nucleus), Eu = true (true nucleus)"}, {"topic": "Key Organelles", "key_concepts": ["Mitochondria: powerhouse of the cell, produces ATP", "Ribosomes: protein factories, found free or on ER", "Endoplasmic Reticulum: transport network (smooth and rough)"], "memory_aid": "MRP: Mitochondria=energy, Ribosomes=proteins, ER=transport"}], "review_questions": ["What is the main structural difference between prokaryotes and eukaryotes?", "Which organelle is responsible for energy production?", "Explain the role of the endoplasmic reticulum."]}',
        },
    ],
)
def create_study_guide(subject: str, material: str, level: str = "general", focus: str = ""):
    pass


@instruction(
    name="lesson_plan",
    description="Design a structured lesson plan with objectives, activities, and assessment",
    prompt=(
        "Design a lesson plan for the given topic. Include learning objectives, "
        "activities, timing, materials needed, and assessment methods.\n\n"
        "Topic: {topic}\n"
        "Grade/Level: {level}\n"
        "Duration: {duration}\n"
        "Learning Style Preference: {learning_style}"
    ),
    system_prompt=(
        "You are an experienced curriculum designer. Create engaging lesson plans "
        "that accommodate different learning styles and include active learning. "
        "Always respond with valid JSON."
    ),
    output_format="json",
    temperature=0.5,
    max_tokens=800,
    category="education",
    tags=["lesson-plan", "teaching", "education", "curriculum"],
    icon="clipboard",
    few_shot_examples=[
        {
            "input": "Topic: Introduction to Fractions. Level: 4th grade. Duration: 45 minutes. Learning style: visual and hands-on.",
            "output": '{"title": "Introduction to Fractions", "grade": "4th grade", "duration_minutes": 45, "objectives": ["Students can identify numerator and denominator", "Students can represent fractions visually", "Students can compare simple fractions"], "materials": ["Fraction circle manipulatives", "Whiteboard and markers", "Worksheet with fraction diagrams"], "activities": [{"time": "0-5 min", "activity": "Warm-up: Pizza Sharing Problem", "description": "Ask: If 4 friends share 1 pizza equally, how much does each get?", "type": "discussion"}, {"time": "5-15 min", "activity": "Direct Instruction", "description": "Introduce numerator/denominator using pizza and pie visuals", "type": "visual"}, {"time": "15-30 min", "activity": "Hands-on Exploration", "description": "Students use fraction circles to build and compare fractions", "type": "hands-on"}, {"time": "30-40 min", "activity": "Guided Practice", "description": "Complete fraction worksheet in pairs", "type": "collaborative"}, {"time": "40-45 min", "activity": "Exit Ticket", "description": "Draw and label 3/4 and explain which is larger: 1/2 or 1/3", "type": "assessment"}], "assessment": "Exit ticket evaluating visual representation and comparison skills"}',
        },
    ],
)
def lesson_plan(topic: str, level: str, duration: str = "45 minutes", learning_style: str = "mixed"):
    pass


@instruction(
    name="explain_concept",
    description="Explain a complex concept in simple terms with analogies and examples",
    prompt=(
        "Explain the following concept in a way that is easy to understand. "
        "Use analogies, real-world examples, and build from simple to complex.\n\n"
        "Concept: {concept}\n"
        "Audience Level: {level}\n"
        "Context: {context}"
    ),
    system_prompt=(
        "You are a gifted teacher who can explain anything to anyone. "
        "Use the Feynman technique: simple language, analogies, and examples. "
        "Always respond with valid JSON."
    ),
    output_format="json",
    temperature=0.6,
    max_tokens=800,
    category="education",
    tags=["explanation", "learning", "education", "concepts"],
    icon="lightbulb",
    few_shot_examples=[
        {
            "input": "Concept: Machine Learning. Level: complete beginner. Context: explaining to a non-technical business executive.",
            "output": '{"simple_definition": "Machine learning is teaching computers to learn from examples instead of giving them explicit rules.", "analogy": "Imagine training a new employee. Instead of giving them a 500-page manual, you show them 1,000 examples of good work and bad work. Eventually, they learn to tell the difference on their own. That\'s machine learning.", "real_world_examples": ["Netflix recommending shows based on what you\'ve watched", "Email spam filters that get better over time", "Phone keyboards predicting your next word"], "key_takeaway": "ML lets software improve through experience rather than manual programming — the more data it sees, the smarter it gets.", "common_misconceptions": ["ML is not the same as general AI or sentient robots", "It requires large amounts of quality data to work well", "It can be wrong — it learns patterns, including bad ones"]}',
        },
    ],
)
def explain_concept(concept: str, level: str = "beginner", context: str = ""):
    pass


@instruction(
    name="generate_flashcards",
    description="Generate study flashcards with questions on the front and answers on the back",
    prompt=(
        "Generate flashcards for studying the given topic. Each card should have "
        "a clear question/prompt on the front and a concise answer on the back.\n\n"
        "Topic: {topic}\n"
        "Source Material: {material}\n"
        "Number of Cards: {num_cards}\n"
        "Card Style: {style}"
    ),
    system_prompt=(
        "You are a study tools expert who creates flashcards optimized for spaced "
        "repetition and active recall. Keep answers concise but complete. "
        "Always respond with valid JSON."
    ),
    output_format="json",
    temperature=0.4,
    max_tokens=800,
    category="education",
    tags=["flashcards", "study", "education", "memorization"],
    icon="layers",
    few_shot_examples=[
        {
            "input": "Topic: Spanish vocabulary - food. Material: common restaurant and kitchen words. Cards: 3. Style: term and definition with example sentence.",
            "output": '{"flashcards": [{"front": "la cuenta", "back": "the bill/check", "example": "La cuenta, por favor. (The check, please.)", "difficulty": "easy"}, {"front": "probar", "back": "to try/taste", "example": "\u00bfQuieres probar mi postre? (Do you want to try my dessert?)", "difficulty": "medium"}, {"front": "la propina", "back": "the tip (gratuity)", "example": "Dej\u00e9 una buena propina. (I left a good tip.)", "difficulty": "medium"}], "study_tip": "Practice these in context by imagining yourself ordering at a restaurant."}',
        },
    ],
)
def generate_flashcards(topic: str, material: str = "", num_cards: str = "10", style: str = "question and answer"):
    pass


# ---------------------------------------------------------------------------
# Plugin class
# ---------------------------------------------------------------------------

class EducationInstructionPack(TransformerPlugin):
    """AI-powered education tools: quizzes, study guides, lesson plans, concept explanations, flashcards."""

    def __init__(self):
        super().__init__("instructions_education")

    @property
    def transformers(self):
        return {}

    @property
    def instructions(self):
        return {
            "generate_quiz": generate_quiz.__instruction__,
            "create_study_guide": create_study_guide.__instruction__,
            "lesson_plan": lesson_plan.__instruction__,
            "explain_concept": explain_concept.__instruction__,
            "generate_flashcards": generate_flashcards.__instruction__,
        }

    @property
    def manifest(self):
        return PluginManifest(
            name="instructions_education",
            display_name="Education Instructions",
            description="AI-powered education tools: quiz generation, study guides, lesson plans, concept explanations, and flashcards.",
            icon="book",
            group="Instructions",
            requires=PluginRequirements(network=True),
        )
