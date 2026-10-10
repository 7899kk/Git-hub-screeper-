import { createConnector } from "../framework.mjs";
export default createConnector({"id": "urbanladder", "name": "Urban Ladder", "host": "urbanladder.com", "search": "/products/search?keywords=", "marker": "/products/", "titlePattern": "<h1[^>]*>(.*?)</h1>", "pricePattern": "\"selling_price\"\\s*:\\s*\"?([\\d.]+)"});
