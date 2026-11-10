import sys
from playwright.sync_api import sync_playwright

# Browsers to try, in order:
#   1. Playwright's own Chromium (python -m playwright install chromium)
#   2. Google Chrome installed on this computer
#   3. Microsoft Edge installed on this computer
# so the tool still works when the Chromium download is blocked/slow.
BROWSER_CHOICES = [None, "chrome", "msedge"]


def launch_browser(p):

    errors = []

    for channel in BROWSER_CHOICES:

        try:

            if channel is None:
                browser = p.chromium.launch(headless=False)
            else:
                browser = p.chromium.launch(
                    headless=False,
                    channel=channel
                )

            print("Browser:", channel or "playwright chromium")

            return browser

        except Exception as e:

            errors.append(
                f"{channel or 'chromium'}: "
                f"{str(e).splitlines()[0][:150]}"
            )

    raise RuntimeError(
        "No browser could be started. Install Google Chrome, or run "
        "'python -m playwright install chromium'. Tried -> "
        + " | ".join(errors)
    )


def run_scraper(url, scraper, product):

    with sync_playwright() as p:

        browser = launch_browser(p)

        page = browser.new_page()

        print("Opening:", url)

        page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=60000
        )

        print("Page loaded.")

        result = scraper.get_products(
            page,
            product
        )

        print("Results:", result)

        browser.close()

        return result


if __name__ == "__main__":

    print(
        "browser_runner.py is designed "
        "to be called by a separate process."
    )
