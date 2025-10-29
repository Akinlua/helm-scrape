from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import os
import traceback
import base64
from urllib.parse import urlparse

# try:
from seleniumwire import webdriver as wire_webdriver
SELENIUM_WIRE_AVAILABLE = True
# except ImportError:
#     SELENIUM_WIRE_AVAILABLE = False

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
    options.add_argument('--disable-quic')

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

    # Proxy config (Selenium Wire preferred)
    proxy_url = 'http://brd-customer-hl_67f2d9ee-zone-residential_proxy1-country-il:vrqfz1kw74ec@brd.superproxy.io:33335'
    parsed = urlparse(proxy_url)

    if SELENIUM_WIRE_AVAILABLE:
        print("Using Selenium Wire for proxy")
        seleniumwire_options = {
            'proxy': {
                'http': proxy_url,
                'https': proxy_url,
                'no_proxy': 'localhost,127.0.0.1'
            }
        }
        return wire_webdriver.Chrome(options=options, seleniumwire_options=seleniumwire_options, service=service)
    else:
        # If proxy requires auth, Chrome's --proxy-server with credentials can cause ERR_NO_SUPPORTED_PROXIES.
        if parsed.username or parsed.password:
            raise RuntimeError(
                "Authenticated proxies require Selenium Wire. Install via 'pip install selenium-wire' or add it to requirements.txt."
            )
        # Unauthenticated proxy fallback
        options.add_argument(f'--proxy-server={proxy_url}')
        print("Using Chrome --proxy-server fallback (no auth)")
        return webdriver.Chrome(options=options, service=service)

