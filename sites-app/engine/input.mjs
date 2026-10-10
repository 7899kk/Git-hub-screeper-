// Accept a bare URL or Android's copied product-share text.
export function productInput(value){
 const text=String(value??'').trim();
 const links=text.match(/https:\/\/[^\s<>"'\u200b]+/gi)||[];
 if(links.length>1)throw new Error('Paste one product link at a time');
 return links.length?links[0].replace(/&amp;/g,'&'):text;
}
