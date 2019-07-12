import imp

import mock


class TestActions:
    def test_add_key(self, sh, monkeypatch):
        mock_function = mock.Mock()
        monkeypatch.setattr(sh, "add_key", mock_function)
        assert mock_function.call_count == 0
        imp.load_source("add_key", "./actions/add-key")
        assert mock_function.call_count == 1

    def test_set_key(self, sh, monkeypatch):
        mock_function = mock.Mock()
        monkeypatch.setattr(sh, "set_key", mock_function)
        assert mock_function.call_count == 0
        imp.load_source("set_key", "./actions/set-key")
        assert mock_function.call_count == 1

    def test_set_password(self, sh, monkeypatch):
        mock_function = mock.Mock()
        monkeypatch.setattr(sh, "set_password", mock_function)
        assert mock_function.call_count == 0
        imp.load_source("set_password", "./actions/set-password")
        assert mock_function.call_count == 1
