"""Tests for the Feedback plugin."""

import pytest

from tukuy.plugins.feedback import (
    FeedbackPlugin,
    feedback_create,
    feedback_validate,
    feedback_submit,
    feedback_analyze,
    feedback_summary,
)
from tukuy.safety import SafetyPolicy


# ── Fixtures ─────────────────────────────────────────────────────────────


@pytest.fixture
def sample_form():
    """Build a standard test form with one of each question type."""
    questions = [
        {"id": "q_text", "type": "text", "text": "Any comments?"},
        {
            "id": "q_rating",
            "type": "rating",
            "text": "Rate the service",
            "min_value": 1,
            "max_value": 5,
        },
        {
            "id": "q_choice",
            "type": "choice",
            "text": "Favourite colour",
            "options": ["Red", "Green", "Blue"],
        },
        {
            "id": "q_multi",
            "type": "multi_choice",
            "text": "Select topics",
            "options": ["Python", "Rust", "Go", "Java"],
        },
        {"id": "q_yesno", "type": "yes_no", "text": "Would you recommend?"},
        {
            "id": "q_scale",
            "type": "scale",
            "text": "Satisfaction",
            "min_value": 1,
            "max_value": 10,
        },
    ]
    result = feedback_create.__skill__.invoke(
        title="Test Form",
        questions=questions,
    )
    assert result.success is True
    return result.value


# ── TestFeedbackCreate ───────────────────────────────────────────────────


class TestFeedbackCreate:
    def test_basic_form(self):
        questions = [
            {"type": "text", "text": "Name?"},
            {"type": "text", "text": "Email?"},
        ]
        result = feedback_create.__skill__.invoke(
            title="Basic Form",
            questions=questions,
        )
        assert result.success is True
        v = result.value
        assert "form_id" in v
        assert v["title"] == "Basic Form"
        assert v["question_count"] == 2
        assert "created_at" in v

    def test_form_with_all_question_types(self):
        questions = [
            {"type": "text", "text": "Q1"},
            {"type": "rating", "text": "Q2", "min_value": 1, "max_value": 5},
            {"type": "choice", "text": "Q3", "options": ["A", "B"]},
            {"type": "multi_choice", "text": "Q4", "options": ["X", "Y"]},
            {"type": "yes_no", "text": "Q5"},
            {"type": "scale", "text": "Q6", "min_value": 1, "max_value": 10},
        ]
        result = feedback_create.__skill__.invoke(
            title="All Types",
            questions=questions,
        )
        assert result.success is True
        assert result.value["question_count"] == 6

    def test_auto_generates_question_ids(self):
        questions = [
            {"type": "text", "text": "First"},
            {"type": "text", "text": "Second"},
        ]
        result = feedback_create.__skill__.invoke(
            title="Auto IDs",
            questions=questions,
        )
        assert result.success is True
        q_list = result.value["questions"]
        assert q_list[0]["id"] == "q1"
        assert q_list[1]["id"] == "q2"

    def test_preserves_custom_ids(self):
        questions = [
            {"id": "custom_one", "type": "text", "text": "First"},
            {"id": "custom_two", "type": "text", "text": "Second"},
        ]
        result = feedback_create.__skill__.invoke(
            title="Custom IDs",
            questions=questions,
        )
        assert result.success is True
        q_list = result.value["questions"]
        assert q_list[0]["id"] == "custom_one"
        assert q_list[1]["id"] == "custom_two"

    def test_empty_title_fails(self):
        questions = [{"type": "text", "text": "Q"}]
        result = feedback_create.__skill__.invoke(
            title="",
            questions=questions,
        )
        assert result.success is False

    def test_no_questions_fails(self):
        result = feedback_create.__skill__.invoke(
            title="Empty",
            questions=[],
        )
        assert result.success is False

    def test_invalid_question_type_fails(self):
        questions = [{"type": "invalid", "text": "Bad type"}]
        result = feedback_create.__skill__.invoke(
            title="Bad",
            questions=questions,
        )
        assert result.success is False

    def test_choice_without_options_fails(self):
        questions = [{"type": "choice", "text": "Pick one"}]
        result = feedback_create.__skill__.invoke(
            title="Missing opts",
            questions=questions,
        )
        assert result.success is False

    def test_multi_choice_without_options_fails(self):
        questions = [{"type": "multi_choice", "text": "Pick many"}]
        result = feedback_create.__skill__.invoke(
            title="Missing opts",
            questions=questions,
        )
        assert result.success is False

    def test_optional_description(self):
        questions = [{"type": "text", "text": "Q"}]
        result = feedback_create.__skill__.invoke(
            title="With Desc",
            questions=questions,
            description="A helpful description",
        )
        assert result.success is True
        assert result.value["description"] == "A helpful description"

    def test_rating_custom_range(self):
        questions = [
            {
                "type": "rating",
                "text": "Rate 0-10",
                "min_value": 0,
                "max_value": 10,
            }
        ]
        result = feedback_create.__skill__.invoke(
            title="Custom Range",
            questions=questions,
        )
        assert result.success is True
        q = result.value["questions"][0]
        assert q["min_value"] == 0
        assert q["max_value"] == 10


