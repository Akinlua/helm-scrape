const express = require('express');
const cors = require('cors');
const { scrapeNadlanDeals } = require('./nadlanScraper');

const app = express();
const port = 4000;

app.use(cors());
app.use(express.json());

// Specific endpoint for Nadlan.gov.il
app.get('/nadlan-deals', async (req, res) => {
    const { display } = req.query;
    
    // if (!id) {
    //     return res.status(400).json({
    //         error: 'Neighborhood ID is required'
    //     });
    // }

    try {
        // const url = `https://www.nadlan.gov.il/?view=neighborhood&id=${id}&page=deals`;
        const url = 'https://www.nadlan.gov.il/?view=neighborhood&id=65210148&page=deals'
        const result = await scrapeNadlanDeals(url);
        
        // Set content type to HTML if the client requests it
        if(display === 'true'){
            if (req.headers.accept && req.headers.accept.includes('text/html')) {
                console.log("conetn")
                res.setHeader('Content-Type', 'text/html');
                res.send(result.tableHtml);
            } else {
                console.log("nodidnt")
                // Otherwise send JSON response
                res.json(result);
            }
        } else {
            res.json(result);
        }
        
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Keep the generic scraping endpoint
app.post('/scrape', async (req, res) => {
    const { url, selector } = req.body;

    if (!url || !selector) {
        return res.status(400).json({
            error: 'URL and selector are required'
        });
    }

    try {
        // Launch browser
        const browser = await puppeteer.launch({
            headless: 'new',
            args: ['--no-sandbox', '--disable-setuid-sandbox']
        });

        // Create new page
        const page = await browser.newPage();

        // Set viewport
        await page.setViewport({ width: 1920, height: 1080 });

        // Navigate to URL
        await page.goto(url, {
            waitUntil: 'networkidle0',
            timeout: 30000
        });

        // Wait for selector to be available
        await page.waitForSelector(selector, { timeout: 10000 });

        // Get HTML content with improved error handling
        const htmlContent = await page.evaluate((selector) => {
            const elements = document.querySelectorAll(selector);
            if (elements.length === 0) {
                return null;
            }
            return Array.from(elements).map(element => element.outerHTML);
        }, selector);

        if (!htmlContent) {
            return res.status(404).json({
                success: false,
                error: `No elements found matching selector: ${selector}`
            });
        }

        // Close browser
        await browser.close();

        // Return the scraped content
        res.json({
            success: true,
            data: htmlContent
        });

    } catch (error) {
        console.error('Scraping error:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Health check endpoint
app.get('/', (req, res) => {
    res.json({ status: 'OK' });
});

// Start server
app.listen(port, () => {
    console.log(`Server running on port ${port}`);
});
