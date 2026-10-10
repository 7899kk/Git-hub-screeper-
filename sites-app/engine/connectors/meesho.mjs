import { createConnector } from "../framework.mjs";
export default createConnector({"id": "meesho", "name": "Meesho", "host": "meesho.com", "search": "/search?q=", "marker": "/p/", "titlePattern": "<h1[^>]*>(.*?)</h1>", "pricePattern": "\"price\"\\s*:\\s*([\\d.]+)"});
