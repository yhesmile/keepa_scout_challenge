from app.config import Settings


def test_resolved_llm_model_for_deepseek() -> None:
    settings = Settings(
        DEEPSEEK_API_KEY='dummy-key',
    )
    assert settings.resolved_llm_model == 'deepseek-chat'


def test_resolved_llm_model_keeps_explicit_value() -> None:
    settings = Settings(
        DEEPSEEK_API_KEY='dummy-key',
        LLM_MODEL='deepseek-reasoner',
    )
    assert settings.resolved_llm_model == 'deepseek-reasoner'