# ── TestFeedbackValidate ─────────────────────────────────────────────────


class TestFeedbackValidate:
    def _full_responses(self, **overrides):
        """Return a complete valid response set, with optional overrides."""
        base = {
            "q_text": "Great service!",
            "q_rating": 3,
            "q_choice": "Red",
            "q_multi": ["Python", "Rust"],
            "q_yesno": True,
            "q_scale": 7,
        }
        base.update(overrides)
        return base

    def test_valid_text_response(self, sample_form):
        result = feedback_validate.__skill__.invoke(
            form=sample_form,
            responses=self._full_responses(q_text="Great service!"),
        )
        assert result.success is True
        assert result.value["valid"] is True

    def test_valid_rating_response(self, sample_form):
        result = feedback_validate.__skill__.invoke(
            form=sample_form,
            responses=self._full_responses(q_rating=3),
        )
        assert result.success is True
        assert result.value["valid"] is True

    def test_valid_choice_response(self, sample_form):
        result = feedback_validate.__skill__.invoke(
            form=sample_form,
            responses=self._full_responses(q_choice="Red"),
        )
        assert result.success is True
        assert result.value["valid"] is True

    def test_valid_multi_choice_response(self, sample_form):
        result = feedback_validate.__skill__.invoke(
            form=sample_form,
            responses=self._full_responses(q_multi=["Python", "Rust"]),
        )
        assert result.success is True
        assert result.value["valid"] is True

    def test_valid_yes_no_response(self, sample_form):
        result = feedback_validate.__skill__.invoke(
            form=sample_form,
            responses=self._full_responses(q_yesno=True),
        )
        assert result.success is True
        assert result.value["valid"] is True

    def test_valid_scale_response(self, sample_form):
        result = feedback_validate.__skill__.invoke(
            form=sample_form,
            responses=self._full_responses(q_scale=7),
        )
        assert result.success is True
        assert result.value["valid"] is True

    def test_missing_required_response(self):
        questions = [
            {"id": "q1", "type": "text", "text": "Name?", "required": True}
        ]
        form_result = feedback_create.__skill__.invoke(
            title="Required",
            questions=questions,
        )
        assert form_result.success is True

        result = feedback_validate.__skill__.invoke(
            form=form_result.value,
            responses={},
        )
        assert result.success is True
        assert result.value["valid"] is False
        assert len(result.value["errors"]) > 0

    def test_optional_question_can_be_skipped(self):
        questions = [
            {"id": "q1", "type": "text", "text": "Optional?", "required": False}
        ]
        form_result = feedback_create.__skill__.invoke(
            title="Optional",
            questions=questions,
        )
        assert form_result.success is True

        result = feedback_validate.__skill__.invoke(
            form=form_result.value,
            responses={},
        )
        assert result.success is True
        assert result.value["valid"] is True

    def test_rating_out_of_range(self):
        questions = [
            {
                "id": "q1",
                "type": "rating",
                "text": "Rate",
                "min_value": 1,
                "max_value": 5,
            }
        ]
        form_result = feedback_create.__skill__.invoke(
            title="Range check",
            questions=questions,
        )
        assert form_result.success is True

        result = feedback_validate.__skill__.invoke(
            form=form_result.value,
            responses={"q1": 6},
        )
        assert result.success is True
        assert result.value["valid"] is False
        assert len(result.value["errors"]) > 0

    def test_choice_invalid_option(self):
        questions = [
            {
                "id": "q1",
                "type": "choice",
                "text": "Pick",
                "options": ["A", "B"],
            }
        ]
        form_result = feedback_create.__skill__.invoke(
            title="Invalid opt",
            questions=questions,
        )
        assert form_result.success is True

        result = feedback_validate.__skill__.invoke(
            form=form_result.value,
            responses={"q1": "C"},
        )
        assert result.success is True
        assert result.value["valid"] is False
        assert len(result.value["errors"]) > 0

    def test_multi_choice_invalid_option(self):
        questions = [
            {
                "id": "q1",
                "type": "multi_choice",
                "text": "Pick many",
                "options": ["X", "Y", "Z"],
            }
        ]
        form_result = feedback_create.__skill__.invoke(
            title="Invalid multi",
            questions=questions,
        )
        assert form_result.success is True

        result = feedback_validate.__skill__.invoke(
            form=form_result.value,
            responses={"q1": ["X", "INVALID"]},
        )
        assert result.success is True
        assert result.value["valid"] is False
        assert len(result.value["errors"]) > 0

    def test_text_exceeds_max_length(self):
        questions = [
            {
                "id": "q1",
                "type": "text",
                "text": "Short answer",
                "max_length": 10,
            }
        ]
        form_result = feedback_create.__skill__.invoke(
            title="Max len",
            questions=questions,
        )
        assert form_result.success is True

        result = feedback_validate.__skill__.invoke(
            form=form_result.value,
            responses={"q1": "This is way too long for the limit"},
        )
        assert result.success is True
        assert result.value["valid"] is False
        assert len(result.value["errors"]) > 0

    def test_yes_no_non_boolean(self):
        questions = [
            {"id": "q1", "type": "yes_no", "text": "Yes or no?"}
        ]
        form_result = feedback_create.__skill__.invoke(
            title="Bool check",
            questions=questions,
        )
        assert form_result.success is True

        result = feedback_validate.__skill__.invoke(
            form=form_result.value,
            responses={"q1": "maybe"},
        )
        assert result.success is True
        assert result.value["valid"] is False
        assert len(result.value["errors"]) > 0

    def test_all_valid_returns_counts(self, sample_form):
        responses = {
            "q_text": "Hello",
            "q_rating": 4,
            "q_choice": "Green",
            "q_multi": ["Python"],
            "q_yesno": False,
            "q_scale": 8,
        }
        result = feedback_validate.__skill__.invoke(
            form=sample_form,
            responses=responses,
        )
        assert result.success is True
        assert result.value["valid"] is True
        assert result.value["answered"] == 6
        assert result.value["total"] == 6


