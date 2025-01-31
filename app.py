import time
from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from nadlan_scraper import scrape_nadlan_deals, setup_driver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor

load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)

@app.route('/nadlan-deals', methods=['GET'])
def nadlan_deals():
    display = request.args.get('display', 'false')
    page = request.args.get('page')
    print(page)
    url = 'https://www.nadlan.gov.il/?view=neighborhood&id=65210148&page=deals'
    
    try:
        # Convert page to integer if it exists
        page = int(page) if page is not None else None
        
        result = scrape_nadlan_deals(url, page=page)
        # print(f"Scraping result: {result}")  # Debug log
        
        if not result['success']:
            return jsonify(result), 500
            
        if display == 'true':
            if 'text/html' in request.headers.get('Accept', ''):
                return result['table_html'], 200, {'Content-Type': 'text/html'}
            else:
                return jsonify(result)
        else:
            return jsonify(result)
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid page number'}), 400
    except Exception as e:
        print(f"Route error: {str(e)}")  # Debug log
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.json
    print(data)
    url = data.get('url')
    selector = data.get('selector')
    display = data.get('display', 'false')
    
    if not url or not selector:
        return jsonify({'error': 'URL and selector are required'}), 400
    
    try:
        driver = setup_driver()
        print("navigating")
        driver.get(url)
        print("navigated")
        
        try:
            # Add specific timeout handling for selector
            WebDriverWait(driver, 60).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
        except Exception as selector_error:
            driver.quit()
            return jsonify({
                'success': False,
                'error': f'Selector "{selector}" not found on the page. Please verify the selector is correct.'
            }), 404
            
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            print("elements found")
            html_content = [element.get_attribute('outerHTML') for element in elements]
        except Exception as element_error:
            driver.quit()
            return jsonify({
                'success': False,
                'error': f'Error extracting content with selector "{selector}". Please verify the selector syntax.'
            }), 400
        
        print("html content")
        driver.quit()
        print("driver quit")

        if not html_content:
            return jsonify({
                'success': False,
                'error': f'No elements found matching selector: {selector}'
            }), 404
        
        if display == 'true':
            return ''.join(html_content), 200, {'Content-Type': 'text/html'}
        else:
            return jsonify({'success': True, 'data': html_content})
            
    except Exception as e:
        # Handle other general errors
        error_message = str(e)
        if "chrome not reachable" in error_message.lower():
            return jsonify({
                'success': False,
                'error': 'Browser connection failed. Please try again.'
            }), 500
        elif "timeout" in error_message.lower():
            return jsonify({
                'success': False,
                'error': 'Page load timed out. Please try again or check the URL.'
            }), 504
        else:
            return jsonify({
                'success': False,
                'error': 'An unexpected error occurred while scraping the page.'
            }), 500

