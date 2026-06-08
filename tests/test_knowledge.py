from unittest.mock import MagicMock
from seed.knowledge import seed, wipe, TOP_ARTICLES, CHILD_ARTICLES


def _mock_client(existing=None):
    client = MagicMock()
    records = existing if existing is not None else []
    client.search_read.return_value = records
    client.create.return_value = 200
    return client


def test_seed_creates_all_when_none_exist():
    client = _mock_client([])
    seed(client)
    assert client.create.call_count == len(TOP_ARTICLES) + len(CHILD_ARTICLES)


def test_seed_skips_when_all_exist():
    all_articles = ([{'id': i, 'name': a['name']} for i, a in enumerate(TOP_ARTICLES, 1)] +
                    [{'id': i + len(TOP_ARTICLES), 'name': a['name']} for i, a in enumerate(CHILD_ARTICLES)])
    client = MagicMock()
    client.search_read.return_value = all_articles
    seed(client)
    client.create.assert_not_called()


def test_seed_creates_top_articles_before_children():
    client = _mock_client([])
    seed(client)
    top_count = len(TOP_ARTICLES)
    child_count = len(CHILD_ARTICLES)
    assert client.create.call_count == top_count + child_count
    # First N creates should be top-level (no parent_id)
    for i, c in enumerate(client.create.call_args_list[:top_count]):
        assert 'parent_id' not in c[0][1] or c[0][1].get('parent_id') is None


def test_wipe_unlinks_all():
    client = MagicMock()
    client.search_read.return_value = [{'id': 1}, {'id': 2}]
    wipe(client)
    client.unlink.assert_called_once_with('knowledge.article', [1, 2])


def test_wipe_does_nothing_when_empty():
    client = MagicMock()
    client.search_read.return_value = []
    wipe(client)
    client.unlink.assert_not_called()