# ── TestFeedbackSubmit ───────────────────────────────────────────────────


class TestFeedbackSubmit:
    def test_valid_submission(self, sample_form):
        responses = {
            "q_text": "Looks good",
            "q_rating": 5,
            "q_choice": "Blue",
            "q_multi": ["Go", "Rust"],
            "q_yesno": True,
            "q_scale": 9,
        }
        result = feedback_submit.__skill__.invoke(
            form=sample_form,
            responses=responses,
        )
        assert result.success is True
        v = result.value
        assert "submission_id" in v
        assert v["form_id"] == sample_form["form_id"]
        assert "submitted_at" in v
        assert isinstance(v["responses"], list)
        assert len(v["responses"]) == 6

    def test_submission_with_respondent(self, sample_form):
        responses = {
            "q_text": "Nice",
            "q_rating": 4,
            "q_choice": "Red",
            "q_multi": ["Java"],
            "q_yesno": False,
            "q_scale": 7,
        }
        result = feedback_submit.__skill__.invoke(
            form=sample_form,
            responses=responses,
            respondent="Alice",
        )
        assert result.success is True
        assert result.value["respondent"] == "Alice"

    def test_invalid_submission_fails(self):
        questions = [
            {"id": "q1", "type": "text", "text": "Name?", "required": True}
        ]
        form_result = feedback_create.__skill__.invoke(
            title="Required Form",
            questions=questions,
        )
        assert form_result.success is True

        result = feedback_submit.__skill__.invoke(
            form=form_result.value,
            responses={},
        )
        assert result.success is False

    def test_response_structure(self, sample_form):
        responses = {
            "q_text": "Test",
            "q_rating": 3,
            "q_choice": "Green",
            "q_multi": ["Python"],
            "q_yesno": True,
            "q_scale": 5,
        }
        result = feedback_submit.__skill__.invoke(
            form=sample_form,
            responses=responses,
        )
        assert result.success is True
        for resp in result.value["responses"]:
            assert "question_id" in resp
            assert "question_text" in resp
            assert "question_type" in resp
            assert "answer" in resp


