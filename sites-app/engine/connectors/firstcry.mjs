import { createConnector } from "../framework.mjs";
export default createConnector({"id": "firstcry", "name": "FirstCry", "host": "firstcry.com", "search": "/search.aspx?searchstring=", "marker": "/product-detail", "titlePattern": "<h1[^>]*>(.*?)</h1>", "pricePattern": "\"offerPrice\"\\s*:\\s*\"?([\\d.]+)"});
