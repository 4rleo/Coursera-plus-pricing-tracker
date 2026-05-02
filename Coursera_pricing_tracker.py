import json
import os
from playwright.sync_api import sync_playwright

COURSERA_COOKIES = os.getenv("COURSERA_COOKIES")


def normalize_cookies(cookies_list):
    result = []
    for c in cookies_list:
        clean = {
            "name": c["name"],
            "value": c["value"],
            "domain": c.get("domain", ".coursera.org"),
            "path": c.get("path", "/"),
            "secure": c.get("secure", True),
        }
        same_site = str(c.get("sameSite", "Lax")).lower()
        clean["sameSite"] = "None" if same_site in ["no_restriction", "unspecified"] else same_site.capitalize()
        if "expirationDate" in c:
            clean["expires"] = float(c["expirationDate"])
        result.append(clean)
    return result


def main():
    raw_cookies = json.loads(COURSERA_COOKIES)
    clean_cookies = normalize_cookies(raw_cookies)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            locale="es-MX",
            extra_http_headers={"Accept-Language": "es-MX,es;q=0.9"}
        )
        context.add_cookies(clean_cookies)
        page = context.new_page()

        def handle_response(response):
            url = response.url
            if "coursera.org/api" in url or "stripe.com" in url:
                try:
                    body = response.json()
                    print(f"\n--- URL: {url}")
                    print(json.dumps(body, indent=2))
                except:
                    pass

        page.on("response", handle_response)
        page.goto("https://www.coursera.org/courseraplus")

        try:
            page.click("button.css-j90x6z", timeout=10000)
        except:
            print("Botón no encontrado")

        page.wait_for_timeout(5000)
        browser.close()


if __name__ == "__main__":
    main()