# ── TestFeedbackAnalyze ──────────────────────────────────────────────────


class TestFeedbackAnalyze:
    def _make_submissions(self, form, response_sets):
        """Helper: submit multiple response sets and return the list."""
        submissions = []
        for responses in response_sets:
            result = feedback_submit.__skill__.invoke(
                form=form,
                responses=responses,
            )
            assert result.success is True
            submissions.append(result.value)
        return submissions

    def test_analyze_text_questions(self):
        questions = [{"id": "q1", "type": "text", "text": "Comment"}]
        form = feedback_create.__skill__.invoke(
            title="Text Analysis",
            questions=questions,
        ).value
        submissions = self._make_submissions(form, [
            {"q1": "Short"},
            {"q1": "A medium length response"},
            {"q1": "This is a somewhat longer response text"},
        ])
        result = feedback_analyze.__skill__.invoke(
            form=form,
            submissions=submissions,
        )
        assert result.success is True
        q_analysis = result.value["analysis"]["q1"]
        assert q_analysis["response_count"] == 3
        assert "avg_length" in q_analysis

    def test_analyze_rating_questions(self):
        questions = [
            {
                "id": "q1",
                "type": "rating",
                "text": "Rate",
                "min_value": 1,
                "max_value": 5,
            }
        ]
        form = feedback_create.__skill__.invoke(
            title="Rating Analysis",
            questions=questions,
        ).value
        submissions = self._make_submissions(form, [
            {"q1": 2},
            {"q1": 4},
            {"q1": 5},
        ])
        result = feedback_analyze.__skill__.invoke(
            form=form,
            submissions=submissions,
        )
        assert result.success is True
        q_analysis = result.value["analysis"]["q1"]
        assert "average" in q_analysis
        assert "min" in q_analysis
        assert "max" in q_analysis
        assert "distribution" in q_analysis

    def test_analyze_choice_questions(self):
        questions = [
            {
                "id": "q1",
                "type": "choice",
                "text": "Pick",
                "options": ["A", "B", "C"],
            }
        ]
        form = feedback_create.__skill__.invoke(
            title="Choice Analysis",
            questions=questions,
        ).value
        submissions = self._make_submissions(form, [
            {"q1": "A"},
            {"q1": "A"},
            {"q1": "B"},
        ])
        result = feedback_analyze.__skill__.invoke(
            form=form,
            submissions=submissions,
        )
        assert result.success is True
        q_analysis = result.value["analysis"]["q1"]
        assert "distribution" in q_analysis
        assert "most_common" in q_analysis

    def test_analyze_multi_choice(self):
        questions = [
            {
                "id": "q1",
                "type": "multi_choice",
                "text": "Topics",
                "options": ["X", "Y", "Z"],
            }
        ]
        form = feedback_create.__skill__.invoke(
            title="Multi Analysis",
            questions=questions,
        ).value
        submissions = self._make_submissions(form, [
            {"q1": ["X", "Y"]},
            {"q1": ["Y", "Z"]},
            {"q1": ["X"]},
        ])
        result = feedback_analyze.__skill__.invoke(
            form=form,
            submissions=submissions,
        )
        assert result.success is True
        q_analysis = result.value["analysis"]["q1"]
        assert "distribution" in q_analysis
        assert "avg_selections" in q_analysis

    def test_analyze_yes_no(self):
        questions = [{"id": "q1", "type": "yes_no", "text": "Recommend?"}]
        form = feedback_create.__skill__.invoke(
            title="YN Analysis",
            questions=questions,
        ).value
        submissions = self._make_submissions(form, [
            {"q1": True},
            {"q1": True},
            {"q1": False},
        ])
        result = feedback_analyze.__skill__.invoke(
            form=form,
            submissions=submissions,
        )
        assert result.success is True
        q_analysis = result.value["analysis"]["q1"]
        assert q_analysis["yes_count"] == 2
        assert q_analysis["no_count"] == 1
        assert "yes_percentage" in q_analysis

    def test_analyze_scale(self):
        questions = [
            {
                "id": "q1",
                "type": "scale",
                "text": "Satisfaction",
                "min_value": 1,
                "max_value": 10,
            }
        ]
        form = feedback_create.__skill__.invoke(
            title="Scale Analysis",
            questions=questions,
        ).value
        submissions = self._make_submissions(form, [
            {"q1": 3},
            {"q1": 7},
            {"q1": 9},
        ])
        result = feedback_analyze.__skill__.invoke(
            form=form,
            submissions=submissions,
        )
        assert result.success is True
        q_analysis = result.value["analysis"]["q1"]
        assert "average" in q_analysis
        assert "min" in q_analysis
        assert "max" in q_analysis
        assert "distribution" in q_analysis

    def test_analyze_empty_submissions(self):
        questions = [{"id": "q1", "type": "text", "text": "Comment"}]
        form = feedback_create.__skill__.invoke(
            title="Empty Analysis",
            questions=questions,
        ).value
        result = feedback_analyze.__skill__.invoke(
            form=form,
            submissions=[],
        )
        assert result.success is True
        assert result.value["total_submissions"] == 0


