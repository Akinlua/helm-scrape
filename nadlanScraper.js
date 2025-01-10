const puppeteer = require('puppeteer-core');
const fs = require('fs');

async function scrapeNadlanDeals(url) {
    try {
        // Launch browser with puppeteer-core
        const browser = await puppeteer.launch({
            executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe', // Adjust path for your system
            headless: 'new'
        });

        const page = await browser.newPage();
        await page.setViewport({ width: 1920, height: 1080 });

        // Navigate to the page
        await page.goto(url, { waitUntil: 'networkidle0', timeout: 1800000 });

        // Wait for the deals table to load
        await page.waitForSelector('table', { timeout: 1800000 });

        // Extract the data
        const deals = await page.evaluate(() => {
            const rows = document.querySelectorAll('table tr:not(:first-child)');
            return Array.from(rows).map(row => {
                const cells = row.querySelectorAll('td');
                return {
                    trendOfChange: cells[0]?.textContent.trim(),
                    floor: cells[1]?.textContent.trim(),
                    rooms: cells[2]?.textContent.trim(),
                    propertyType: cells[3]?.textContent.trim(),
                    blockAndParcel: cells[4]?.textContent.trim(),
                    transactionPrice: cells[5]?.textContent.trim(),
                    transactionDate: cells[6]?.textContent.trim(),
                    areaInSquareMeters: cells[7]?.textContent.trim(),
                    address: cells[8]?.textContent.trim(),
                    serialNumber: cells[9]?.textContent.trim()
                };
            });
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

        // Add CSV export functionality
        const csvHeader = 'Trend of Change,Floor,Rooms,Property Type,Block and Parcel,Transaction Price,Transaction Date,Area (m²),Address,Serial Number\n';
        const csvRows = deals.map(deal => {
            return `"${deal.trendOfChange}","${deal.floor}","${deal.rooms}","${deal.propertyType}","${deal.blockAndParcel}","${deal.transactionPrice}","${deal.transactionDate}","${deal.areaInSquareMeters}","${deal.address}","${deal.serialNumber}"`;
        }).join('\n');

        const csvContent = csvHeader + csvRows;
        fs.writeFileSync('nadlan_deals.csv', csvContent, 'utf-8');

        return {
            success: true,
            stats,
            deals,
            totalDeals: deals.length,
            csvPath: 'nadlan_deals.csv'
        };

    } catch (error) {
        console.error('Scraping error:', error);
        return {
            success: false,
            error: error.message
        };
    }
}

// Example usage
const url = 'https://www.nadlan.gov.il/?view=neighborhood&id=65210148&page=deals';

scrapeNadlanDeals(url)
    .then(result => {
        console.log(JSON.stringify(result, null, 2));
    })
    .catch(error => {
        console.error('Error:', error);
    }); 