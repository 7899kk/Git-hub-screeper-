import { createConnector } from "../framework.mjs";
export default createConnector({"id": "flipkart", "name": "Flipkart", "host": "flipkart.com", "search": "/search?q=", "marker": "/p/", "titlePattern": "<h1[^>]*>([\\s\\S]*?)</h1>", "pricePattern": "(?:class=\"[^\"]*(?:Nx9bqj|_30jeq3)[^\"]*\"[^>]*>)[^\u20b9]*\u20b9([\\d,.]+)"});
