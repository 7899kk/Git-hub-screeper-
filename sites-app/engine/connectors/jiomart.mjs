import { createConnector } from "../framework.mjs";
export default createConnector({"id": "jiomart", "name": "JioMart", "host": "jiomart.com", "search": "/search/", "marker": "/p/", "titlePattern": "<h1[^>]*>(.*?)</h1>", "pricePattern": "\"selling_price\"\\s*:\\s*\"?([\\d.]+)"});
