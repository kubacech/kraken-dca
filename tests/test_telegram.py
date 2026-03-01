import pytest
from unittest.mock import MagicMock
from requests.exceptions import HTTPError, ConnectionError


class TestSendMessage:

    def test_sends_message_successfully(self, telegram_notifier, mock_requests_post):
        result = telegram_notifier.send_message("Hello!")
        assert result is True
        mock_requests_post.assert_called_once()
        call_kwargs = mock_requests_post.call_args
        assert call_kwargs[1]["data"]["text"] == "Hello!"
        assert call_kwargs[1]["data"]["chat_id"] == "fake-chat-id"
        assert call_kwargs[1]["data"]["parse_mode"] == "HTML"

    def test_uses_correct_url(self, telegram_notifier, mock_requests_post):
        telegram_notifier.send_message("test")
        url = mock_requests_post.call_args[0][0]
        assert url == "https://api.telegram.org/botfake-token/sendMessage"

    def test_custom_parse_mode(self, telegram_notifier, mock_requests_post):
        telegram_notifier.send_message("test", parse_mode="Markdown")
        assert mock_requests_post.call_args[1]["data"]["parse_mode"] == "Markdown"

    def test_returns_false_on_http_error(self, telegram_notifier, mock_requests_post):
        mock_requests_post.return_value.raise_for_status.side_effect = HTTPError("500")
        result = telegram_notifier.send_message("fail")
        assert result is False

    def test_returns_false_on_connection_error(self, telegram_notifier, mock_requests_post):
        mock_requests_post.side_effect = ConnectionError("timeout")
        result = telegram_notifier.send_message("fail")
        assert result is False