def scrape_nadlan_deals(url, page=None):
    try:
        driver = setup_driver()
        driver.get(url)
        
        print("Starting scrape...")
        time.sleep(1000)
        
        # Wait for initial table load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'table'))
        )

        print("Table found...")

        print(driver.page_source)

        print("now header")
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

        # Take a screenshot of the current page for debugging
        screenshot_path = "test1html.png"
        if save_full_page_screenshot(driver, screenshot_path):
            print(f"Screenshot saved to {screenshot_path}")
        else:
            print(f"Screenshot saved (viewport only) to {screenshot_path}")


        # time.sleep(15)

        # Ensure table rows are present before reading pagination
        # WebDriverWait(driver, 15).until(
        #     lambda d: d.execute_script(
        #         """
        #         const sections = Array.from(document.querySelectorAll('.transactionsSection'));
        #         const visibleSection = sections.find(sec => getComputedStyle(sec).display !== 'none');
        #         if (!visibleSection) return false;
        #         const table = visibleSection.querySelector('table#dealsTable.mainTable');
        #         return table && table.querySelectorAll('tbody tr').length > 0;
        #         """
        #     )
        # )

        # test_html = WebDriverWait(driver, 10).until(
        #     lambda d: d.execute_script(
        #         """
        #         // Get all sections with class "transactionsSection"
        #         const sections = Array.from(document.querySelectorAll('.transactionsSection'));
        #         // Filter out any section that is wrapped by a div with "display: none"
        #         const visibleSection = sections.find(sec => !sec.closest('div[style*="display: none"]'));
        #         if (!visibleSection) return null;
        #         const header = visibleSection.querySelector('.paginate');
        #         return header ? header.outerHTML : null;
        #         """
        #     )
        # )

        # print(f"Test HTML: {test_html}...")


        # test2_html = WebDriverWait(driver, 10).until(
        #     lambda d: d.execute_script(
        #         """
        #         // Get all sections with class "transactionsSection"
        #         const sections = Array.from(document.querySelectorAll('.transactionsSection'));
        #         // Filter out any section that is wrapped by a div with "display: none"
        #         const visibleSection = sections.find(sec => !sec.closest('div[style*="display: none"]'));
        #         if (!visibleSection) return null;
        #         const header = visibleSection.querySelector('.paginate');
        #         const text = header.textContent || "";
        #         return text;
        #         """
        #     )
        # )

        # print(f"Test2 HTML: {test2_html}...")

        # Take a screenshot of the current page for debugging
        # screenshot_path = "test2html.png"
        # if save_full_page_screenshot(driver, screenshot_path):
        #     print(f"Screenshot saved to {screenshot_path}")
        # else:
        #     print(f"Screenshot saved (viewport only) to {screenshot_path}")

        total_pages = 0
        try:
            total_pages = WebDriverWait(driver, 10).until(
                lambda d: d.execute_script(
                    """
                    // Get all sections with class "transactionsSection"
                    const sections = Array.from(document.querySelectorAll('.transactionsSection'));
                    // Find the first section whose computed style is not "none"
                    const visibleSection = sections.find(sec => !sec.closest('div[style*="display: none"]'));
                    if (!visibleSection) return 0;
                    // Look inside the visible section for the table with the deals
                    const paginate = visibleSection.querySelector('.paginate');
                    if (!paginate) return 0;

                    // Safely get the text content
                    const text = paginate.textContent || "";
                    // Assume text is in the form "1 / 5537"
                    const parts = text.split('/');
                    if (parts.length < 2) return 0;
                    // Parse and return the total pages (e.g., "5537")
                    return parseInt(parts[1].trim(), 10);
                    """
                )
            )

            if total_pages == 0:
                print("Could not find the total pages normally.")
            else:
                print("Total pages:", total_pages)
        except Exception as e:
            print("Could not find the total pages. got error")
            print(f"Exception type: {type(e).__name__}")
            print(f"Exception repr: {repr(e)}")
            if hasattr(e, 'msg'):
                print(f"Exception msg: {e.msg}")
            if hasattr(e, 'stacktrace') and e.stacktrace:
                print("Selenium stacktrace:")
                try:
                    print("\n".join(e.stacktrace))
                except Exception:
                    print(e.stacktrace)
            print("Traceback:")
            print(traceback.format_exc())



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
                const sections = Array.from(document.querySelectorAll('.transactionsSection'));
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
                    next_button = WebDriverWait(driver, 15).until(lambda d: get_next_button(d))
                    # next_button = WebDriverWait(driver, 5).until(
                    #     EC.element_to_be_clickable((By.CSS_SELECTOR, 'ul[data-v-26d3d030].pagination #next:not([disabled])'))
                    # )
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
                    final_table_html = f'<table>{header_html}</table>'
                    return {
                        'success': True,
                        'table_html': final_table_html,
                        'page': page if page is not None else 0,
                        'total_pages': total_pages
                    }

            # Wait until rows are present in the visible table
            try:
                print("checks")
                WebDriverWait(driver, 15).until(
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
                page_source_snippet = driver.page_source
                print("Error waiting for rows. Page source snippet:")
                print(page_source_snippet)
                final_table_html = f'<table>{header_html}</table>'
                return {
                    'success': True,
                    'table_html': final_table_html,
                    'page': page if page is not None else 0,
                    'total_pages': total_pages
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
                    final_table_html = f'<table>{header_html}</table>'
                    return {
                        'success': True,
                        'table_html': final_table_html,
                        'page': page if page is not None else 0,
                        'total_pages': total_pages
                    }
                    # raise Exception("No rows found on page")
                    
            except Exception as e:
                print(f"Row extraction error: {str(e)}")
                final_table_html = f'<table>{header_html}</table>'
                return {
                    'success': True,
                    'table_html': final_table_html,
                    'page': page if page is not None else 0,
                    'total_pages': total_pages
                }
                # raise e
        else:
            current_page = 1
            page_rows_html = ""
            while current_page < int(total_pages):
                print(f"Navigating to page {current_page}...")
                try:
                    # Wait for table content to update
                    # WebDriverWait(driver, 30).until(
                    #     lambda d: d.execute_script("""
                    #         return document.querySelectorAll('table#dealsTable.mainTable tbody tr').length > 0;
                    #     """)
                    # )
                    
                     # Wait until rows are present in the visible table
                    WebDriverWait(driver, 15).until(
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
                    next_button = WebDriverWait(driver, 15).until(lambda d: get_next_button(d))
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
                    final_table_html = f'<table>{header_html}</table>'
                    return {
                        'success': True,
                        'table_html': final_table_html,
                        'page': page if page is not None else 0,
                        'total_pages': total_pages
                    }
                    break 
        

        driver.quit()
        
        # Construct final table HTML
        final_table_html = f'<table>{header_html}{page_rows_html}</table>'
        
        return {
            'success': True,
            'table_html': final_table_html,
            'page': page if page is not None else 0,
            'total_pages': total_pages
        }
        
    except Exception as e:
        if 'driver' in locals():
            driver.quit()
        return {
            'success': False,
            'error': str(e)
        }



def save_full_page_screenshot(driver, path):
    try:
        driver.execute_cdp_cmd("Page.enable", {})
        metrics = driver.execute_cdp_cmd("Page.getLayoutMetrics", {})
        content_size = metrics.get("contentSize", {})
        width = int(content_size.get("width", 1200))
        height = int(content_size.get("height", 800))
        shot = driver.execute_cdp_cmd("Page.captureScreenshot", {
            "format": "png",
            "fromSurface": True,
            "captureBeyondViewport": True,
            "clip": {"x": 0, "y": 0, "width": width, "height": height, "scale": 1}
        })
        data = shot.get("data")
        if data:
            with open(path, "wb") as f:
                f.write(base64.b64decode(data))
            return True
    except Exception:
        pass
    # Fallback to viewport-based approach
    try:
        total_width = driver.execute_script("return Math.max(document.body.scrollWidth, document.documentElement.scrollWidth);")
        total_height = driver.execute_script("return Math.max(document.body.scrollHeight, document.documentElement.scrollHeight);")
        driver.set_window_size(total_width, total_height)
        driver.execute_script("window.scrollTo(0, 0)")
        return driver.save_screenshot(path)
    except Exception:
        return False