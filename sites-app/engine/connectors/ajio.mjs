import { createConnector } from "../framework.mjs";
export default createConnector({"id": "ajio", "name": "AJIO", "host": "ajio.com", "search": "/search/?text=", "marker": "/p/", "titlePattern": "class=\"prod-name\"[^>]*>(.*?)<", "pricePattern": "class=\"prod-sp\"[^>]*>[^\u20b9]*\u20b9([\\d,.]+)"});
