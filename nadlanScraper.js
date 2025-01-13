const puppeteer = require('puppeteer-core');

async function scrapeNadlanDeals(url) {
    try {
        const browser = await puppeteer.launch({
            executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
            headless: 'new'
        });

        const page = await browser.newPage();
        await page.setViewport({ width: 1920, height: 1080 });
        await page.goto(url, { waitUntil: 'networkidle0', timeout: 1800000 });

        // Wait for the initial table to load
        await page.waitForSelector('table', { timeout: 1800000 });

        // Get the HTML of the table
        const tableHtml = await page.evaluate(() => {
            const table = document.querySelector('table');
            if (!table) return null;
            
            // Clean up the table by removing any duplicate trend columns
            const cleanTable = table.cloneNode(true);
            // Remove the trend summary elements if they exist
            const trendSummaries = cleanTable.querySelectorAll('.trend-summary');
            trendSummaries.forEach(el => el.remove());
            
            return cleanTable.outerHTML;
        });

        // Get neighborhood stats
        const stats = await page.evaluate(() => {
            return {
                yield: document.querySelector('.yield')?.textContent.trim(),
                priceChange: document.querySelector('.price-drop')?.textContent.trim(),
                neighborhoodRating: document.querySelector('.neighborhood-value')?.textContent.trim()
            };
        });

        await browser.close();

        return {
            success: true,
            stats,
            tableHtml
        };

    } catch (error) {
        console.error('Scraping error:', error);
        return {
            success: false,
            error: error.message
        };
    }
}

// Export the function if you're using it in other files
module.exports = { scrapeNadlanDeals }; 