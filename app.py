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

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({'status': 'OK'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 4000))
    app.run(host='0.0.0.0', port=port) 