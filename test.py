from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time


def scrape_nadlan_deals(url):
    try:
        # Initialize the Selenium WebDriver
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # Optional: run in headless mode
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

        driver = webdriver.Chrome(options=options)
        driver.get(url)

        print("Browser launched")

        # Wait for the table to load
        WebDriverWait(driver, 180).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table#dealsTable.mainTable tbody tr"))
        )

        has_next_page = True
        current_page = 0
        all_tables_html = ""

        # # Get the header row HTML once
        # header_html = driver.execute_script(
        #     """
        #     const headerRow = document.querySelector('table tbody tr');
        #     return headerRow.outerHTML;
        #     """
        # )
        # print(header_html)


        # After the page is loaded with Selenium
        page_source = driver.page_source

        # Parse the page source with Beautiful Soup
        soup = BeautifulSoup(page_source, "html.parser")

        # Locate the table rows (excluding the header)
        rows = soup.select("table#dealsTable.mainTable tbody tr")
        # Collect all rows' HTML
        page_rows_html = "".join(str(row) for row in rows)

        header_row = soup.select("table#dealsTable.mainTable thead tr")
        header_row_html = "".join(str(row) for row in header_row)

        print("header row html")
        print(header_row_html)
        print("page rows html")
        print(page_rows_html)


        while has_next_page and current_page < 90:
            print(f"Scraping page {current_page}...")

            # Get the rows from the current page
            page_rows_html = driver.execute_script(
                """
                const rows = document.querySelectorAll('table tbody tr');
                return Array.from(rows).map(row => {
                    const cells = row.querySelectorAll('td');
                    for (let i = 0; i < cells.length - 1; i++) {
                        if (cells[i].classList.contains('trend-summary')) {
                            cells[i].remove();
                        }
                    }
                    return row.outerHTML;
                }).join('');
                """
            )

            print(page_rows_html)
            print("page rows html")

            # Add rows to the collection
            all_tables_html += page_rows_html
            print("all tables html")

            # Check for the next page button and click if it exists
            has_next_page = driver.execute_script(
                """
                const nextButton = document.querySelector('ul[data-v-26d3d030].pagination #next:not([disabled])');
                if (nextButton) {
                    nextButton.click();
                    return true;
                }
                return false;
                """
            )
            print(has_next_page)
            print("has next page")
            if has_next_page:
                # Wait for the table to update with new data
                WebDriverWait(driver, 180).until(
                    lambda d: len(d.find_elements(By.CSS_SELECTOR, 'table tr:not(:first-child)')) > 0
                )
                current_page += 1
                time.sleep(1)  # Add a small delay to ensure content is fully loaded

        # Get neighborhood stats
        stats = driver.execute_script(
            """
            return {
                yield: document.querySelector('.yield')?.textContent.trim(),
                priceChange: document.querySelector('.price-drop')?.textContent.trim(),
                neighborhoodRating: document.querySelector('.neighborhood-value')?.textContent.trim()
            };
            """
        )
        print("stats")

        driver.quit()

        # Construct the complete table HTML
        table_html = f"<table>{header_html}{all_tables_html}</table>"

        return {
            "success": True,
            "stats": stats,
            "tableHtml": table_html,
            "totalPages": current_page
        }

    except Exception as e:
        print("Scraping error:", e)
        return {
            "success": False,
            "error": str(e)
        }

# Example usage
if __name__ == "__main__":
    url = "https://www.nadlan.gov.il/?view=neighborhood&id=65210148&page=deals"
    result = scrape_nadlan_deals(url)
    print(result)