const puppeteer = require('puppeteer-core');
const fs = require('fs');

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

        let allDeals = [];
        let hasNextPage = true;
        let currentPage = 1;
        let count = 0;

        while (hasNextPage && count < 90) {
            console.log(`Scraping page ${currentPage}...`);

            // Extract data from current page
            const pageDeals = await page.evaluate(() => {
                const rows = document.querySelectorAll('table tr:not(:first-child)');
                return Array.from(rows).map(row => {
                    const cells = row.querySelectorAll('td');
                    return {
                        trendOfChange: cells[9]?.textContent.trim(),
                        floor: cells[8]?.textContent.trim(),
                        rooms: cells[7]?.textContent.trim(),
                        propertyType: cells[6]?.textContent.trim(),
                        blockAndParcel: cells[5]?.textContent.trim(),
                        transactionPrice: cells[4]?.textContent.trim(),
                        transactionDate: cells[3]?.textContent.trim(),
                        areaInSquareMeters: cells[2]?.textContent.trim(),
                        address: cells[1]?.textContent.trim(),
                        serialNumber: cells[0]?.textContent.trim()
                    };
                });
            });

            allDeals = [...allDeals, ...pageDeals];
            if(currentPage == 40) {
                console.log(allDeals)
            }

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
                    (oldLength) => {
                        const rows = document.querySelectorAll('table tr:not(:first-child)');
                        return rows.length > 0 && rows[0].textContent !== oldLength;
                    },
                    { timeout: 1800000 },
                    pageDeals[0]?.serialNumber
                );
                currentPage++;
                // Add a small delay to ensure content is fully loaded
                await new Promise(resolve => setTimeout(resolve, 1000));
            }
            count++;
        }

        // Get neighborhood stats (only need to do this once)
        const stats = await page.evaluate(() => {
            return {
                yield: document.querySelector('.yield')?.textContent.trim(),
                priceChange: document.querySelector('.price-drop')?.textContent.trim(),
                neighborhoodRating: document.querySelector('.neighborhood-value')?.textContent.trim()
            };
        });

        await browser.close();

        // Generate unique filename with timestamp
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const filename = `nadlan_deals_${timestamp}.csv`;

        // Export to CSV with all deals
        const csvHeader = 'Trend of Change,Floor,Rooms,Property Type,Block and Parcel,Transaction Price,Transaction Date,Area (m²),Address,Serial Number\n';
        const csvRows = allDeals.map(deal => {
            return `"${deal.trendOfChange}","${deal.floor}","${deal.rooms}","${deal.propertyType}","${deal.blockAndParcel}","${deal.transactionPrice}","${deal.transactionDate}","${deal.areaInSquareMeters}","${deal.address}","${deal.serialNumber}"`;
        }).join('\n');

        const csvContent = csvHeader + csvRows;
        
        // Add try-catch specifically for file writing
        try {
            fs.writeFileSync(filename, csvContent, { encoding: 'utf-8', flag: 'wx' });
        } catch (writeError) {
            console.error('Error writing CSV:', writeError);
            // If file writing fails, continue without CSV
            return {
                success: true,
                stats,
                deals: allDeals,
                totalDeals: allDeals.length,
                totalPages: currentPage,
                csvError: writeError.message
            };
        }

        console.log(`Scraping completed. Total deals: ${allDeals.length}, Total pages: ${currentPage}`);
        console.log( {
            success: true,
            stats,
            deals: allDeals,
            totalDeals: allDeals.length,
            totalPages: currentPage,
            csvPath: filename
        })
        return {
            success: true,
            stats,
            deals: allDeals,
            totalDeals: allDeals.length,
            totalPages: currentPage,
            csvPath: filename
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