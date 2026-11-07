import pytest

from markwise.services.grader import GradingError, grade_submission, parse_result

GOOD = '{"score": 7, "per_question": [], "feedback": "ok", "confidence": "high"}'
SOLUTION = SUBMISSION = {"type": "text", "text": "x"}


class Scripted:
    def __init__(self, *replies):
        self.replies, self.calls = list(replies), 0

    def generate(self, prompt, solution, submission):
        self.calls += 1
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply


def test_score_is_clamped():
    assert parse_result('{"score": 99, "feedback": "x"}', 10)["score"] == 10
    assert parse_result('{"score": -5, "feedback": "x"}', 10)["score"] == 0


def test_fenced_json_accepted():
    assert parse_result("```json\n" + GOOD + "\n```", 10)["score"] == 7


def test_parts_not_adding_up_lowers_confidence():
    raw = '{"score": 7, "per_question": [{"marks": 2}, {"marks": 2}], "confidence": "high"}'
    assert parse_result(raw, 10)["confidence"] == "low"


def test_bad_json_retried_once():
    client = Scripted("not json", GOOD)
    assert grade_submission(client, 10, "", SOLUTION, SUBMISSION)["score"] == 7
    assert client.calls == 2


def test_bad_json_twice_fails():
    with pytest.raises(GradingError):
        grade_submission(Scripted("no", "no"), 10, "", SOLUTION, SUBMISSION)


def test_rate_limit_backs_off():
    sleeps = []
    client = Scripted(Exception("429 RESOURCE_EXHAUSTED"), Exception("429"), GOOD)
    result = grade_submission(client, 10, "", SOLUTION, SUBMISSION, sleep=sleeps.append)
    assert result["score"] == 7 and sleeps == [5, 10]
