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

def scrape_nadlan_deals(url, stream=False):
    try:
        driver = setup_driver()
        driver.get(url)
        WebDriverWait(driver, 180).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'table'))
        )

        header_html = WebDriverWait(driver, 180).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'table thead tr'))
        ).get_attribute('outerHTML')
        
        all_tables_html = ''
        has_next_page = True
        current_page = 0
        
        while has_next_page and current_page < 90:
            print(f"Scraping page {current_page}...")
            # Wait for table rows to be present
            WebDriverWait(driver, 180).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "table#dealsTable.mainTable tbody tr"))
            )
            
            # Get rows with explicit wait
            rows = WebDriverWait(driver, 180).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'table tbody tr'))
            )
            
            # Collect row HTML with retry mechanism
            page_rows_html = ''
            for row in rows:
                try:
                    row_html = WebDriverWait(driver, 10).until(
                        lambda d: row.get_attribute('outerHTML')
                    )
                    page_rows_html += row_html
                    
                    if stream:
                        yield {
                            'type': 'row',
                            'html': row_html,
                            'page': current_page
                        }
                except:
                    continue
                    
            all_tables_html += page_rows_html
            
            if stream:
                yield {
                    'type': 'page_complete',
                    'page': current_page,
                    'total_pages': current_page + 1
                }
            
            try:
                next_button = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'ul[data-v-26d3d030].pagination #next:not([disabled])'))
                )
                next_button.click()
                time.sleep(2)
                current_page += 1
            except:
                has_next_page = False
        
        driver.quit()
        
        if not stream:
            table_html = f'<table>{header_html}{all_tables_html}</table>'
            return {
                'success': True,
                'table_html': table_html,
                'totalPages': current_page
            }
            
    except Exception as e:
        if 'driver' in locals():
            driver.quit()
        if stream:
            yield {
                'type': 'error',
                'error': str(e)
            }
        else:
            return {
                'success': False,
                'error': str(e)
            } 