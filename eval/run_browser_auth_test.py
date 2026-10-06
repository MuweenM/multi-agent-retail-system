import asyncio
from playwright.async_api import async_playwright

async def run_test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        print("=== Navigating to Submit Return ===")
        await page.goto('http://localhost:5173')
        await page.wait_for_selector('input[type="email"]')
        await page.fill('input[type="email"]', 'admin@demo.com')
        await page.fill('input[type="password"]', 'password')
        await page.click('button[type="submit"]')
        
        await page.wait_for_selector('nav', timeout=5000)
        await page.click('button:has-text("Submit Return")')
        await page.wait_for_selector('textarea')
        
        complaint = "My Samsung Galaxy A15 smartphone battery dies fast, call 0771234567 for refund order ORD-9921"
        await page.fill('textarea', complaint)
        
        print("=== Submitting Single Return ===")
        await page.click('button:has-text("Analyse Return")')
        
        # Wait a bit for the API call to complete
        await page.wait_for_timeout(4000)
        
        page_text = await page.evaluate("document.body.innerText")
        print("Decision Card UI Text contains [PHONE]?", "[PHONE]" in page_text)
        print("Decision Card UI Text contains 0771234567?", "0771234567" in page_text)
        print("Page text snippet:", page_text[:500])
        
        await browser.close()

if __name__ == '__main__':
    asyncio.run(run_test())
