from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Optional: run in headless mode
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=options)
    return driver

def scrape_nadlan_deals(url):
    try:
        driver = setup_driver()
        # options = Options()
        # options.headless = True
        # service = Service('C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe')
        # driver = webdriver.Chrome(service=service, options=options)
        
        driver.get(url)
        WebDriverWait(driver, 180).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'table'))
        )
        # driver.implicitly_wait(30)

       
        header_html = driver.find_element(By.CSS_SELECTOR, 'table thead tr').get_attribute('outerHTML')
        print(header_html)
        print("header found")
        all_tables_html = ''
        has_next_page = True
        current_page = 0
        
        while has_next_page and current_page < 90:
              # Wait for the table to load
            WebDriverWait(driver, 180).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table#dealsTable.mainTable tbody tr"))
            )
        
            print(f"Scraping page {current_page}...")
            rows = driver.find_elements(By.CSS_SELECTOR, 'table tbody tr')
            print(rows)
            print("row found")

            # # Locate the table rows (excluding the header)
            # Parse the page source with Beautiful Soup
            # soup = BeautifulSoup(page_source, "html.parser")
            # rows = soup.select("table#dealsTable.mainTable tbody tr")
            # # Collect all rows' HTML
            # page_rows_html = "".join(str(row) for row in rows)

            page_rows_html = ''.join([row.get_attribute('outerHTML') for row in rows])
            all_tables_html += page_rows_html
            
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            next_button = soup.select_one('ul[data-v-26d3d030].pagination #next:not([disabled])')
            print("next button found")

            if next_button:
                # Locate the next button using Selenium
                selenium_next_button = driver.find_element(By.CSS_SELECTOR, 'ul[data-v-26d3d030].pagination #next:not([disabled])')
                selenium_next_button.click()
                print("next button clicked")
                time.sleep(1)
                current_page += 1
            else:
                has_next_page = False
        
        # stats = {
        #     'yield': driver.find_element(By.CSS_SELECTOR, '.yield').text.strip(),
        #     'priceChange': driver.find_element(By.CSS_SELECTOR, '.price-drop').text.strip(),
        #     'neighborhoodRating': driver.find_element(By.CSS_SELECTOR, '.neighborhood-value').text.strip()
        # }
        
        driver.quit()
        
        table_html = f'<table>{header_html}{all_tables_html}</table>'
        
        return {
            'success': True,
            # 'stats': stats,
            'table_html': table_html,
            'totalPages': current_page
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        } 