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
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'table'))
        )

        print("Table found...")

        header_html = WebDriverWait(driver, 10).until(
            lambda d: d.execute_script(
                """
                // Get all sections with class "transactionsSection"
                const sections = Array.from(document.querySelectorAll('.transactionsSection'));
                // Filter out any section that is wrapped by a div with "display: none"
                const visibleSection = sections.find(sec => !sec.closest('div[style*="display: none"]'));
                if (!visibleSection) return null;
                const header = visibleSection.querySelector('table#dealsTable.mainTable thead tr');
                return header ? header.outerHTML : null;
                """
            )
        )

        # header_html = WebDriverWait(driver, 30).until(
        #     EC.presence_of_element_located((By.CSS_SELECTOR, 'table thead tr'))
        # ).get_attribute('outerHTML')
        
        print(f"Header HTML: {header_html[:100]}...")

        # Example snippet to extract total pages from the visible pagination element
        # total_pages = WebDriverWait(driver, 10).until(
        #     lambda d: d.execute_script(
        #         """
        #         // Get all pagination elements with class "paginate"
        #         const sections = Array.from(document.querySelectorAll('.transactionsSection'));
        #         const visibleSection = sections.find(sec => !sec.closest('div[style*="display: none"]'));
        #         if (!visibleSection) return "";
        #         const table = visibleSection.querySelector('table#dealsTable.mainTable');
        #         if (!table) return 0;
        #         const paginations = table.querySelectorAll('.paginate');
        #         const paginate = paginations[0]
               
        #         // Assume the text is of the form "1 / 5537"
        #         const text = paginate.textContent || "";
        #         const parts = text.split('/');
        #         if (parts.length < 2) return null;
        #         // Parse the total pages (e.g. "5537")
        #         const total = parseInt(parts[1].trim(), 10);
        #         return total;
        #         """
        #     )
        # )

        # if total_pages is None:
        #     print("Could not find the total pages.")
        # else:
        #     print("Total pages:", total_pages)


        # Define a JS snippet to extract rows from the visible transaction section.
        extract_rows_script = """
            const sections = Array.from(document.querySelectorAll('.transactionsSection'));
            const visibleSection = sections.find(sec => !sec.closest('div[style*="display: none"]'));
            if (!visibleSection) return "";
            const table = visibleSection.querySelector('table#dealsTable.mainTable');
            if (!table) return "";
            const rows = table.querySelectorAll('tbody tr');
            return Array.from(rows).map(row => {
                const cells = row.querySelectorAll('td');
                // Remove any cell with class 'trend-summary' except the last one
                for (let i = 0; i < cells.length - 1; i++) {
                    if (cells[i].classList.contains('trend-summary')) {
                        cells[i].remove();
                    }
                }
                return row.outerHTML;
            }).join('');
        """

         # A helper function to get the "next" button within the visible transaction section.
        def get_next_button(driver):
            return driver.execute_script(
                """
                const sections = Array.from(document.querySelectorAll('.transactionsection'));
                const visibleSection = sections.find(sec => !sec.closest('div[style*="display: none"]'));
                if (!visibleSection) return null;
                return visibleSection.querySelector('ul[data-v-26d3d030].pagination #next:not([disabled])');
                """
            )
        
        # If specific page is requested, navigate to that page
        if page is not None and page > 0:
            print(f"Navigating to page {page}...")
            current_page = 1
            while current_page < page:
                print("Navigating to next page...")
                try:
                    # Wait for next button to be clickable
                    # next_button = WebDriverWait(driver, 5).until(lambda d: get_next_button(d))
                    next_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, 'ul[data-v-26d3d030].pagination #next:not([disabled])'))
                    )
                    print("Next button found...")
                    print(next_button)
                    
                    # Scroll the button into view
                    driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                    
                    # Click using JavaScript
                    driver.execute_script("arguments[0].click();", next_button)
                    current_page += 1
                    print(f"Clicked to page {current_page}")
                    
                except Exception as e:
                    print(f"Navigation error: {str(e)}")
                    # break
                    return {
                        'success': False,
                        'error': "No page found"
                    } 

            # Wait until rows are present in the visible table
            try:
                print("checks")
                WebDriverWait(driver, 5).until(
                    lambda d: d.execute_script(
                        """
                        const sections = Array.from(document.querySelectorAll('.transactionsSection'));
                        const visibleSection = sections.find(sec => !sec.closest('div[style*="display: none"]'));
                        if (!visibleSection) return false;
                        const table = visibleSection.querySelectorAll('table#dealsTable.mainTable tbody tr').length > 0;
                        return table;
                        """
                    )
                )
                # # Wait for table content to update
                # WebDriverWait(driver, 30).until(
                #     lambda d: d.execute_script("""
                #         return document.querySelectorAll('table#dealsTable.mainTable tbody tr').length > 0;
                #     """)
                # )
                time.sleep(1)
            except Exception as wait_error:
                page_source_snippet = driver.page_source[:1000]
                print("Error waiting for rows. Page source snippet:")
                print(page_source_snippet)
                return {
                    'success': False,
                    'error': "No row found"
                } 
                # raise wait_error
            
            # Get the rows from the current page
            try:
                # page_rows_html = driver.execute_script("""
                #     const rows = document.querySelectorAll('table#dealsTable.mainTable tbody tr');
                #     return Array.from(rows).map(row => {
                #         const cells = row.querySelectorAll('td');
                #         for (let i = 0; i < cells.length - 1; i++) {
                #             if (cells[i].classList.contains('trend-summary')) {
                #                 cells[i].remove();
                #             }
                #         }
                #         return row.outerHTML;
                #     }).join('');
                # """)
                page_rows_html = driver.execute_script(extract_rows_script)
                
                print(f"Rows HTML length: {len(page_rows_html)}")
                
                if not page_rows_html:
                    return {
                        'success': False,
                        'error': "No row found"
                    }    
                    # raise Exception("No rows found on page")
                    
            except Exception as e:
                print(f"Row extraction error: {str(e)}")
                return {
                    'success': False,
                    'error': "No row found"
                } 
                # raise e
        else:
            current_page = 1
            page_rows_html = ""
            while current_page < 100:
                print(f"Navigating to page {current_page}...")
                try:
                    # Wait for table content to update
                    # WebDriverWait(driver, 30).until(
                    #     lambda d: d.execute_script("""
                    #         return document.querySelectorAll('table#dealsTable.mainTable tbody tr').length > 0;
                    #     """)
                    # )
                    
                     # Wait until rows are present in the visible table
                    WebDriverWait(driver, 5).until(
                        lambda d: d.execute_script(
                            """
                            const sections = Array.from(document.querySelectorAll('.transactionsSection'));
                            const visibleSection = sections.find(sec => !sec.closest('div[style*="display: none"]'));
                            if (!visibleSection) return false;
                            const table = visibleSection.querySelector('table#dealsTable.mainTable');
                            return table && table.querySelectorAll('tbody tr').length > 0;
                            """
                        )
                    )
                    # page_rows_html += driver.execute_script("""
                    #     const rows = document.querySelectorAll('table#dealsTable.mainTable tbody tr');
                    #     return Array.from(rows).map(row => {
                    #         const cells = row.querySelectorAll('td');
                    #         for (let i = 0; i < cells.length - 1; i++) {
                    #             if (cells[i].classList.contains('trend-summary')) {
                    #                 cells[i].remove();
                    #             }
                    #         }
                    #         return row.outerHTML;
                    #     }).join('');
                    # """)
                    # Append the current page rows from the visible table
                    page_rows_html += driver.execute_script(extract_rows_script)
                    
                    # Wait for next button to be clickable
                    next_button = WebDriverWait(driver, 5).until(lambda d: get_next_button(d))
                    # next_button = WebDriverWait(driver, 10).until(
                    #     EC.element_to_be_clickable((By.CSS_SELECTOR, 'ul[data-v-26d3d030].pagination #next:not([disabled])'))
                    # )
                    
                    # Scroll the button into view
                    driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                    
                    # Click using JavaScript
                    driver.execute_script("arguments[0].click();", next_button)
                    current_page += 1
                    print(f"Clicked to page {current_page}")
                    
                except Exception as e:
                    print(f"Navigation error: {str(e)}")
                    return {
                        'success': False,
                        'error': "No row found"
                    } 
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