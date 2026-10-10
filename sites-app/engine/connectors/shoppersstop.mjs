import { createConnector } from "../framework.mjs";
export default createConnector({"id": "shoppersstop", "name": "Shoppers Stop", "host": "shoppersstop.com", "search": "/search/?text=", "marker": "/p-", "titlePattern": "<h1[^>]*>(.*?)</h1>", "pricePattern": "\"value\"\\s*:\\s*([\\d.]+)"});
