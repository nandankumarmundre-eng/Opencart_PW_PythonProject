from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from email.utils import parsedate_to_datetime
import json
import math
import re
from urllib.error import URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen
from xml.etree import ElementTree


TOPIC_QUERIES = {
    "technical analysis": (
        "technical analysis OR support resistance OR breakout OR trend outlook"
    ),
    "fundamental analysis": (
        "fundamental outlook OR supply demand OR economic outlook OR market drivers"
    ),
    "experts and forecasts": (
        "analyst forecast OR expert prediction OR price target OR market outlook"
    ),
}

UPCOMING_QUERIES = {
    "scheduled events": (
        "upcoming scheduled event OR economic calendar OR policy decision "
        "OR inventory report OR data release"
    ),
    "published expectations": (
        "forecast OR analyst outlook OR expected decision OR market expectations "
        "OR price target"
    ),
}

NEWS_LOCALES = (
    ("en-US", "US", "US:en"),
    ("en-IN", "IN", "IN:en"),
    ("en-GB", "GB", "GB:en"),
    ("en-AU", "AU", "AU:en"),
)
MARKET_TIMEZONE = timezone(timedelta(hours=5, minutes=30), "IST")

SYMBOL_SEARCH_TERMS = {
    "NSE:NIFTY": "NIFTY 50 India index",
    "BTCUSD": "Bitcoin BTC USD spot price",
    "MCX:NATURALGASM2026": "natural gas futures Henry Hub prices MCX India",
    "MCX:CRUDEOILX2026": "crude oil futures Brent WTI prices MCX India",
}

PRIMARY_SOURCE_QUERIES = {
    "NSE:NIFTY": "site:nseindia.com OR site:rbi.org.in OR site:mospi.gov.in",
    "MCX:NATURALGASM2026": (
        "site:mcxindia.com OR site:eia.gov OR site:cmegroup.com OR site:opec.org"
    ),
    "MCX:CRUDEOILX2026": (
        "site:mcxindia.com OR site:eia.gov OR site:cmegroup.com OR site:opec.org"
    ),
}

MARKET_CLOSES = {
    "NSE:": time(15, 30),
    "MCX:": time(23, 30),
}

BULLISH_TERMS = {
    "accumulate",
    "beat",
    "bullish",
    "buy",
    "breakout",
    "gain",
    "growth",
    "higher",
    "increase",
    "outperform",
    "positive",
    " rally ",
    "raised",
    "record high",
    "recovery",
    "rise",
    "rises",
    "surge",
    "upgrade",
    "upside",
}

BEARISH_TERMS = {
    "bearish",
    "below",
    "contraction",
    "cut",
    "decline",
    "decrease",
    "downgrade",
    "fall",
    "falls",
    "lower",
    "loss",
    "negative",
    "oversupply",
    "sell",
    "slump",
    "weak",
    "downside",
}


@dataclass(frozen=True)
class NewsArticle:
    title: str
    source: str
    url: str
    published: datetime | None
    topic: str
    window: str = "current session"
    evidence_type: str = "News report"
    analyst_or_entity: str = "Not identified in headline"
    forecast_horizon: str = "Not specified"


@dataclass(frozen=True)
class MarketPriceSnapshot:
    price: float
    change_pct_24h: float
    source: str
    as_of: datetime


@dataclass
class SymbolAnalysis:
    symbol: str
    analysis_date: date
    action: str
    confidence_pct: int
    explanation: str
    articles: list[NewsArticle]
    window_summaries: dict[str, str]
    errors: list[str]
    price_snapshot: MarketPriceSnapshot | None = None


