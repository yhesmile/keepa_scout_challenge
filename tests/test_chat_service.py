from app.config import Settings
from app.services.chat_service import ChatService


def test_apply_intent_replaces_filters_and_budget() -> None:
    service = ChatService(Settings())
    state = service._default_state()
    state['active_filters'] = {'eligible_only': True, 'min_roi': 25}
    state['user_constraints'] = {'budget_per_unit': 20}

    service._apply_intent(
        {
            'topic_reset': False,
            'budget_per_unit': 15,
            'filters_to_set': {'min_roi': 30},
            'filters_to_clear': ['eligible_only'],
            'sort': 'amazon_pct_asc',
            'limit': 5,
        },
        state,
    )

    assert 'eligible_only' not in state['active_filters']
    assert state['active_filters']['min_roi'] == 30
    assert state['active_filters']['max_supplier_cost'] == 15
    assert state['user_constraints']['budget_per_unit'] == 15
    assert state['sort'] == 'amazon_pct_asc'
    assert state['limit'] == 5


def test_topic_reset_keeps_user_constraints() -> None:
    service = ChatService(Settings())
    state = service._default_state()
    state['active_filters'] = {'eligible_only': True}
    state['last_result_asins'] = ['B00HEON30Y']
    state['last_resolved_asin'] = 'B00HEON30Y'
    state['user_constraints'] = {'budget_per_unit': 18}

    service._apply_intent(
        {
            'topic_reset': True,
            'budget_per_unit': None,
            'filters_to_set': {},
            'filters_to_clear': [],
            'sort': None,
            'limit': None,
        },
        state,
    )

    assert state['active_filters']['max_supplier_cost'] == 18
    assert state['last_result_asins'] == []
    assert state['last_resolved_asin'] is None
    assert state['user_constraints']['budget_per_unit'] == 18
