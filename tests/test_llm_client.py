from app.services.llm_client import LLMClient


def test_parse_json_object_plain_json() -> None:
    result = LLMClient._parse_json_object('{"out_of_scope": false, "sql": "SELECT 1"}')
    assert result['out_of_scope'] is False
    assert result['sql'] == 'SELECT 1'


def test_parse_json_object_markdown_fence() -> None:
    result = LLMClient._parse_json_object(
        '```json\n{"mode":"list","topic_reset":false}\n```'
    )
    assert result['mode'] == 'list'
    assert result['topic_reset'] is False