@app.route('/autocomplete', methods=['POST'])
def autocomplete():
    data = request.json
    search_text = data.get('text')
    print(f"search_text: {search_text}")
    
    if not search_text:
        return jsonify({'error': 'Search text is required'}), 400
        
    try:
        print("setting")
        driver = setup_driver()
        print("driver setup")
        url = 'https://www.nadlan.gov.il/?view=neighborhood&id=65210148&page=deals'
        driver.get(url)
        print("driver get")
        
        # print(driver.page_source)  # Check if content is fully loaded

        # Wait for search input and enter text
        search_input = WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.ID, "myInput2"))
        )
        print("search input")

        # Clear and set initial search text using JavaScript
        driver.execute_script("""
            const input = document.getElementById('myInput2');
            input.value = '';  // Clear first
            input.value = arguments[0];
            input.dispatchEvent(new Event('input', { bubbles: true }));
            input.dispatchEvent(new Event('change', { bubbles: true }));
            input.dispatchEvent(new KeyboardEvent('keydown', { bubbles: true }));
            input.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true }));
        """, search_text)
        print("search input send keys")
        driver.save_screenshot("enterd_search.png")
        
        # Wait for suggestions using JavaScript

        
        try:
            print("waiting for suggestions")
            time.sleep(10)
            driver.save_screenshot("enterd_search_2.png")
            # wait for suggestions to show
            WebDriverWait(driver, 60).until(
                EC.presence_of_element_located((By.ID, 'react-autowhatever-1'))
            )
            print("suggestions showed")
            driver.save_screenshot("suggestions_showed.png")
            # WebDriverWait(driver, 60).until(
            #     lambda d: d.execute_script("""
            #         return document.querySelector('.react-autosuggest__suggestions-list') !== null &&
            #                document.querySelectorAll('.react-autosuggest__suggestions-list li').length > 0;
            #     """)
            # )
            print("suggestions list")
        except Exception as e:
            print(f"Error waiting for suggestions: {str(e)}")
            driver.save_screenshot("debug.png")
            driver.quit()
            return jsonify({
                'success': False,
                'error': 'No suggestions found'
            }), 404

        # Get all suggestions with their IDs using JavaScript
        suggestion_data = driver.execute_script("""
            const suggestions = document.querySelectorAll('.react-autosuggest__suggestions-list li');
            return Array.from(suggestions).map(suggestion => ({
                text: suggestion.textContent,
                id: suggestion.getAttribute('id')
            }));
        """)
        print(suggestion_data)
        
        results = []
        for data in suggestion_data:
            try:
                # Store the current URL before clicking
                original_url = driver.current_url
                
                # Click using JavaScript with retry mechanism
                clicked = driver.execute_script("""
                    function clickElement(id) {
                        const element = document.getElementById(id);
                        if (element) {
                            element.click();
                            return true;
                        }
                        return false;
                    }
                    
                    // Try clicking multiple times with small delays
                    for (let i = 0; i < 10; i++) {
                        if (clickElement(arguments[0])) {
                            return true;
                        }
                        // Small delay between attempts
                        for (let j = 0; j < 1000000; j++) {}
                    }
                    return false;
                """, data["id"])
                
                if not clicked:
                    print(f"Could not click element with ID: {data['id']}")
                    driver.save_screenshot(f"debug_{data['id']}.png")
                    continue
                
                print("clicked")
                
                # Wait for URL to change
                WebDriverWait(driver, 60).until(
                    lambda d: d.current_url != original_url
                )
                
                # Get URL after navigation completes
                current_url = driver.current_url
                print(f"current_url: {current_url}")
                
                results.append({
                    "text": data["text"],
                    "link": current_url
                })
                
                # Navigate back
                driver.back()
                
                # Wait for original URL to be restored
                WebDriverWait(driver, 60).until(
                    lambda d: d.current_url == original_url
                )
                
                # Re-enter search text using JavaScript
                search_input = WebDriverWait(driver, 60).until(
                    EC.presence_of_element_located((By.ID, "myInput2"))
                )
                print("search input 2")
                driver.execute_script("""
                    const input = document.getElementById('myInput2');
                    if (input) {
                        input.value = '';  // Clear first
                        input.value = arguments[0];
                        input.focus();
                        input.dispatchEvent(new Event('focus', { bubbles: true }));
                        input.dispatchEvent(new Event('input', { bubbles: true }));
                        input.dispatchEvent(new Event('change', { bubbles: true }));
                        input.dispatchEvent(new KeyboardEvent('keydown', { 
                            bubbles: true,
                            key: 'Process',
                            code: 'Process'
                        }));
                    }
                """, search_text)
                driver.save_screenshot(f"re_enterd_search_{data['id']}.png")
                print("re enterd search saved")
                # wait for suggestions to show
                WebDriverWait(driver, 60).until(
                    EC.presence_of_element_located((By.ID, 'react-autowhatever-1'))
                )
                print("suggestions showed")
                driver.save_screenshot(f"suggestions_showed_{data['id']}.png")
                # Wait for suggestions list to reappear
                # WebDriverWait(driver, 60).until(
                #     lambda d: d.execute_script("""
                #         return document.querySelector('.react-autosuggest__suggestions-list') !== null &&
                #                document.querySelectorAll('.react-autosuggest__suggestions-list li').length > 0;
                #     """)
                # )
                
            except Exception as e:
                print(f"Error processing suggestion '{data}': {str(e)}")
                driver.save_screenshot(f"debug_2{data['id']}.png")
                continue
        
        driver.quit()
        return jsonify(results)
        
    except Exception as e:
        print(f"Error in autocomplete: {str(e)}")
        if 'driver' in locals():
            driver.quit()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({'status': 'OK'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 4000))
    app.run(host='0.0.0.0', port=port) 