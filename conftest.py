import pytest
import allure
from pathlib import Path
from smtplib import SMTPException
from config import Config
from playwright.sync_api import Dialog, Error as PlaywrightError, Page, sync_playwright
from utilities.email_report import send_email_report


MARKET_SUMMARY_LINES_KEY = pytest.StashKey[list[str]]()

# ========================================================================
# PYTEST + PLAYWRIGHT TEST CONFIGURATION FILE
# ========================================================================
# This file provides:
# 1. Command-line options (browser, base URL, video, screenshots, etc.)
# 2. Hooks to track test results
# 3. Fixtures for browser setup and teardown
# 4. Screenshot, video, and trace attachments to Allure reports
# ========================================================================


# ----------------------------------------------------------------------------
# STEP 1: ADD COMMAND LINE OPTIONS
# ----------------------------------------------------------------------------
def pytest_addoption(parser):
    """
    Adds command line options for test configuration.
    You can override these when running pytest or store defaults in pytest.ini.
    """
    parser.addoption("--browser", default="chromium", help="Browser: chromium, firefox, webkit")
    parser.addoption("--headed", action="store_true", default=False, help="Run in headed (visible) mode")
    parser.addoption("--headless", dest="headed", action="store_false", help="Run in headless mode")
    parser.addoption("--base-url", default=Config.practice_url, help="Base URL for tests")
    parser.addoption(
        "--market-symbols",
        default=Config.market_symbols,
        help="Comma-separated market symbols to analyze",
    )
    parser.addoption("--video", default="retain-on-failure", help="Record video: on, off, retain-on-failure")
    parser.addoption("--screenshot", default="only-on-failure", help="Take screenshot: on, off, only-on-failure")
    parser.addoption("--tracing", default="retain-on-failure", help="Tracing: on, off, retain-on-failure")


def pytest_generate_tests(metafunc):
    if "market_symbol" not in metafunc.fixturenames:
        return

    symbols = [
        symbol.strip()
        for symbol in metafunc.config.getoption("market_symbols").split(",")
        if symbol.strip()
    ]
    if not symbols:
        raise pytest.UsageError("Configure symbols with MARKET_SYMBOLS or --market-symbols.")
    metafunc.parametrize("market_symbol", symbols, ids=symbols)


def pytest_terminal_summary(terminalreporter, config):
    summary_lines = config.stash.get(MARKET_SUMMARY_LINES_KEY, [])
    if not summary_lines:
        return

    terminalreporter.write_sep("=", "Market summary")
    for line in summary_lines:
        terminalreporter.write_line(line)


def pytest_sessionfinish(session, exitstatus):
    summary_lines = session.config.stash.get(MARKET_SUMMARY_LINES_KEY, [])
    if not summary_lines:
        return

    try:
        send_email_report(
            host=Config.market_smtp_host,
            port=Config.market_smtp_port,
            username=Config.market_smtp_username,
            password=Config.market_smtp_password,
            recipient=Config.market_report_email,
            subject=f"Daily market analysis - {session.config.rootpath.name}",
            body="\n".join(summary_lines),
        )
    except (OSError, SMTPException, ValueError) as error:
        session.exitstatus = max(exitstatus, pytest.ExitCode.TESTS_FAILED)
        print(f"Market summary email failed: {error}", flush=True)
    else:
        print(
            f"Market summary email sent to {Config.market_report_email}.",
            flush=True,
        )


# ----------------------------------------------------------------------------
# STEP 2: GET CONFIGURATION VALUE (CMDLINE OR pytest.ini)
# ----------------------------------------------------------------------------
def get_config_value(config, option_name):
    """
    Helper to read configuration values.
    Tries to get from command line first, otherwise from pytest.ini.
    Supports both string and boolean options.
    """
    # Try command-line first
    cmd_value = config.getoption(option_name)
    if cmd_value is not None:
        return cmd_value

    # Fallback to pytest.ini
    if option_name == "headed":
        ini_value = config.getini(option_name)
        return ini_value.lower() == "true" if isinstance(ini_value, str) else ini_value
    else:
        return config.getini(option_name)