# ── TestFeedbackSummary ──────────────────────────────────────────────────


class TestFeedbackSummary:
    def _build_analysis(self):
        """Helper: create a form, submit data, and return the analysis."""
        questions = [
            {
                "id": "q1",
                "type": "rating",
                "text": "Rate the event",
                "min_value": 1,
                "max_value": 5,
            },
            {"id": "q2", "type": "yes_no", "text": "Would you attend again?"},
        ]
        form = feedback_create.__skill__.invoke(
            title="Event Feedback",
            questions=questions,
        ).value
        submissions = []
        for rating, attend in [(5, True), (4, True), (3, False)]:
            sub = feedback_submit.__skill__.invoke(
                form=form,
                responses={"q1": rating, "q2": attend},
            )
            assert sub.success is True
            submissions.append(sub.value)

        analysis = feedback_analyze.__skill__.invoke(
            form=form,
            submissions=submissions,
        )
        assert analysis.success is True
        return form, analysis.value

    def test_summary_generation(self):
        form, analysis = self._build_analysis()
        result = feedback_summary.__skill__.invoke(
            analysis=analysis,
        )
        assert result.success is True
        summary_text = result.value["summary"]
        assert isinstance(summary_text, str)
        assert len(summary_text) > 0
        assert form["title"] in summary_text

    def test_summary_contains_stats(self):
        form, analysis = self._build_analysis()
        result = feedback_summary.__skill__.invoke(
            analysis=analysis,
        )
        assert result.success is True
        summary_text = result.value["summary"]
        # Should mention key statistics like count or averages
        assert "3" in summary_text  # total submissions


# ── Plugin registration ──────────────────────────────────────────────────


class TestFeedbackPlugin:
    def test_plugin_name(self):
        plugin = FeedbackPlugin()
        assert plugin.name == "feedback"

    def test_no_transformers(self):
        plugin = FeedbackPlugin()
        assert plugin.transformers == {}

    def test_has_all_skills(self):
        plugin = FeedbackPlugin()
        names = set(plugin.skills.keys())
        assert names == {
            "feedback_create",
            "feedback_validate",
            "feedback_submit",
            "feedback_analyze",
            "feedback_summary",
        }

    def test_manifest(self):
        plugin = FeedbackPlugin()
        m = plugin.manifest
        assert m.name == "feedback"
        assert m.display_name is not None
        assert m.group is not None
