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
    # options.add_argument('--headless=new')  # New headless mode
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-infobars')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-browser-side-navigation')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--log-level=3')
    options.add_argument('--disable-logging')
    options.add_argument('--disable-images')
    options.add_argument('--disable-web-security')
    options.add_argument('--allow-running-insecure-content')
    options.add_argument('--disable-features=IsolateOrigins,site-per-process')
    
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
        
        # Wait for initial table load
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
            current_page = 1
            while current_page < page:
                try:
                    # Wait for next button to be clickable
                    next_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, 'ul[data-v-26d3d030].pagination #next:not([disabled])'))
                    )
                    
                    # Scroll the button into view
                    driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                    
                    # Click using JavaScript
                    driver.execute_script("arguments[0].click();", next_button)
                    current_page += 1
                    print(f"Clicked to page {current_page}")
                    
                except Exception as e:
                    print(f"Navigation error: {str(e)}")
                    break
            # Wait for table content to update
            WebDriverWait(driver, 180).until(
                lambda d: d.execute_script("""
                    return document.querySelectorAll('table#dealsTable.mainTable tbody tr').length > 0;
                """)
            )
            time.sleep(1)

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
        else:
            current_page = 1
            page_rows_html = ""
            while current_page < 100:
                print(f"Navigating to page {current_page}...")
                try:
                    # Wait for table content to update
                    WebDriverWait(driver, 180).until(
                        lambda d: d.execute_script("""
                            return document.querySelectorAll('table#dealsTable.mainTable tbody tr').length > 0;
                        """)
                    )
                    
                    page_rows_html += driver.execute_script("""
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
                    
                    # Wait for next button to be clickable
                    next_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, 'ul[data-v-26d3d030].pagination #next:not([disabled])'))
                    )
                    
                    # Scroll the button into view
                    driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                    
                    # Click using JavaScript
                    driver.execute_script("arguments[0].click();", next_button)
                    current_page += 1
                    print(f"Clicked to page {current_page}")
                    
                except Exception as e:
                    print(f"Navigation error: {str(e)}")
                    break 
        

        driver.quit()
        
        # Construct final table HTML
        final_table_html = f'<table>{header_html}{page_rows_html}</table>'
        
        return {
            'success': True,
            'table_html': final_table_html,
            'page': page if page is not None else 0,
            'total_pages': 100
        }
        
    except Exception as e:
        if 'driver' in locals():
            driver.quit()
        return {
            'success': False,
            'error': str(e)
        } 