# ----------------------------------------------------------------------------
# STEP 3: HOOK TO TRACK TEST RESULTS (PASS/FAIL)
# ----------------------------------------------------------------------------
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Captures the test result (pass/fail/skip) after each test.
    This is used later to decide whether to take screenshots or save traces.
    """
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)


# ----------------------------------------------------------------------------
# STEP 4: FIXTURE 1 - BROWSER CONTEXT SETUP
# ----------------------------------------------------------------------------
@pytest.fixture(scope="function")
def browser_context(request):
    """
    Creates and manages the Playwright browser context.
    - Reads configuration (browser, headed mode, video settings)
    - Starts the Playwright browser
    - Enables video recording if configured
    - Cleans up automatically after each test
    """
    # Read configuration values
    browser_name = str(get_config_value(request.config, "browser"))
    headed_flag = get_config_value(request.config, "headed")
    video_option = get_config_value(request.config, "video")

    print(f"[OK] Starting browser: {browser_name}")
    print(f"[OK] Headless mode: {not headed_flag} (headed={headed_flag})")

    # Start Playwright
    playwright = sync_playwright().start()

    # Start Chromium maximized and let its viewport follow the window size.
    if browser_name.lower() == "chromium":
        browser = playwright.chromium.launch(
            headless=not headed_flag,
            args=["--start-maximized"] if headed_flag else [],
        )
    elif browser_name.lower() == "firefox":
        browser = playwright.firefox.launch(headless=not headed_flag)
    elif browser_name.lower() == "webkit":
        browser = playwright.webkit.launch(headless=not headed_flag)
    else:
        raise ValueError(f"[FAIL] Unsupported browser: {browser_name}")

    # Create a browser context (optionally with video recording)
    if headed_flag and browser_name.lower() == "chromium":
        if video_option in ["on", "retain-on-failure"]:
            context = browser.new_context(
                no_viewport=True,
                record_video_dir="reports/videos",
            )
        else:
            context = browser.new_context(no_viewport=True)
    elif video_option in ["on", "retain-on-failure"]:
        context = browser.new_context(record_video_dir="reports/videos")
    else:
        context = browser.new_context()

    # Yield the context for use in tests
    yield context

    # Clean up after the test
    print("[CLEANUP] Closing browser context and stopping Playwright...")
    context.close()
    browser.close()
    playwright.stop()


# ----------------------------------------------------------------------------
# STEP 5: FIXTURE 2 - PAGE CREATION AND TEST ARTIFACT MANAGEMENT
# ----------------------------------------------------------------------------
@pytest.fixture(scope="function")
def page(request, browser_context):
    """
    Creates a new browser page for each test.
    - Navigates to the base URL
    - Starts tracing (if enabled)
    - Captures screenshots, traces, and videos for failed tests
    - Attaches all artifacts to Allure report
    """
    # Read test configuration
    base_url = get_config_value(request.config, "base_url")
    screenshot_option = get_config_value(request.config, "screenshot")
    tracing_option = get_config_value(request.config, "tracing")
    video_option = get_config_value(request.config, "video")

    print(f"[INFO] Navigating to: {base_url}")

    # Start tracing if enabled
    if tracing_option in ["on", "retain-on-failure"]:
        print("[TRACE] Tracing enabled - capturing screenshots and actions")
        browser_context.tracing.start(screenshots=True, snapshots=True, sources=True)

    # Create and navigate to base URL
    page = browser_context.new_page()

    def handle_dialog(dialog: Dialog):
        try:
            dialog.accept()
        except PlaywrightError as error:
            raise RuntimeError(
                f"Could not handle the browser's {dialog.type} dialog"
            ) from error

    def close_unexpected_page(popup: Page):
        popup_url = popup.url
        try:
            popup.on("dialog", handle_dialog)
            popup.close()
            print(f"[POPUP] Closed unexpected page: {popup_url}")
        except PlaywrightError as error:
            raise RuntimeError(
                f"Could not close unexpected popup: {popup_url}"
            ) from error

    page.on("dialog", handle_dialog)
    browser_context.on("page", close_unexpected_page)

    try:
        page.goto(base_url)

        # Yield the page to the test
        yield page

        # --------------------------------------------------------------------
        # After the test: manage artifacts (screenshots, videos, traces)
        # --------------------------------------------------------------------
        test_name = request.node.name
        test_failed = hasattr(request.node, "rep_call") and request.node.rep_call.failed

        print(f"[RESULT] Test '{test_name}' result: {'[FAIL]' if test_failed else '[PASS]'}")

        # Save and attach trace
        if tracing_option in ["on", "retain-on-failure"]:
            trace_path = f"reports/traces/{test_name}_trace.zip"
            browser_context.tracing.stop(path=trace_path)
            print(f"[SAVE] Trace saved: {trace_path}")

            # Attach trace to Allure report if test failed
            # Currently ZIP file is not supported to attach in Allure reports
            # if test_failed:
            #     allure.attach.file(
            #         trace_path,
            #         name=f"{test_name}_trace",
            #         attachment_type=allure.attachment_type.ZIP
            #     )
            #     print("[ATTACH] Trace attached to Allure report")

        # Take screenshot if test failed
        if test_failed and screenshot_option in ["on", "only-on-failure"]:
            screenshot_path = f"reports/screenshots/{test_name}.png"
            page.screenshot(path=screenshot_path)
            print(f"[SAVE] Screenshot saved: {screenshot_path}")

            # Attach to Allure report
            allure.attach.file(
                screenshot_path,
                name=f"{test_name}_screenshot",
                attachment_type=allure.attachment_type.PNG
            )
            print("[ATTACH] Screenshot attached to Allure report")

        # Attach video if available and test failed
        if test_failed and video_option in ["on", "retain-on-failure"]:
            video_path = page.video.path() if page.video else None
            if video_path and Path(video_path).exists():
                allure.attach.file(
                    video_path,
                    name=f"{test_name}_video",
                    attachment_type=allure.attachment_type.WEBM
                )
                print("[ATTACH] Video attached to Allure report")
    finally:
        page.remove_listener("dialog", handle_dialog)
        browser_context.remove_listener("page", close_unexpected_page)
