// French quarter · evening district scene.
// Ported VERBATIM from branding/stories/district_2d.html per the fidelity rules.
// Only allowed changes applied: module-level ctx, export + TS types, dropped HTML/demo chrome.

import { AV_FOX, AV_BEAR, type Rect } from '../sprites';

let ctx: CanvasRenderingContext2D;

export function drawFrench(context: CanvasRenderingContext2D, t: number, heroAv: Rect[] | null = null): void {
  ctx = context;
  const W = ctx.canvas.width, H = ctx.canvas.height;   // 200 x 356 low-res buffer, ×2 crisp
  ctx.imageSmoothingEnabled = false;
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;

  // ---------- mature evening palette ----------
  const C = {
    ink:'#0e1017', stone:['#b8ad8f','#aa9f82','#c2b89a','#9c9478','#b0a686'],
    zinc:'#3e434e', zincHi:'#545a68', iron:'#191c23',
    winWarm:'#ffbe5a', winHi:'#ffe3ad', winCold:'#28344c', winDark:'#161b28',
    cream:'#efe6cf', gold:'#e8bf48',
    awn:['#7e322f','#2f567f','#3a6b4a','#6b4a7a'], teal:'#49b7a6', neon:'#ff8a4a',
    cobble:'#26262b', cobbleWet:'#1a1a20', rubber:'#352b30',
    haze:'#4b4a60', rimCool:'#9ec2d8', rimWarm:'#ffd49a'
  };
  const THEME = {
    name:'ФРАНЦУЗСКИЙ КВАРТАЛ', quest:'КВЕСТ: ДЕНЬ ТРИЦЕПСА · 7 ДНЕЙ',
    skyTop:'#151b2d', skyHorizon:'#8a6455',
    stone:C.stone, awnings:C.awn, far:'eiffel',
    weather:{clouds:true, birds:true, rain:true},
    ped:['#5f4636','#30495f','#53384a','#4a4d57','#6f5330','#2f4a44']
  };

  // ---------- band geometry ----------
  const FAR_BASE=176, GROUND=238, STREET_H=46, SPORTS_TOP=280;

  // ---------- helpers ----------
  const R=(x:number,y:number,w:number,h:number,col:string)=>{ctx.fillStyle=col; ctx.fillRect(x|0,y|0,Math.max(1,w|0),Math.max(1,h|0));};
  const A=(a:number,fn:()=>void)=>{ctx.globalAlpha=a; fn(); ctx.globalAlpha=1;};
  const lerp=(a:number,b:number,t:number)=>a+(b-a)*t;
  function mix(a:string,b:string,t:number){const pa=parseInt(a.slice(1),16),pb=parseInt(b.slice(1),16);
    const r=Math.round(lerp((pa>>16)&255,(pb>>16)&255,t)),g=Math.round(lerp((pa>>8)&255,(pb>>8)&255,t)),bl=Math.round(lerp(pa&255,pb&255,t));
    return '#'+((1<<24)+(r<<16)+(g<<8)+bl).toString(16).slice(1);}
  function mulberry(s:number){return ()=>{s|=0;s=s+0x6D2B79F5|0;let t=Math.imul(s^s>>>15,1|s);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296;};}
  const hash=(a:number)=>{a=Math.sin(a)*43758.5453;return a-Math.floor(a);};
  function disc(cx:number,cy:number,r:number,col:string){ctx.fillStyle=col; for(let y=-r;y<=r;y++){const w=Math.floor(Math.sqrt(r*r-y*y)+1e-3); ctx.fillRect((cx-w)|0,(cy+y)|0,2*w+1,1);} }
  const discA=(cx:number,cy:number,r:number,col:string,a:number)=>A(a,()=>disc(cx,cy,r,col));
  function glow(cx:number,cy:number,r:number,col:string){ discA(cx,cy,r,col,0.06); discA(cx,cy,(r*0.66)|0,col,0.09); discA(cx,cy,(r*0.36)|0,col,0.13); }
  function vgrad(x:number,y:number,w:number,h:number,c0:string,c1:string,bands:number){const bh=h/bands;
    for(let i=0;i<bands;i++) R(x,y+Math.floor(i*bh),w,Math.ceil(bh)+1,mix(c0,c1,i/(bands-1)));
    for(let i=1;i<bands;i++){const yy=y+Math.round(i*bh),ca=mix(c0,c1,(i-1)/(bands-1));
      for(let xx=x+((yy&1)?0:1); xx<x+w; xx+=2) R(xx,yy,1,1,ca);} }
  // ordered-dither horizontal haze band (fades with t 0..1 top→bottom opacity)
  function haze(x:number,y:number,w:number,h:number,col:string,topA:number){ for(let yy=0;yy<h;yy++){ const a=topA*(1-yy/h);
    for(let xx=0;xx<w;xx++){ if(((xx+ (yy&1))&1)===0 && hash((x+xx)*2.1+(y+yy)*3.7) < a) R(x+xx,y+yy,1,1,col);} } }
  // warm reflection smeared down wet ground
  function reflect(x:number,yTop:number,len:number,col:string){ A(1,()=>{}); for(let i=0;i<len;i++){ const a=0.3*(1-i/len);
    if(a<=0) break; const jx=((hash(x*1.7+i*0.9)*3)|0)-1; A(a,()=>R(x+ (i>2?jx:0), yTop+i,1,1,col)); } }

  // ---------- static layout (seeded once) ----------
  const rS=mulberry(7); const STARS=Array.from({length:30},()=>({x:(rS()*W)|0,y:(rS()*120)|0,b:rS()}));
  const rC=mulberry(21); const FARCITY:{x:number;w:number;h:number}[]=[],MIDCITY:{x:number;w:number;h:number;wins:{wx:number;wy:number;ph:number;on0:boolean}[]}[]=[];
  for(let x=-8;x<W+8;x+=20) FARCITY.push({x,w:14+(rC()*12|0),h:28+(rC()*54|0)});
  for(let x=-10;x<W+12;x+=22){ const w=18+(rC()*14|0),h=50+(rC()*80|0),wins:{wx:number;wy:number;ph:number;on0:boolean}[]=[];
    for(let wy=10;wy<h-10;wy+=9) for(let wx=4;wx<w-5;wx+=7) if(rC()<0.5) wins.push({wx,wy,ph:rC(),on0:rC()<0.5});
    MIDCITY.push({x,w,h,wins}); }
  const rCl=mulberry(5); const CLOUDS=Array.from({length:3},(_,i)=>({x0:rCl()*W,y:24+i*22+(rCl()*8|0),spd:0.04+rCl()*0.06,sc:0.9+rCl()*0.8,sh:0.14+rCl()*0.08}));
  const FLOCKS=[{y:92,spd:0.1,n:5,ph:0},{y:70,spd:0.16,n:4,ph:70}];
  // district buildings — richer per-building features (the themed облицовка)
  const SHOPS=['cafe','boul','pharm','bar','cafe'];   // café, boulangerie, pharmacie(+neon cross), bar(neon), café
  const rB=mulberry(42); const BUILDINGS:{x:number;w:number;h:number;floors:number;cols:number;stone:string;shop:string|null;awn:string;wins:{f:number;c:number;ph:number;warm0:boolean;shut:boolean;box:boolean}[];roof:{anten:boolean;tank:boolean;pots:number};bal:boolean;drain:boolean;age:number}[]=[]; { let x=-4;
    while(x<W+4){ const w=30+(rB()*22|0), floors=3+(rB()*4|0), h=floors*19+15;
      const stone=THEME.stone[(rB()*THEME.stone.length)|0];
      const shop= rB()<0.7 ? SHOPS[(rB()*SHOPS.length)|0] : null;
      const awn=THEME.awnings[(rB()*THEME.awnings.length)|0];
      const cols=Math.max(2,(w-8)/10|0), wins:{f:number;c:number;ph:number;warm0:boolean;shut:boolean;box:boolean}[]=[];
      for(let f=0;f<floors;f++) for(let c=0;c<cols;c++) wins.push({f,c,ph:rB(),warm0:rB()<0.52,shut:rB()<0.5,box:rB()<0.3});
      const roof={anten:rB()<0.5, tank:rB()<0.25, pots:1+(rB()*2|0)};
      BUILDINGS.push({x,w,h,floors,cols,stone,shop,awn,wins,roof, bal:floors>=4, drain:rB()<0.6, age:rB()}); x+=w+1; } }
  const LAMPS=[22,70,120,172]; const TREES=[48,150]; const PUDDLES=[30,92,158,186];
  // street clutter
  const CLUTTER=[{t:'kiosk',x:98},{t:'bollard',x:14},{t:'bollard',x:40},{t:'bollard',x:160},{t:'bollard',x:186},{t:'bike',x:178},{t:'bin',x:60},{t:'manhole',x:110}];
  const PEDS=[
    {base:0.10,spd:0.009,dir:1, y:GROUND+32,sc:1.0, coat:THEME.ped[0],head:'#c7b89a',umb:false,dog:true},
    {base:0.58,spd:0.007,dir:-1,y:GROUND+34,sc:1.0, coat:THEME.ped[1],head:'#d6d6d6',umb:true,dog:false},
    {base:0.34,spd:0.012,dir:1, y:GROUND+30,sc:1.0, coat:THEME.ped[2],head:'#caa98f',umb:true,dog:false},
    {base:0.80,spd:0.0055,dir:-1,y:GROUND+22,sc:0.8, coat:THEME.ped[3],head:'#b9bcc4',umb:false,dog:false},
    {base:0.46,spd:0.010,dir:1, y:GROUND+20,sc:0.76,coat:THEME.ped[5],head:'#c0b59a',umb:false,dog:false},
  ];
  const rR=mulberry(3); const RAIN=Array.from({length:120},()=>({x:(rR()*W)|0,y:(rR()*H)|0,len:5+(rR()*7|0),sp:5+rR()*4}));

  // ---------- project avatars (32×32, straight from backend/static/sprites/avatars) ----------
  function drawAvatar(av:Rect[],cx:number,topY:number,sc:number){ for(const r of av){ const x=Math.round(cx-16*sc+r[0]*sc), y=Math.round(topY+r[1]*sc); R(x,y,Math.max(1,Math.round(r[2]*sc)),Math.max(1,Math.round(r[3]*sc)),r[4]); } }

  // ================= LAYERS =================
  function drawSky(t:number){
    vgrad(0,0,W,SPORTS_TOP, THEME.skyTop, THEME.skyHorizon, 11);
    for(const s of STARS){ if(s.y>FAR_BASE-24) continue; const on=reduce?s.b>.3:(Math.sin(t/900+s.x)>-.2); if(on) R(s.x,s.y,1,1,mix('#283152','#c7d0ec',s.b)); }
    const mx=44,my=38;
    glow(mx,my,22,mix(THEME.skyTop,'#ffe9c0',0.85));
    disc(mx,my,7,'#efe3c2'); R(mx-7,my-7,14,1,'#fff4d8'); disc(mx+2,my+1,3,mix('#efe3c2','#000',0.12));
    A(0.5,()=>disc(mx-3,my-2,5,mix('#efe3c2','#000',0.08)));
  }
  function drawClouds(t:number){ if(!THEME.weather.clouds) return;
    for(const cl of CLOUDS){ const x=((cl.x0+t*cl.spd)%(W+70))-35, col=mix(THEME.skyTop,C.cream,0.1+cl.sh);
      for(const [dx,dy,r] of [[-14,2,8],[-3,-3,12],[9,2,10],[19,3,6]]) A(0.85,()=>disc(x+dx,cl.y+dy,Math.round(r*cl.sc),col)); } }
  function drawFarCity(t:number){
    for(const b of FARCITY) R(b.x,FAR_BASE-b.h,b.w,b.h, mix(mix('#242a40','#12152a',0.4), C.haze, 0.35));   // hazed far band
    drawClouds(t);
    const tick=(t/3000)|0;
    for(const b of MIDCITY){ R(b.x,FAR_BASE-b.h,b.w,b.h, mix(mix('#1d2130','#0d1018',0.3), C.haze, 0.18));
      for(const w of b.wins){ let on=w.on0; if(w.ph>0.9) on=hash(w.ph*91.7+tick*2.3)>0.5;
        if(on) R(b.x+w.wx,FAR_BASE-b.h+w.wy,3,4, mix(C.winWarm,C.haze,0.3)); } }
    if(THEME.far==='eiffel') eiffel(92,FAR_BASE,86);
    if(THEME.weather.birds) for(const fl of FLOCKS){ const head=((fl.ph+t*fl.spd)%(W+60))-30;
      for(let j=0;j<fl.n;j++){ const bx=(head-j*10)|0, by=(fl.y+Math.sin(t/300+j)*2+(j%2)*3)|0, up=((t/90|0)+j)%2?0:2, c=mix(THEME.skyTop,C.cream,0.3);
        R(bx-3,by,2,1,c); R(bx-1,by-up,2,1,c); R(bx+1,by,2,1,c); } }
    haze(0,FAR_BASE-16,W,20, C.haze, 0.5);                         // aerial perspective at the skyline base
  }
  function eiffel(x:number,base:number,h:number){ const col=mix(mix('#262a38','#15182a',0.4), C.haze, 0.4);
    for(let i=0;i<h;i+=4){ const p=i/h, half=Math.round(13-11*p); R(x-half,base-i-1,2,1,col); R(x+half-1,base-i-1,2,1,col); }
    R(x-1,base-h,2,h,col); R(x-1,base-h-4,2,4,col);
    for(const yy of [base-(h*0.3|0),base-(h*0.56|0)]) R(x-1,yy,2,1,mix(C.gold,'#fff',0.3)); }

  function drawBuildings(t:number){
    const tick=((t+900)/2800)|0;
    for(const b of BUILDINGS){ const topY=GROUND-b.h, body=b.stone, se=mix(body,'#000',0.16), hi=mix(body,'#fff',0.13);
      R(b.x,topY,b.w,b.h,body);
      // aging streaks + quoins
      for(let s=0;s<3;s++){ const sx=b.x+2+((hash(b.x+s)* (b.w-4))|0); A(0.12,()=>R(sx,topY+6,1,b.h-10,mix(body,'#000',0.5))); }
      R(b.x,topY,2,b.h,hi); R(b.x+b.w-2,topY,2,b.h,se); R(b.x,topY,b.w,1,hi);
      for(let f=1;f<b.floors;f++){ const yy=GROUND-f*19; R(b.x,yy,b.w,1,mix(se,'#fff',0.14)); R(b.x,yy+1,b.w,1,mix(se,'#000',0.2)); }
      if(b.drain) R(b.x+b.w-3,topY+2,1,b.h-4,mix(se,'#000',0.3));
      const gap=(b.w-6)/b.cols;
      for(const wd of b.wins){ const wx=(b.x+4+wd.c*gap)|0, wy=GROUND-(wd.f+1)*19+5, ww=6, wh=12;
        let warm=wd.warm0; if(wd.ph>0.86) warm=hash(wd.ph*57.3+tick*1.7)>0.5;
        if(warm){ A(0.10,()=>disc(wx+ww/2|0, wy+wh/2|0, 8, C.winWarm)); }          // glow spill
        R(wx-1,wy-1,ww+2,wh+2,C.iron);
        R(wx,wy,ww,wh, warm?C.winWarm:C.winCold);
        if(warm){ R(wx+1,wy+1,ww-2,4,C.winHi); A(0.5,()=>R(wx+1,wy+wh-3,ww-2,2,mix(C.winWarm,'#000',0.2))); }
        R(wx+ (ww/2|0),wy,1,wh,C.iron); R(wx,wy+(wh/2|0),ww,1,C.iron);             // cross mullion
        if(wd.shut){ R(wx-2,wy-1,1,wh+2,mix(se,'#000',0.1)); R(wx+ww+1,wy-1,1,wh+2,mix(se,'#000',0.1)); } // shutters
        if(wd.box && wd.f<b.floors-1){ R(wx-1,wy+wh,ww+2,2,mix('#5a4326','#000',0.1)); R(wx,wy+wh-1,2,1,C.awn[2]); R(wx+3,wy+wh-1,2,1,mix(C.awn[2],'#fff',0.2)); }
        if(b.bal && wd.f===b.floors-2){ R(wx-2,wy+wh-1,ww+4,1,C.iron); for(let k=0;k<ww+2;k+=2) R(wx-1+k,wy+wh-1,1,3,C.iron); }
      }
      // mansard roof + dormers + chimney pots + rooftop props
      R(b.x-1,topY-8,b.w+2,8,C.zinc); R(b.x-1,topY-8,b.w+2,1,C.zincHi); R(b.x-1,topY,b.w+2,1,mix(C.zinc,'#000',0.4));
      for(let dx=5;dx<b.w-6;dx+=11){ R(b.x+dx,topY-6,4,5,mix(C.zinc,'#000',0.2)); R(b.x+dx+1,topY-5,2,3,mix(C.winWarm,'#000',0.35)); }
      for(let p=0;p<b.roof.pots;p++){ const px=b.x+6+p*7; R(px,topY-12,3,5,'#7a4a30'); R(px,topY-13,3,1,'#9c6a3a'); }
      if(b.roof.anten){ R(b.x+b.w-10,topY-18,1,10,C.iron); R(b.x+b.w-13,topY-18,7,1,C.iron); R(b.x+b.w-7,topY-19,1,1,mix(C.neon,'#fff',0.3)); }
      if(b.roof.tank){ R(b.x+8,topY-14,8,6,mix(C.iron,'#3a2e28',0.5)); R(b.x+9,topY-16,6,2,mix(C.iron,'#000',0.2)); }
      // storefront
      if(b.shop) storefront(b, topY);
    }
    R(0,GROUND,W,1,'#0b0c12');
  }
  function storefront(b:typeof BUILDINGS[number], topY:number){ const sy=GROUND-17, aw=b.awn;
    R(b.x+2,sy,b.w-4,17,mix('#14151c','#000',0.1));                 // dark glass
    A(0.9,()=>R(b.x+3,sy+2,b.w-6,11,mix(C.winWarm,'#000',0.4)));    // warm interior
    for(let i=0;i<Math.max(2,(b.w-6)/5|0);i++) R(b.x+3+i*2,sy+4,1,7,mix('#14151c','#000',0.2)); // silhouettes in window
    for(let i=0;i*6<b.w-4;i++) R(b.x+2+i*6,sy-6,6,6, i%2?aw:mix(aw,C.cream,0.55));               // striped awning
    R(b.x+2,sy-7,b.w-4,1,mix(aw,'#000',0.3)); R(b.x+2,sy,b.w-4,1,mix(aw,'#000',0.4));
    // type-specific sign / neon
    if(b.shop==='pharm'){ const cx=b.x+b.w/2|0; R(cx-1,sy-13,2,5,C.awn[2]); R(cx-2,sy-11,5,2,C.awn[2]); A(0.25,()=>disc(cx+1|0,sy-11,5,'#59e0a0')); }
    else if(b.shop==='bar'){ const nx=b.x+4, ny=sy-13; A(0.3,()=>disc(nx+6,ny+2,8,C.neon)); R(nx,ny,b.w-8,5,mix(C.ink,C.neon,0.3)); R(nx+1,ny+1,b.w-10,1,mix(C.neon,'#fff',0.4)); }
    else { const col=b.shop==='boul'?C.gold:C.cream; R(b.x+4,sy-12,b.w-8,5,mix('#101119','#000',0.1)); R(b.x+6,sy-10,b.w-12,1,mix(col,'#000',0.1)); R(b.x+6,sy-9,((b.w-12)*0.6)|0,1,mix(col,'#000',0.3)); }
    // warm light spilling onto the pavement
    A(0.12,()=>{ for(let i=0;i<b.w-4;i++) R(b.x+2+i, GROUND+1, 1, 3+ (hash(b.x+i)*3|0), C.winWarm); });
  }

  function drawStreet(t:number){
    // wet cobble
    vgrad(0,GROUND,W,STREET_H+8, C.cobbleWet,'#0f0d10',4);
    const rp=mulberry(99);
    for(let i=0;i<150;i++){ const x=(rp()*W)|0,y=GROUND+2+(rp()*STREET_H)|0; R(x,y,2,1, rp()<0.5?mix(C.cobbleWet,'#fff',0.06):mix(C.cobbleWet,'#000',0.4)); }
    for(const px of PUDDLES){ const py=GROUND+STREET_H-6-(hash(px)*6|0); A(0.5,()=>R(px-6,py,13,3,'#0c0e14')); R(px-4,py+1,8,1,mix(C.rimCool,'#000',0.4)); } // puddles
    // reflections of shops + lamps on the wet ground
    for(const x of LAMPS) reflect(x, GROUND+6, 20, C.rimWarm);
    // depth fog separating the street plane
    haze(0,GROUND-6,W,10,C.haze,0.4);
    garland(16,GROUND-82,82,GROUND-66,8,t); garland(116,GROUND-78,182,GROUND-90,7,t+40);
    for(const x of TREES) tree(x,GROUND+4);
    for(const c of CLUTTER) clutter(c,t);
    for(const x of LAMPS) lamp(x,GROUND+6);
    for(const p of PEDS) pedestrian(p,t);
  }
  function tree(x:number,y:number){ R(x-1,y-15,2,15,'#4a3826'); disc(x,y-20,8,mix(C.awn[2],'#000',0.35)); disc(x-3,y-17,6,mix(C.awn[2],'#000',0.15)); disc(x+3,y-24,5,mix(C.awn[2],C.cream,0.1)); A(0.2,()=>disc(x+2,y-26,3,C.cream)); }
  function lamp(x:number,y:number){ glow(x,y-30,14,mix('#3a3022',C.rimWarm,0.6)); R(x-1,y-32,2,32,'#2a302c'); R(x-1,y-32,1,32,mix('#2a302c',C.cream,0.14));
    for(const s of [-1,1]){ R(x,y-32,s*5,1,'#2a302c'); R(x+s*5-1,y-34,2,3,mix(C.gold,'#fff',0.5)); } R(x-2,y-34,4,2,mix(C.gold,'#fff',0.5)); }
  function bench(x:number,y:number){ R(x-10,y-3,20,2,'#6b4f30'); R(x-10,y-9,20,2,mix('#6b4f30','#000',0.25)); R(x-9,y-1,1,5,'#2a2420'); R(x+8,y-1,1,5,'#2a2420'); }
  function clutter(c:{t:string;x:number},t:number){ const g=GROUND+STREET_H-8;
    if(c.t==='bollard'){ R(c.x-1,g-6,3,8,'#2c2f36'); R(c.x-1,g-7,3,1,mix(C.gold,'#000',0.2)); }
    else if(c.t==='bin'){ R(c.x-3,g-8,6,9,'#2f3a34'); R(c.x-3,g-9,6,1,'#3f4a44'); R(c.x-2,g-6,4,1,mix('#2f3a34','#000',0.3)); }
    else if(c.t==='bike'){ R(c.x-7,g-3,14,1,'#20242b'); A(1,()=>{disc(c.x-6,g-1,3,'#15181e');disc(c.x+6,g-1,3,'#15181e');}); R(c.x-6,g-1,1,1,C.cobble); R(c.x+6,g-1,1,1,C.cobble); R(c.x-6,g-7,12,1,'#3a4452'); R(c.x,g-7,1,6,'#3a4452'); }
    else if(c.t==='bin'){}
    else if(c.t==='manhole'){ R(c.x-4,g+2,8,2,'#1c1f26'); steam(c.x,g,t); }
    else if(c.t==='kiosk'){ R(c.x-9,GROUND+6,18,STREET_H-12,'#24302c'); R(c.x-9,GROUND+4,18,3,mix('#24302c','#000',0.3)); A(0.85,()=>R(c.x-7,GROUND+10,14,10,mix(C.winWarm,'#000',0.4)));
      for(let i=0;i<4;i++) R(c.x-6+i*4,GROUND+11,3,7,[C.awn[0],C.awn[1],C.gold,C.awn[2]][i]); R(c.x-10,GROUND+3,20,2,'#394a44'); R(c.x-1,GROUND-2,2,5,mix(C.gold,'#000',0.2)); }
  }
  function steam(x:number,y:number,t:number){ for(let i=0;i<3;i++){ const ph=((t*0.03+i*0.37)%1), yy=y-(ph*16|0), rr=1+(ph*3|0), xx=x+Math.round(Math.sin(ph*6.2+i)*2); A(0.18*(1-ph),()=>disc(xx,yy,rr,C.rimCool)); } }
  function garland(x1:number,y1:number,x2:number,y2:number,n:number,t:number){ let px:[number,number]|null=null;
    for(let i=0;i<=n;i++){ const u=i/n,x=Math.round(lerp(x1,x2,u)),y=Math.round(lerp(y1,y2,u)+Math.sin(u*Math.PI)*8);
      if(px){ const st=Math.max(Math.abs(x-px[0]),Math.abs(y-px[1])); for(let s=0;s<=st;s++) R(Math.round(lerp(px[0],x,s/st)),Math.round(lerp(px[1],y,s/st)),1,1,mix(C.iron,C.cream,0.2)); }
      px=[x,y]; const tw=reduce?1:(0.55+0.45*(Math.sin(t/260+i)>0?1:0)); A(0.3*tw,()=>disc(x,y,3,mix(C.winWarm,C.gold,0.3))); R(x,y,1,1,mix(C.winWarm,'#fff',0.5)); } }

  function pedestrian(p:typeof PEDS[number],t:number){ const span=W+16, x=(((((p.base+t*p.spd*0.001*p.dir)%1)+1)%1)*span-8)|0, y=p.y,s=p.sc,dir=p.dir;
    const w=Math.round(5*s), bodyH=Math.round(11*s), headH=Math.round(5*s), step=reduce?0:(Math.floor(t/240+p.base*9)%2);
    A(0.5,()=>R(x-w,y,w*2,1,'#07080c'));
    R(x-2,y-4,2,5,'#141821'); R(x+1,y-4,2,5,'#141821'); R(step?x-3:x+2,y-1,2,2,'#141821');
    R(x-w,y-4-bodyH,w*2,bodyH,p.coat); R(x-w,y-4-bodyH,w*2,2,mix(p.coat,'#fff',0.12)); R(x-w,y-4-bodyH,1,bodyH,mix(p.coat,'#000',0.3));
    A(0.4,()=>R(x+(dir>0?w-1:-w),y-3-bodyH,1,bodyH-2,C.rimCool));               // cool rim from sky
    R(x-2,y-4-bodyH-headH,4,headH,p.head);
    R(dir>0?x+w-1:x-w,y-2-bodyH,1,Math.round(6*s),mix(p.coat,'#000',0.2));
    if(p.umb){ const uc=[C.awn[0],C.awn[1],C.teal,C.awn[3]][(p.base*4)|0], uy=y-4-bodyH-headH-3;
      R(x,uy,1,headH+2,'#20242b'); for(let k=-5;k<=5;k++) R(x+k,uy-(Math.max(0,3-Math.abs(k)*0.5)|0),1,2,k%2?uc:mix(uc,'#000',0.22)); R(x-6,uy,13,1,mix(uc,'#000',0.3)); }
    if(p.dog){ const dx=x+(dir>0?10:-10); A(0.5,()=>R(dx-3,y,6,1,'#07080c')); R(dx-3,y-3,6,3,'#2e2620'); R(dx+(dir>0?2:-3),y-5,3,3,'#2e2620'); R(dx-3,y-1,1,1,'#2e2620'); R(dx+2,y-1,1,1,'#2e2620'); A(0.5,()=>{const lx=x+(dir>0?w:-w); for(let i=0;i<8;i++) R(lerp(lx,dx,i/8)|0, lerp(y-7,y-4,i/8)|0,1,1,'#3a3f48');}); } }

  // ---------- LAYER 5 · sports площадка ----------
  function drawSports(t:number){
    vgrad(0,SPORTS_TOP,W,H-SPORTS_TOP, C.rubber,'#120d10',4); R(0,SPORTS_TOP,W,1,mix(C.rubber,'#000',0.4));
    const rp=mulberry(55); for(let i=0;i<90;i++){ const x=(rp()*W)|0,y=SPORTS_TOP+4+(rp()*(H-SPORTS_TOP-6))|0; R(x,y,1,1, rp()<0.5?mix(C.rubber,'#fff',0.05):mix(C.rubber,'#000',0.4)); }
    rrect(10,SPORTS_TOP+8,W-20,H-SPORTS_TOP-16,mix(C.rubber,C.gold,0.16));
    glow(104,330,26,C.rimWarm); A(0.05,()=>disc(104,337,30,C.winWarm));   // warm meeting light pooled on the floor
    pullupRig(36,SPORTS_TOP+12); dipBars(168,SPORTS_TOP+26); bench(150,H-16);
    R(50,H-20,100,7,mix(C.awn[1],'#000',0.25)); R(50,H-20,100,2,mix(C.awn[1],C.cream,0.18)); // mat
    heroFox(66,H-10,t); boss(136,H-14,t);
    questMark(136,268,t);
  }
  function rrect(x:number,y:number,w:number,h:number,col:string){ R(x+1,y,w-2,1,col); R(x+1,y+h,w-2,1,col); R(x,y+1,1,h-2,col); R(x+w,y+1,1,h-2,col); }
  function pullupRig(x:number,y:number){ R(x-22,y,2,42,C.iron); R(x+22,y,2,42,C.iron); R(x-22,y,1,42,mix(C.iron,C.cream,0.2)); R(x-24,y,48,2,mix(C.iron,C.cream,0.22)); A(0.3,()=>R(x-24,y,48,1,C.rimWarm)); }
  function dipBars(x:number,y:number){ for(const s of [-1,1]){ R(x+s*8-1,y,2,24,C.iron); R(x+s*8-6,y-1,12,2,mix(C.iron,C.cream,0.2)); } }

  // hero — neutral muted body + the REAL fire-fox avatar as the head (app's big-head style)
  function heroFox(x:number,y:number,t:number){ const bob=reduce?0:(Math.sin(t/430)>0?0:1); y-=bob;
    const hood='#55605c',hoodSh='#3d4643',pant='#333b46', sc=0.8;
    A(0.5,()=>R(x-8,y,16,1,'#07080c'));                            // shadow
    R(x-6,y-6,5,6,pant); R(x+1,y-6,5,6,pant); R(x-6,y,5,2,'#1c2026'); R(x+1,y,5,2,'#1c2026');   // legs
    R(x-7,y-16,14,10,hood); R(x-7,y-16,3,10,hoodSh); R(x+5,y-16,2,10,mix(hood,'#fff',0.08)); R(x-7,y-16,14,2,mix(hood,'#fff',0.12)); R(x-1,y-15,2,8,hoodSh);
    A(0.35,()=>R(x+6,y-16,1,10,C.rimWarm)); A(0.3,()=>R(x-7,y-16,1,10,C.rimCool));
    drawAvatar(heroAv ?? AV_FOX, x, y-13-Math.round(32*sc), sc); }

  // district boss — broad neutral body + the REAL iron-bear avatar as the head
  function boss(x:number,y:number,t:number){ const br=reduce?0:(Math.sin(t/1100)>0?0:1); y-=br;
    const jkt='#2a2f39',jktSh='#1b1f27',jktHi='#3a4250', sc=0.95;
    A(0.55,()=>R(x-14,y,28,1,'#07080c'));                          // shadow
    R(x-9,y-8,7,8,'#171b23'); R(x+2,y-8,7,8,'#171b23'); R(x-6,y-8,1,8,'#262d38'); R(x+5,y-8,1,8,'#262d38'); R(x-9,y,7,2,'#0d0f14'); R(x+2,y,7,2,'#0d0f14');  // legs
    R(x-12,y-20,24,14,jkt); R(x-12,y-20,3,14,jktSh); R(x+9,y-20,3,14,jktHi); R(x-12,y-20,24,2,mix(jkt,'#fff',0.1)); R(x-1,y-20,2,14,jktSh);   // broad torso + zip
    R(x-9,y-10,5,5,mix(jkt,'#000',0.3)); R(x+4,y-10,5,5,mix(jkt,'#000',0.3));    // pockets
    R(x-16,y-19,5,12,jkt); R(x+11,y-19,5,12,jkt); R(x-16,y-8,5,2,jktSh); R(x+11,y-8,5,2,jktSh);  // shoulders/arms
    A(0.4,()=>{R(x+15,y-19,1,13,C.rimCool); R(x-16,y-19,1,13,C.rimCool);});
    drawAvatar(AV_BEAR, x, y-17-Math.round(32*sc), sc); }

  function questMark(x:number,y:number,t:number){ const bob=reduce?0:Math.round(Math.sin(t/300)*2); y+=bob;
    glow(x,y+7,10,C.gold); R(x-8,y,16,15,C.gold); R(x-8,y,16,2,mix(C.gold,'#fff',0.4)); rrect(x-8,y,16,15,C.ink);
    R(x-1,y+3,3,6,C.ink); R(x-1,y+10,3,2,C.ink);
    for(let i=0;i<5;i++) R(x-4+i,y+15+i,Math.max(1,8-2*i),1,C.gold); }

  function drawRain(t:number){ A(0.5,()=>{ for(const d of RAIN){ const y=(d.y+(reduce?0:t*d.sp*0.04))%(H+10);
    for(let k=0;k<d.len;k++) R((d.x-(k>>1))|0,(y+k)|0,1,1,mix('#223040','#9ec0de',0.6)); } });
    if(!reduce){ for(let i=0;i<6;i++){ const sx=(hash(i*7+((t/300)|0))*W)|0, sy=GROUND+STREET_H-4-(hash(i*3)*8|0); A(0.4,()=>{R(sx-1,sy,3,1,C.rimCool); R(sx,sy-1,1,1,C.rimCool);}); } } }

  function vignette(){ A(0.5,()=>{ disc(-10,-10,40,'#000'); disc(W+10,-10,40,'#000'); disc(-10,H+10,46,'#000'); disc(W+10,H+10,46,'#000'); }); }

  // ---------- compose ----------
  function draw(t:number){
    R(0,0,W,H,C.ink);
    drawSky(t);
    drawFarCity(t);
    drawBuildings(t);
    drawStreet(t);
    drawRain(t);
    drawSports(t);
    vignette();
  }

  draw(reduce?9000:t);
}
