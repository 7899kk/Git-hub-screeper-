import { createConnector } from "../framework.mjs";
export default createConnector({"id": "ikea", "name": "IKEA India", "host": "ikea.com", "search": "/in/en/search/?q=", "marker": "/in/en/p/", "titlePattern": "class=\"pip-header-section__description-text\"[^>]*>(.*?)<", "pricePattern": "class=\"pip-price__integer\"[^>]*>([\\d,]+)"});
