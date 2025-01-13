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

        let hasNextPage = true;
        let currentPage = 1;
        let allTablesHtml = '';

        // Get the header row HTML once
        const headerHtml = await page.evaluate(() => {
            const headerRow = document.querySelector('table tr:first-child');
            // Clean up header by removing duplicate trend column if it exists
            const cleanHeader = headerRow.cloneNode(true);
            const trendCells = cleanHeader.querySelectorAll('th');
            // Keep only the last trend column if duplicates exist
            for (let i = 0; i < trendCells.length - 1; i++) {
                if (trendCells[i].textContent.includes('Trend')) {
                    trendCells[i].remove();
                }
            }
            return cleanHeader.outerHTML;
        });

        while (hasNextPage && currentPage < 90) {
            console.log(`Scraping page ${currentPage}...`);

            // Get the rows from current page
            const pageRowsHtml = await page.evaluate(() => {
                const rows = document.querySelectorAll('table tr:not(:first-child)');
                return Array.from(rows).map(row => {
                    // Clean up each row by removing duplicate trend column
                    const cleanRow = row.cloneNode(true);
                    const cells = cleanRow.querySelectorAll('td');
                    // Remove duplicate trend cells, keep only the last one
                    for (let i = 0; i < cells.length - 1; i++) {
                        if (cells[i].classList.contains('trend-summary')) {
                            cells[i].remove();
                        }
                    }
                    return cleanRow.outerHTML;
                }).join('');
            });

            // Add rows to our collection
            allTablesHtml += pageRowsHtml;

            // Check for next page button and click if exists
            hasNextPage = await page.evaluate(() => {
                const nextButton = document.querySelector('ul[data-v-26d3d030].pagination #next:not([disabled])');
                if (nextButton) {
                    nextButton.click();
                    return true;
                }
                return false;
            });

            if (hasNextPage) {
                // Wait for the table to update with new data
                await page.waitForFunction(
                    () => {
                        const rows = document.querySelectorAll('table tr:not(:first-child)');
                        return rows.length > 0;
                    },
                    { timeout: 1800000 }
                );
                currentPage++;
                // Add a small delay to ensure content is fully loaded
                await new Promise(resolve => setTimeout(resolve, 1000));
            }
        }

        // Get neighborhood stats
        const stats = await page.evaluate(() => {
            return {
                yield: document.querySelector('.yield')?.textContent.trim(),
                priceChange: document.querySelector('.price-drop')?.textContent.trim(),
                neighborhoodRating: document.querySelector('.neighborhood-value')?.textContent.trim()
            };
        });

        await browser.close();

        // Construct the complete table HTML
        const tableHtml = `<table>${headerHtml}${allTablesHtml}</table>`;

        return {
            success: true,
            stats,
            tableHtml,
            totalPages: currentPage
        };

    } catch (error) {
        console.error('Scraping error:', error);
        return {
            success: false,
            error: error.message
        };
    }
}

module.exports = { scrapeNadlanDeals }; 