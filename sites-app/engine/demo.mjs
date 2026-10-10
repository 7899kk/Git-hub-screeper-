
export const demoProducts=[
 {id:'demo-phone',title:'Samsung Galaxy S24',subtitle:'8 GB RAM · 128 GB · Onyx Black',brand:'Samsung',model:'SM-S921B',category:'Mobiles',icon:'phone',price:5299900,mrp:7999900,color:'#d5e6db',variant:{storage:'128 GB',ram:'8 GB',color:'black'},offers:[{platform:'Amazon India',price:5299900},{platform:'Flipkart',price:5499900},{platform:'Croma',price:5599900}]},
 {id:'demo-audio',title:'Sony WH-1000XM5',subtitle:'Wireless noise cancelling · Black',brand:'Sony',model:'WH-1000XM5',category:'Electronics',icon:'headphones',price:2499000,mrp:3499000,color:'#e2ddf5',variant:{color:'black'},offers:[{platform:'Croma',price:2499000},{platform:'Amazon India',price:2699000}]},
 {id:'demo-shoe',title:'RUN Active Running Shoes',subtitle:'Men · Navy · Size 9',brand:'Kalenji',model:'RUN ACTIVE',category:'Sports',icon:'shoe',price:149900,mrp:249900,color:'#f2e3d7',variant:{color:'blue',size:'9'},offers:[{platform:'Decathlon India',price:149900}]},
 {id:'demo-coffee',title:'Philips Drip Coffee Maker',subtitle:'HD7432/20 · 0.6 L · Black',brand:'Philips',model:'HD7432/20',category:'Appliances',icon:'coffee',price:229900,mrp:349500,color:'#e5e7e9',variant:{color:'black'},offers:[{platform:'Amazon India',price:229900},{platform:'Reliance Digital',price:249900}]}
];
export const demoHistory=[5999900,5899900,5899900,5699900,5799900,5599900,5499900,5499900,5299900].map((price,i)=>({price,observed_at:new Date(Date.UTC(2026,8,20+i*2)).toISOString(),verification:'sample'}));
