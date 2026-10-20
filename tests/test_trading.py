import allure
import pytest
from datetime import date, datetime, timezone
from unittest.mock import MagicMock, patch

from conftest import (
    MARKET_SUMMARY_LINES_KEY,
    pytest_sessionfinish,
    pytest_terminal_summary,
)
from config import Config
from pages.market_news_analyzer import MARKET_TIMEZONE, MarketNewsAnalyzer, NewsArticle
from utilities.email_report import send_email_report


def _article(index, title, source=None):
    return NewsArticle(
        title=title,
        source=source or f"Source {index}",
        url=f"https://example{index}.com/story",
        published=datetime.now(timezone.utc),
        topic="unit test",
    )


@pytest.mark.end_to_end
def test_analyze_market_news(request, market_symbol):
    analyzer = MarketNewsAnalyzer()
    result = analyzer.analyze(market_symbol)
    summary_line = (
        f"{result.symbol} : {result.action} : {result.confidence_pct}%"
    )
    request.config.stash.setdefault(MARKET_SUMMARY_LINES_KEY, []).append(summary_line)

    allure.attach(
        f"Symbol: {result.symbol}\n"
        f"Analysis date (IST): {result.analysis_date.isoformat()}\n"
        f"Action: {result.action}\n"
        f"News-consensus strength (not a probability): {result.confidence_pct}%\n"
        f"Assessment: {result.explanation}\n"
        f"Window summaries:\n"
        + "\n".join(
            f"- {window}: {summary}" for window, summary in result.window_summaries.items()
        )
        + "\nSource errors: "
        + f"{'; '.join(result.errors) if result.errors else 'None'}\n"
        + "Articles:\n"
        + "\n".join(
            f"- [{article.window} | {article.evidence_type} | {article.topic}] "
            f"{article.published.isoformat() if article.published else 'date unavailable'} "
            f"| {article.source} | {article.title} "
            f"| entity={article.analyst_or_entity} "
            f"| horizon={article.forecast_horizon}\n  {article.url}"
            for article in result.articles[:60]
        ),
        name=f"News assessment - {result.symbol}",
        attachment_type=allure.attachment_type.TEXT,
    )
    assert result.action in {"BUY", "SELL", "SIDEWAYS"}


@pytest.mark.end_to_end
def test_confident_headline_consensus_returns_buy():
    analyzer = MarketNewsAnalyzer()
    articles = [
        _article(index, "Analysts see bullish outlook and strong growth")
        for index in range(1, 7)
    ]

    result = analyzer._summarize("NSE:NIFTY", articles, [])

    assert result.action == "BUY"
    assert result.confidence_pct <= 70
    assert "headline-sentiment signal only" in result.explanation


@pytest.mark.end_to_end
def test_mixed_headlines_return_sideways():
    analyzer = MarketNewsAnalyzer()
    articles = [
        _article(
            index,
            "Analysts see bullish growth outlook"
            if index % 2
            else "Analysts warn of bearish decline",
        )
        for index in range(1, 7)
    ]

    result = analyzer._summarize("MCX:NATURALGASM2026", articles, [])

    assert result.action == "SIDEWAYS"
    assert result.confidence_pct < 50
    assert "not a technical trend reading" in result.explanation


@pytest.mark.end_to_end
def test_insufficient_coverage_returns_sideways_with_zero_confidence():
    analyzer = MarketNewsAnalyzer()

    result = analyzer._summarize(
        "MCX:CRUDEOILX2026",
        [_article(1, "Crude oil prices rise")],
        ["network unavailable"],
    )

    assert result.action == "SIDEWAYS"
    assert result.confidence_pct == 0
    assert result.errors == ["network unavailable"]


@pytest.mark.end_to_end
def test_headline_without_sentiment_word_is_neutral():
    analyzer = MarketNewsAnalyzer()

    assert analyzer._article_polarity("Analysts discuss surprise market update") == 0


@pytest.mark.end_to_end
def test_rss_queries_define_past_current_and_upcoming_windows():
    now = datetime(2026, 10, 20, 12, 0, tzinfo=MARKET_TIMEZONE)
    analyzer = MarketNewsAnalyzer(analysis_date=date(2026, 10, 20), now=now)
    past_query = analyzer._build_search_query(
        "NSE:NIFTY", "technical analysis OR breakout", "past context"
    )
    current_query = analyzer._build_search_query(
        "NSE:NIFTY", "technical analysis OR breakout", "current session"
    )
    upcoming_query = analyzer._build_search_query(
        "NSE:NIFTY", "upcoming scheduled event", "upcoming"
    )

    assert "after:2026-10-05 before:2026-10-20" in past_query
    assert "after:2026-10-19 before:2026-10-21" in current_query
    assert "after:2026-10-17 before:2026-10-21" in upcoming_query
    assert "site:nseindia.com" in current_query


@pytest.mark.end_to_end
def test_session_windows_are_market_local_and_timestamp_strict():
    now = datetime(2026, 10, 20, 16, 0, tzinfo=MARKET_TIMEZONE)
    analyzer = MarketNewsAnalyzer(analysis_date=date(2026, 10, 20), now=now)
    session_start, session_end = analyzer._window_bounds("NSE:NIFTY", "current session")
    before_session = datetime(2026, 10, 20, 9, 59, tzinfo=MARKET_TIMEZONE)
    during_session = datetime(2026, 10, 20, 10, 0, tzinfo=MARKET_TIMEZONE)

    assert session_start == datetime(2026, 10, 20, 15, 30, tzinfo=MARKET_TIMEZONE)
    assert session_end == now
    assert not analyzer._is_in_window("NSE:NIFTY", "current session", before_session)
    assert analyzer._is_in_window("NSE:NIFTY", "past context", before_session)
    assert analyzer._is_in_window("NSE:NIFTY", "upcoming", during_session)
    assert not analyzer._is_in_window("NSE:NIFTY", "current session", None)


