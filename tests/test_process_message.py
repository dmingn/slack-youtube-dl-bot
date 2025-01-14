import pytest

from slack_youtube_dl_bot.process_message import extract_url_from_message_text


@pytest.mark.parametrize(
    "text, expected",
    [
        ("<https://example.com/path?query=1>", "https://example.com/path?query=1"),
        (
            "This message contains a URL <https://example.com/path?query=1>",
            "https://example.com/path?query=1",
        ),
        (
            "This message contains URLs <https://example.com/path?query=1> <https://example.com/path?query=2>",
            "https://example.com/path?query=1",
        ),
        (
            "<https://example.com/path?query=1|This message *is* a link>",
            "https://example.com/path?query=1",
        ),
    ],
)
def test_extract_url_from_message_text(text: str, expected: str):
    assert extract_url_from_message_text(text) == expected