class MarketNewsAnalyzer:
    def __init__(
        self,
        max_workers: int = 12,
        analysis_date: date | None = None,
        now: datetime | None = None,
    ):
        self.now = now or datetime.now(MARKET_TIMEZONE)
        self.analysis_date = analysis_date or self.now.astimezone(MARKET_TIMEZONE).date()
        self.max_workers = max_workers

    @staticmethod
    def _search_term(symbol: str) -> str:
        if MarketNewsAnalyzer._is_btcusd(symbol):
            return SYMBOL_SEARCH_TERMS["BTCUSD"]
        return SYMBOL_SEARCH_TERMS.get(symbol, symbol.replace(":", " "))

    @staticmethod
    def _is_btcusd(symbol: str) -> bool:
        return symbol.upper() in {"BTCUSD", "BTC-USD", "DELTAIN:BTCUSD.P"}

    @classmethod
    def _is_relevant_title(
        cls,
        symbol: str,
        title: str,
        source: str = "",
    ) -> bool:
        if not cls._is_btcusd(symbol):
            return True
        source_suffix = f" - {source}"
        if source and title.casefold().endswith(source_suffix.casefold()):
            title = title[: -len(source_suffix)]
        return re.search(
            r"\b(?:bitcoin|btc[\s/-]*usd|btc)\b",
            title,
            re.IGNORECASE,
        ) is not None

    def _session_start(self, symbol: str) -> datetime:
        if self._is_btcusd(symbol):
            return self.now.astimezone(timezone.utc) - timedelta(hours=24)

        market_close = next(
            (close for prefix, close in MARKET_CLOSES.items() if symbol.startswith(prefix)),
            time(15, 30),
        )
        now_local = self.now.astimezone(MARKET_TIMEZONE)
        candidate = datetime.combine(
            now_local.date(),
            market_close,
            tzinfo=MARKET_TIMEZONE,
        )
        if candidate > now_local:
            candidate -= timedelta(days=1)
        while candidate.weekday() >= 5:
            candidate -= timedelta(days=1)
        return candidate

    def _window_bounds(self, symbol: str, window: str) -> tuple[datetime, datetime]:
        session_start = self._session_start(symbol)
        if window == "current session":
            return session_start, self.now
        if window == "past context":
            return session_start - timedelta(days=14), session_start
        if window == "upcoming":
            return self.now - timedelta(days=3), self.now
        raise ValueError(f"Unsupported news window: {window}")

    def _build_search_query(self, symbol: str, topic_query: str, window: str) -> str:
        start, end = self._window_bounds(symbol, window)
        if self._is_btcusd(symbol):
            combined_query = topic_query
        else:
            source_query = PRIMARY_SOURCE_QUERIES.get(symbol, "")
            combined_query = (
                f"({topic_query}) OR ({source_query})"
                if source_query
                else topic_query
            )
        return (
            f'{self._search_term(symbol)} ({combined_query}) '
            f"after:{start.date().isoformat()} before:"
            f"{(end.date() + timedelta(days=1)).isoformat()}"
        )

    def _is_in_window(self, symbol: str, window: str, published: datetime | None) -> bool:
        if published is None:
            return False
        start, end = self._window_bounds(symbol, window)
        localized = published.astimezone(start.tzinfo or MARKET_TIMEZONE)
        return start <= localized <= end

    @staticmethod
    def _classify_evidence(topic: str, source: str) -> tuple[str, str]:
        normalized_source = source.lower()
        official_sources = (
            "nse",
            "national stock exchange",
            "mcx",
            "ministry",
            "reserve bank",
            "rbi",
            "eia",
            "cme",
            "opec",
            "federal reserve",
            "sec",
            "exchange",
        )
        if any(name in normalized_source for name in official_sources):
            return "Official/primary-source item (publisher label)", source
        if topic in {"experts and forecasts", "published expectations"}:
            return "Expert opinion/forecast (headline; verify article)", "Not identified in headline"
        if topic == "scheduled events":
            return "Calendar/event expectation (verify official schedule)", "Not identified in headline"
        return "News report (headline only)", "Not identified in headline"

    @staticmethod
    def _forecast_horizon(title: str) -> str:
        match = re.search(
            r"\b(today|tomorrow|this week|next week|this month|next month|"
            r"Q[1-4]\s*\d{4}|\d{4})\b",
            title,
            re.IGNORECASE,
        )
        return match.group(0) if match else "Not specified in headline"

    def _fetch_topic(
        self,
        symbol: str,
        topic: str,
        topic_query: str,
        language: str,
        region: str,
        edition: str,
        window: str,
    ) -> tuple[list[NewsArticle], str | None]:
        query = self._build_search_query(symbol, topic_query, window)
        params = urlencode(
            {
                "q": query,
                "hl": language,
                "gl": region,
                "ceid": edition,
            }
        )
        url = f"https://news.google.com/rss/search?{params}"
        request = Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; MarketNewsSummary/1.0)"},
        )
        try:
            with urlopen(request, timeout=15) as response:
                feed = ElementTree.fromstring(response.read())
        except (URLError, TimeoutError, ElementTree.ParseError) as error:
            return [], f"{topic} ({region} feed): {error}"

        articles = []
        for item in feed.findall(".//item")[:30]:
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            source_element = item.find("source")
            source = (
                (source_element.text or "").strip()
                if source_element is not None
                else urlparse(link).hostname or "Unknown source"
            )
            published_text = item.findtext("pubDate")
            published = self._parse_date(published_text)
            if (
                not title
                or not link
                or not self._is_relevant_title(symbol, title, source)
                or not self._is_in_window(symbol, window, published)
            ):
                continue
            evidence_type, analyst_or_entity = self._classify_evidence(topic, source)
            articles.append(
                NewsArticle(
                    title=title,
                    source=source,
                    url=link,
                    published=published,
                    topic=topic,
                    window=window,
                    evidence_type=evidence_type,
                    analyst_or_entity=analyst_or_entity,
                    forecast_horizon=self._forecast_horizon(title),
                )
            )
        return articles, None

    @staticmethod
    def _parse_date(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            parsed = parsedate_to_datetime(value)
        except (TypeError, ValueError, OverflowError):
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    @staticmethod
    def _article_polarity(title: str) -> int:
        normalized = f" {title.lower()} "
        bullish = sum(
            re.search(r"(?<!\w)" + re.escape(term.strip()) + r"(?!\w)", normalized) is not None
            for term in BULLISH_TERMS
        )
        bearish = sum(
            re.search(r"(?<!\w)" + re.escape(term.strip()) + r"(?!\w)", normalized) is not None
            for term in BEARISH_TERMS
        )
        return (bullish > bearish) - (bearish > bullish)

    def _summarize(
        self,
        symbol: str,
        articles: list[NewsArticle],
        errors: list[str],
        price_snapshot: MarketPriceSnapshot | None = None,
    ) -> SymbolAnalysis:
        window_priority = {
            "current session": 3,
            "past context": 2,
            "upcoming": 1,
        }
        deduplicated = {}
        for article in sorted(
            articles,
            key=lambda item: (
                window_priority.get(item.window, 0),
                item.published or datetime.min.replace(tzinfo=timezone.utc),
            ),
            reverse=True,
        ):
            parsed_url = urlparse(article.url)
            deduplication_key = (
                f"{parsed_url.netloc.lower()}{parsed_url.path.rstrip('/')}"
                or article.title.casefold()
            )
            deduplicated.setdefault((article.window, deduplication_key), article)
        unique_articles = sorted(
            deduplicated.values(),
            key=lambda item: item.published or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
        current_articles = [
            article for article in unique_articles if article.window == "current session"
        ]
        past_articles = [article for article in unique_articles if article.window == "past context"]
        upcoming_articles = [article for article in unique_articles if article.window == "upcoming"]
        polarities = [self._article_polarity(article.title) for article in current_articles]
        bullish = sum(polarity > 0 for polarity in polarities)
        bearish = sum(polarity < 0 for polarity in polarities)
        directional_count = bullish + bearish
        source_count = len({article.source.lower() for article in current_articles})

        if directional_count:
            agreement = max(bullish, bearish) / directional_count
        else:
            agreement = 0.0
        coverage = min(len(current_articles) / 10, source_count / 5, 1.0)
        confidence = min(70, round(agreement * coverage * 100))

        if len(current_articles) < 5 or source_count < 3:
            action = "SIDEWAYS"
            confidence = 0
            explanation = (
                f"Insufficient current-session news coverage for a directional consensus "
                f"({len(current_articles)} articles from {source_count} sources). "
                "SIDEWAYS here means inconclusive news, not measured price consolidation."
            )
        elif directional_count < 5 or agreement < 0.65:
            action = "SIDEWAYS"
            confidence = (
                min(70, round((1 - agreement) * coverage * 100))
                if directional_count >= 5
                else 0
            )
            explanation = (
                f"News sentiment is neutral or mixed "
                f"({bullish} bullish, {bearish} bearish headlines). "
                "SIDEWAYS means no clear news consensus; it is not a technical trend reading."
            )
        else:
            action = "BUY" if bullish > bearish else "SELL"
            confidence = min(70, round(agreement * coverage * 100))
            chosen, opposing = (bullish, bearish) if action == "BUY" else (bearish, bullish)
            explanation = (
                f"{chosen} directional headlines versus {opposing} opposing headlines "
                f"across {source_count} current-session sources. Past context and upcoming "
                "expectations are shown separately. This is a headline-sentiment signal "
                "only, not a calibrated probability or investment recommendation."
            )

        if self._is_btcusd(symbol):
            if price_snapshot is None:
                if action in {"BUY", "SELL"}:
                    action = "SIDEWAYS"
                explanation += (
                    " A current BTC-USD spot quote was unavailable, so no "
                    "price-confirmed directional signal is issued."
                )
            elif action in {"BUY", "SELL"}:
                price_is_confirming = (
                    action == "BUY" and price_snapshot.change_pct_24h > 0
                ) or (
                    action == "SELL" and price_snapshot.change_pct_24h < 0
                )
                if price_is_confirming:
                    explanation += (
                        f" The headline direction agrees with the BTC-USD 24-hour "
                        f"spot move ({price_snapshot.change_pct_24h:+.2f}%)."
                    )
                else:
                    action = "SIDEWAYS"
                    explanation += (
                        f" Headline direction conflicts with or is not confirmed by "
                        f"the BTC-USD 24-hour spot move "
                        f"({price_snapshot.change_pct_24h:+.2f}%); no directional "
                        "signal is issued."
                    )
            else:
                explanation += (
                    f" BTC-USD spot is {price_snapshot.change_pct_24h:+.2f}% over "
                    "24 hours; this price move is reported separately and does not "
                    "create a directional signal by itself."
                )

        window_summaries = {
            "past context": (
                f"{len(past_articles)} unique reports/opinions from the prior 14 calendar "
                "days (approximately 10 trading sessions); background only."
            ),
            "current session": (
                f"{len(current_articles)} unique items from {source_count} sources; "
                f"{bullish} bullish, {bearish} bearish headlines."
            ),
            "upcoming": (
                f"{len(upcoming_articles)} recent articles about scheduled events or "
                "published expectations. These are not confirmed future outcomes."
            ),
        }
        return SymbolAnalysis(
            symbol=symbol,
            analysis_date=self.analysis_date,
            action=action,
            confidence_pct=confidence,
            explanation=explanation,
            articles=unique_articles,
            window_summaries=window_summaries,
            errors=errors,
            price_snapshot=price_snapshot,
        )

    def _fetch_btcusd_snapshot(
        self,
    ) -> tuple[MarketPriceSnapshot | None, str | None]:
        request = Request(
            "https://api.exchange.coinbase.com/products/BTC-USD/stats",
            headers={"User-Agent": "Mozilla/5.0 (compatible; MarketNewsSummary/1.0)"},
        )
        try:
            with urlopen(request, timeout=10) as response:
                payload = json.loads(response.read())
        except (
            URLError,
            TimeoutError,
            UnicodeDecodeError,
            json.JSONDecodeError,
        ) as error:
            return None, f"BTCUSD spot quote (Coinbase): {error}"

        try:
            opening_price = float(payload["open"])
            current_price = float(payload["last"])
        except (KeyError, TypeError, ValueError) as error:
            return None, f"BTCUSD spot quote (Coinbase) has an invalid response: {error}"

        if (
            not math.isfinite(opening_price)
            or not math.isfinite(current_price)
            or opening_price <= 0
            or current_price <= 0
        ):
            return None, "BTCUSD spot quote (Coinbase) has non-positive or invalid prices"

        return (
            MarketPriceSnapshot(
                price=current_price,
                change_pct_24h=(current_price / opening_price - 1) * 100,
                source="Coinbase BTC-USD",
                as_of=datetime.now(timezone.utc),
            ),
            None,
        )

    def analyze(self, symbol: str) -> SymbolAnalysis:
        if not symbol.strip():
            raise ValueError("symbol must not be empty")

        articles = []
        errors = []
        topic_sets = [
            ("past context", {**TOPIC_QUERIES, "official data": "official data release OR exchange notice"}),
            ("current session", {**TOPIC_QUERIES, "official data": "official data release OR exchange notice"}),
            ("upcoming", {**UPCOMING_QUERIES, "official schedules": "official schedule OR release calendar OR inventory report"}),
        ]
        price_snapshot = None
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [
                executor.submit(
                    self._fetch_topic,
                    symbol,
                    topic,
                    query,
                    language,
                    region,
                    edition,
                    window,
                )
                for window, topics in topic_sets
                for topic, query in topics.items()
                for language, region, edition in NEWS_LOCALES
            ]
            price_future = (
                executor.submit(self._fetch_btcusd_snapshot)
                if self._is_btcusd(symbol)
                else None
            )
            for future in as_completed(futures):
                topic_articles, error = future.result()
                articles.extend(topic_articles)
                if error:
                    errors.append(error)

            if price_future is not None:
                price_snapshot, price_error = price_future.result()
                if price_error:
                    errors.append(price_error)

        return self._summarize(symbol, articles, errors, price_snapshot)