@pytest.mark.end_to_end
def test_upcoming_forecasts_are_labeled_as_expectations():
    evidence_type, entity = MarketNewsAnalyzer._classify_evidence(
        "published expectations",
        "Market Journal",
    )

    assert evidence_type == "Expert opinion/forecast (headline; verify article)"
    assert entity == "Not identified in headline"
    assert MarketNewsAnalyzer._forecast_horizon("Analyst outlook for next week") == "next week"


@pytest.mark.end_to_end
def test_same_story_can_be_kept_in_distinct_time_windows():
    analyzer = MarketNewsAnalyzer()
    same_story = _article(1, "Analysts expect higher prices next week")
    upcoming_copy = NewsArticle(
        title=same_story.title,
        source=same_story.source,
        url=same_story.url,
        published=same_story.published,
        topic="published expectations",
        window="upcoming",
    )
    current_copies = [
        NewsArticle(
            title=_article(index, "Analysts see bullish outlook").title,
            source=f"Current source {index}",
            url=f"https://current{index}.example/story",
            published=same_story.published,
            topic="technical analysis",
        )
        for index in range(2, 7)
    ]

    result = analyzer._summarize(
        "NSE:NIFTY",
        [same_story, upcoming_copy, *current_copies],
        [],
    )

    assert sum(article.window == "current session" for article in result.articles) == 6
    assert sum(article.window == "upcoming" for article in result.articles) == 1
    assert result.action == "BUY"

@pytest.mark.skip(reason='it is in pilot project, later will be enabled')
@pytest.mark.end_to_end
def test_email_report_sends_only_summary_body():
    with patch("utilities.email_report.smtplib.SMTP") as smtp_factory:
        smtp = MagicMock()
        smtp_factory.return_value.__enter__.return_value = smtp

        send_email_report(
            host="smtp.example.com",
            port=587,
            username="sender@example.com",
            password="application-secret",
            recipient="recipient@example.com",
            subject="Daily market summary",
            body="NSE:NIFTY : BUY : 65%",
        )

    sent_message = smtp.send_message.call_args.args[0]
    assert sent_message["To"] == "recipient@example.com"
    assert sent_message.get_content().strip() == "NSE:NIFTY : BUY : 65%"
    smtp.starttls.assert_called_once()
    smtp.login.assert_called_once_with("sender@example.com", "application-secret")

@pytest.mark.skip(reason='it is in pilot project, later will be enabled')
@pytest.mark.end_to_end
def test_email_report_requires_smtp_secrets():
    with pytest.raises(ValueError, match="MARKET_SMTP_USERNAME and MARKET_SMTP_PASSWORD"):
        send_email_report(
            host="smtp.gmail.com",
            port=587,
            username="",
            password="",
            recipient="recipient@example.com",
            subject="Daily market summary",
            body="NSE:NIFTY : BUY : 65%",
        )

@pytest.mark.skip(reason='it is in pilot project, later will be enabled')
@pytest.mark.end_to_end
def test_sessionfinish_emails_only_aggregated_summary_lines(monkeypatch):
    from pathlib import Path
    from types import SimpleNamespace

    lines = [
        "NSE:NIFTY : BUY : 65%",
        "MCX:CRUDEOILX2026 : SIDEWAYS : 36%",
    ]
    fake_config = SimpleNamespace(
        stash={MARKET_SUMMARY_LINES_KEY: lines},
        rootpath=Path("market-project"),
    )
    session = SimpleNamespace(config=fake_config, exitstatus=pytest.ExitCode.OK)
    sent = {}

    def capture_email(**kwargs):
        sent.update(kwargs)

    monkeypatch.setattr("conftest.send_email_report", capture_email)
    monkeypatch.setattr(Config, "market_smtp_host", "smtp.example.com")
    monkeypatch.setattr(Config, "market_smtp_port", 587)
    monkeypatch.setattr(Config, "market_smtp_username", "sender@example.com")
    monkeypatch.setattr(Config, "market_smtp_password", "application-secret")
    monkeypatch.setattr(Config, "market_report_email", "recipient@example.com")

    pytest_sessionfinish(session, pytest.ExitCode.OK)

    assert sent["body"] == "\n".join(lines)
    assert sent["recipient"] == "recipient@example.com"


@pytest.mark.end_to_end
def test_terminal_summary_prints_all_market_lines():
    from types import SimpleNamespace

    lines = [
        "NSE:NIFTY : BUY : 65%",
        "DELTAIN:BTCUSD.P : SIDEWAYS : 0%",
    ]
    fake_config = SimpleNamespace(stash={MARKET_SUMMARY_LINES_KEY: lines})
    terminal = MagicMock()

    pytest_terminal_summary(terminal, fake_config)

    terminal.write_sep.assert_called_once_with("=", "Market summary")
    assert [call.args[0] for call in terminal.write_line.call_args_list] == lines
