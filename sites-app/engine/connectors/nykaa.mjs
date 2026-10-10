import { createConnector } from "../framework.mjs";
export default createConnector({"id": "nykaa", "name": "Nykaa", "host": "nykaa.com", "search": "/search/result/?q=", "marker": "/p/", "titlePattern": "<h1[^>]*>(.*?)</h1>", "pricePattern": "\"discountedPrice\"\\s*:\\s*\"?([\\d.]+)"});
