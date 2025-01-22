from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import os

def setup_driver():
    options = webdriver.ChromeOptions()
    
    # Add performance-focused arguments
    options.add_argument('--headless=new')  # New headless mode
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-infobars')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-browser-side-navigation')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--log-level=3')
    options.add_argument('--disable-logging')
    options.add_argument('--disable-images')
    
    # Disable unnecessary features
    prefs = {
        'profile.default_content_setting_values': {
            'images': 2,
            'plugins': 2,
            'popups': 2,
            'geolocation': 2,
            'notifications': 2,
            'auto_select_certificate': 2,
            'fullscreen': 2,
            'mouselock': 2,
            'mixed_script': 2,
            'media_stream': 2,
            'media_stream_mic': 2,
            'media_stream_camera': 2,
            'protocol_handlers': 2,
            'ppapi_broker': 2,
            'automatic_downloads': 2,
            'midi_sysex': 2,
            'push_messaging': 2,
            'ssl_cert_decisions': 2,
            'metro_switch_to_desktop': 2,
            'protected_media_identifier': 2,
            'app_banner': 2,
            'site_engagement': 2,
            'durable_storage': 2
        }
    }
    options.add_experimental_option('prefs', prefs)
    
    service = Service(log_output=os.devnull)
    return webdriver.Chrome(options=options, service=service)

def scrape_nadlan_deals(url, page=None):
    try:
        driver = setup_driver()
        driver.get(url)
        
        print("Starting scrape...")
        
        # Wait for initial table load with increased timeout
        WebDriverWait(driver, 180).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'table'))
        )

        print("Table found...")

        header_html = WebDriverWait(driver, 180).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'table thead tr'))
        ).get_attribute('outerHTML')
        
        print(f"Header HTML: {header_html[:100]}...")
        
        # If specific page is requested, navigate to that page
        if page is not None and page > 0:
            print(f"Navigating to page {page}...")
            current_page = 0
            while current_page < page:
                try:
                    # Try different methods to find and click the next button
                    try:
                        # Method 1: Using JavaScript to find and click
                        has_next = driver.execute_script("""
                            const nextButton = document.querySelector('ul[data-v-26d3d030].pagination #next:not([disabled])');
                            if (nextButton) {
                                nextButton.scrollIntoView({ behavior: 'smooth', block: 'center' });
                                setTimeout(() => nextButton.click(), 100);
                                return true;
                            }
                            return false;
                        """)
                        
                        if not has_next:
                            print("No next button found")
                            break
                            
                    except Exception as js_error:
                        print(f"JavaScript click failed: {str(js_error)}")
                        # Method 2: Traditional Selenium approach
                        next_button = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, 'ul[data-v-26d3d030].pagination #next:not([disabled])'))
                        )
                        driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                        next_button.click()
                    
                    current_page += 1
                    print(f"Clicked to page {current_page}")
                    
                except Exception as e:
                    print(f"Navigation error: {str(e)}")
                    break

            # Wait for table content to update with retry mechanism
            retry_count = 0
            while retry_count < 3:
                try:
                    WebDriverWait(driver, 60).until(
                        lambda d: d.execute_script("""
                            return document.querySelectorAll('table#dealsTable.mainTable tbody tr').length > 0;
                        """)
                    )
                    break
                except Exception as wait_error:
                    print(f"Wait retry {retry_count + 1}: {str(wait_error)}")
                    retry_count += 1
            
            if retry_count == 3:
                raise Exception("Failed to verify page load after multiple retries")
        # Get the rows from the current page
        try:
            page_rows_html = driver.execute_script("""
                const rows = document.querySelectorAll('table#dealsTable.mainTable tbody tr');
                return Array.from(rows).map(row => {
                    const cells = row.querySelectorAll('td');
                    for (let i = 0; i < cells.length - 1; i++) {
                        if (cells[i].classList.contains('trend-summary')) {
                            cells[i].remove();
                        }
                    }
                    return row.outerHTML;
                }).join('');
            """)
            
            print(f"Rows HTML length: {len(page_rows_html)}")
            
            if not page_rows_html:
                raise Exception("No rows found on page")
                
        except Exception as e:
            print(f"Row extraction error: {str(e)}")
            raise e

        driver.quit()
        
        # Construct final table HTML
        final_table_html = f'<table>{header_html}{page_rows_html}</table>'
        
        return {
            'success': True,
            'table_html': final_table_html,
            'page': page if page is not None else 0
        }
        
    except Exception as e:
        if 'driver' in locals():
            driver.quit()
        return {
            'success': False,
            'error': str(e)
        } 