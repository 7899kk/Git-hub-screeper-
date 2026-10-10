import {env} from 'cloudflare:workers';
export function middleware(request:Request){
 if(!env.OWNER_PASSWORD&&env.REQUIRE_OWNER_AUTH!=='true')return;
 if(!env.OWNER_PASSWORD)return new Response('Configure OWNER_PASSWORD before enabling this deployment.',{status:503});
 const expected='Basic '+btoa('owner:'+env.OWNER_PASSWORD);
 if(request.headers.get('authorization')!==expected)return new Response('Private PricePulse workspace',{status:401,headers:{'WWW-Authenticate':'Basic realm="PricePulse India", charset="UTF-8"','Cache-Control':'no-store'}});
}
export const config={matcher:['/:path*']};
