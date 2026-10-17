// SlideReady gösteri efektleri. Hepsi render(t)'nin saf parçasıdır: aynı t her zaman aynı kareyi verir.
// Her efekt PowerPoint'in çizdiği katmandan beslenir ve iş bitince katmanın kendisine devreder (son kare değişmez).
// Gölgelendirici kodları SlideReady'ye aittir (gl-transitions vb. yalnızca fikir olarak örnek alındı).
const FX=!!STYLE.fx, PAL=STYLE.palette||{base:[.03,.05,.25],accent:[1,.75,.25],light:[.25,.4,1]};
const FX_READY=[];
const pxPerUnit=()=>innerWidth/VB[0];
function rng(seed){ return ()=>{ seed|=0; seed=seed+0x6D2B79F5|0; let t=Math.imul(seed^seed>>>15,1|seed);
  t=t+Math.imul(t^t>>>7,61|t)^t; return ((t^t>>>14)>>>0)/4294967296; }; }
// Analitik yay (kütle 1): yerine yaylanarak oturur; 2 sn sonra tam olarak 1
function spring(u,k=170,c=18){
  if(u<=0) return 0; if(u>=2) return 1;
  const w0=Math.sqrt(k), z=c/(2*w0);
  if(z>=1) return 1-Math.exp(-w0*u)*(1+w0*u);
  const wd=w0*Math.sqrt(1-z*z);
  return 1-Math.exp(-z*w0*u)*(Math.cos(wd*u)+z*w0/wd*Math.sin(wd*u));
}
const smooth=(a,b,x)=>{ x=clamp((x-a)/(b-a)); return x*x*(3-2*x); };
const loadImg=src=>new Promise(ok=>{ const i=new Image(); i.onload=()=>ok(i); i.onerror=()=>ok(null); i.src=src; });

function foCanvas(parent,x,y,w,h,before=null,res=1){
  const fo=el('foreignObject',{x,y,width:w,height:h}), cv=document.createElement('canvas');
  const S=pxPerUnit()*res; cv.width=Math.max(2,Math.round(w*S)); cv.height=Math.max(2,Math.round(h*S));
  cv.style.cssText='width:100%;height:100%;display:block';
  fo.appendChild(cv); parent.insertBefore(fo,before); return {fo,cv};
}

// --- WebGL: tam ekran dörtgen + parça gölgelendirici ---
const NOISE=`
float h21(vec2 p){ p=fract(p*vec2(123.34,456.21)); p+=dot(p,p+45.32); return fract(p.x*p.y); }
float vn(vec2 p){ vec2 i=floor(p), f=fract(p); f=f*f*(3.-2.*f);
  return mix(mix(h21(i),h21(i+vec2(1,0)),f.x),mix(h21(i+vec2(0,1)),h21(i+vec2(1,1)),f.x),f.y); }
float fbm(vec2 p){ float s=0., a=.5; for(int i=0;i<5;i++){ s+=a*vn(p); p=p*2.03+vec2(1.7,9.2); a*=.5; } return s; }`;
function glSetup(cv,fs){
  const gl=cv.getContext('webgl',{premultipliedAlpha:true,preserveDrawingBuffer:true,antialias:false});
  if(!gl) return null;
  const sh=(type,src)=>{ const s=gl.createShader(type); gl.shaderSource(s,src); gl.compileShader(s);
    if(!gl.getShaderParameter(s,gl.COMPILE_STATUS)) console.error(gl.getShaderInfoLog(s)); return s; };
  const p=gl.createProgram();
  gl.attachShader(p,sh(gl.VERTEX_SHADER,'attribute vec2 a;varying vec2 uv;void main(){uv=a*.5+.5;uv.y=1.-uv.y;gl_Position=vec4(a,0,1);}'));
  gl.attachShader(p,sh(gl.FRAGMENT_SHADER,'precision highp float;varying vec2 uv;'+NOISE+fs)); gl.linkProgram(p); gl.useProgram(p);
  const b=gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER,b);
  gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,1,1]),gl.STATIC_DRAW);
  const loc=gl.getAttribLocation(p,'a'); gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc,2,gl.FLOAT,false,0,0);
  const U={}; const u=n=>U[n]??(U[n]=gl.getUniformLocation(p,n));
  return {gl, set:(n,...v)=>{ const l=u(n); if(v.length===1) gl.uniform1f(l,v[0]); else gl[`uniform${v.length}f`](l,...v); },
    tex:(n,img,unit)=>{ const t=gl.createTexture(); gl.activeTexture(gl.TEXTURE0+unit); gl.bindTexture(gl.TEXTURE_2D,t);
      gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL,true);
      gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,img);
      for(const [k,v] of [[gl.TEXTURE_MIN_FILTER,gl.LINEAR],[gl.TEXTURE_MAG_FILTER,gl.LINEAR],[gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE],[gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE]]) gl.texParameteri(gl.TEXTURE_2D,k,v);
      gl.uniform1i(u(n),unit); },
    draw:()=>{ gl.viewport(0,0,cv.width,cv.height); gl.clearColor(0,0,0,0); gl.clear(gl.COLOR_BUFFER_BIT); gl.drawArrays(gl.TRIANGLE_STRIP,0,4); } };
}

// --- Aurora + ışık sızması: slaydın kendi renklerinden akan ışık; okuma payından önce tamamen söner ---
const AURORA=`uniform float t,a,L,ar; uniform vec3 c1,c2,c3;
void main(){ vec2 p=vec2(uv.x*ar,uv.y)*1.5;
  float f=fbm(p+vec2(t*.10,-t*.04)+1.3*fbm(p*1.6-vec2(t*.07,t*.03)));
  float r=pow(.5+.5*sin(p.x*2.1+f*4.5+t*.45),5.);
  vec3 col=mix(c1,c2,smoothstep(.25,.85,f))+c3*r*.55;
  float al=a*(.55*smoothstep(.35,.95,f)+.35*r)*(.35+.65*smoothstep(1.1,.1,uv.y));
  float d=length((uv-vec2(-.05+.35*L,.15))*vec2(ar*.8,1.));
  float lk=L*(1.-L)*4.*exp(-d*d*3.2);
  vec3 warm=mix(c3,vec3(1.,.62,.32),.55);
  gl_FragColor=vec4(col*al+warm*lk*.9, clamp(al+lk*.6,0.,1.)); }`;
function aurora(){
  const amt=STYLE.aurora||0; if(!FX||!amt) return null;
  const g=el('g'); document.getElementById('sr-bg').after(g);
  const {fo,cv}=foCanvas(g,0,0,VB[0],VB[1],null,.5); fo.style.mixBlendMode='screen';
  const G=glSetup(cv,AURORA); if(!G) return null;
  const end=Math.max(1.2,Math.min(CAM.end||3,(STYLE.still||4)-.3)), t0=STYLE.cont?STYLE.cont.dur*.6:0;
  G.set('c1',...PAL.light); G.set('c2',...PAL.light.map((v,i)=>v*.5+PAL.accent[i]*.5)); G.set('c3',...PAL.accent);
  G.set('ar',VB[0]/VB[1]);
  return t=>{ const u=t-t0, env=smooth(0,.9,u)*(1-smooth(end*.55,end,t)), L=STYLE.leak?clamp((u-.1)/1.3):0;
    const lk=L>0&&L<1;
    if(env<=0.001&&!lk){ fo.setAttribute('display','none'); return; }
    fo.removeAttribute('display'); G.set('t',t); G.set('a',amt*env); G.set('L',lk?L:0); G.draw(); };
}

// --- Slaytlar arası süreklilik: önceki slaydın son karesi, değişen yerlerde bükülüp gürültüyle eriyerek bu slayda
// açılır. Ortak pikseller (asıl slayttaki logo, şerit) bükülmez: yerinden kımıldamadan kalır. ---
const CONT=`uniform sampler2D A,B; uniform float p,kind; uniform vec3 acc; uniform vec2 px;
void main(){ vec4 a0=texture2D(A,uv), b0=texture2D(B,uv);
  float diff=smoothstep(.03,.14,length(a0.rgb-b0.rgb));
  vec2 dir=kind<.5? (uv-vec2(.5)) : vec2(1.,.3)*.6;
  float w=p*p*diff; vec4 s=vec4(0.);
  for(int i=0;i<10;i++){ float k=float(i)/9.; s+=texture2D(A,uv-dir*w*(.18+.22*k)); }
  s/=10.; vec4 a=mix(a0,s,diff);
  float n=fbm(uv*vec2(px.x/px.y,1.)*3.2+3.);
  float th=p*1.35-n*.35;
  float al=1.-smoothstep(.0,1.,th);
  float e=exp(-pow((th-.5)*9.,2.))*diff*(1.-p);
  gl_FragColor=vec4(a.rgb*al+acc*e*.65, clamp(al+e*.4,0.,1.)); }`;
function continuity(){
  const C=STYLE.cont; if(!FX||!C) return null;
  const g=el('g'); svg.appendChild(g);
  const {fo,cv}=foCanvas(g,0,0,VB[0],VB[1]); const G=glSetup(cv,CONT); if(!G) return null;
  FX_READY.push(Promise.all([loadImg(C.prev),loadImg(C.to)]).then(([a,b])=>{ if(a&&b){ G.tex('A',a,0); G.tex('B',b,1); } }));
  G.set('kind',C.kind==='zoom'?0:1); G.set('acc',...PAL.accent); G.set('px',cv.width,cv.height);
  return t=>{ const p=clamp(t/C.dur);
    if(p>=1){ fo.setAttribute('display','none'); return; }
    fo.removeAttribute('display'); G.set('p',inout(p)); G.draw(); };
}

// --- Mürekkep açılışı: gürültü eşiği + yanık kenar + sönen UV bükülmesi; sonunda görselin kendisi ---
const INK=`uniform sampler2D T; uniform float p; uniform vec3 acc; uniform float ar;
void main(){ vec2 q=uv*vec2(ar,1.)*3.;
  vec2 d=(vec2(fbm(q+7.1),fbm(q+2.3))-.5)*.06*(1.-p);
  vec4 c=texture2D(T,uv+d);
  float n=fbm(q*1.3);
  float th=p*1.4-.2;
  float m=smoothstep(n-.05,n+.05,th);
  float e=exp(-pow((th-n)*22.,2.))*(1.-p)*c.a;
  gl_FragColor=vec4(c.rgb*m+acc*e*1.2, clamp(c.a*m+e*.8,0.,1.)); }`;
function ink(it){
  const im=[...it.g.querySelectorAll('image')].pop(); if(!im) return;
  const b=imageBox(im), {fo,cv}=foCanvas(it.g,b.x,b.y,b.w,b.h,im.nextSibling);
  const G=glSetup(cv,INK); if(!G) return;
  FX_READY.push(loadImg(im.getAttribute('href')).then(i=>i&&G.tex('T',i,0)));
  G.set('acc',...PAL.accent); G.set('ar',b.w/b.h);
  const T=1.3;
  it.fxRender=(t,u)=>{ const p=clamp(u/T), done=p>=1;
    it.g.style.opacity=u>0?1:0; it.blur(0);
    it.g.style.transform=done?'':`scale(${1.04-.04*out3(u/1.6)})`;
    im.setAttribute('opacity',done?1:0);
    if(done||u<=0){ fo.setAttribute('display','none'); return true; }
    fo.removeAttribute('display'); G.set('p',out3(p)); G.draw(); return true; };
}

// --- Parçacıklarla toplanma: öğe kendi piksellerinden örneklenmiş binlerce parçacıktan oluşur ---
function particles(it){
  const P=it.s.pts, n=P.n, R=rng(n*7919+P.area|0), T=1.9;
  const {fo,cv}=foCanvas(it.g.parentNode,0,0,VB[0],VB[1],it.g.nextSibling), ctx=cv.getContext('2d');
  const S=cv.width/VB[0], dot=Math.max(1.1,Math.sqrt(P.area/n)*1.25*S);
  const box=it.s.box||[it.s.x,it.s.y,it.s.x+it.s.w,it.s.y+it.s.h], cx=(box[0]+box[2])/2, cy=(box[1]+box[3])/2;
  const xs=[],ys=[],sx=[],sy=[],qx=[],qy=[],st=[],col=[];
  for(let i=0;i<n;i++){
    const x=P.xy[2*i], y=P.xy[2*i+1], gx=(R()+R()+R()-1.5)/1.5, gy=(R()+R()+R()-1.5)/1.5;
    const ox=cx-VB[0]*.62+gx*VB[0]*.10, oy=cy+VB[1]*.32+gy*VB[1]*.12;   // sol alttan gelen bir akım
    const mx=(ox+x)/2, my=(oy+y)/2, nx=-(y-oy), ny=x-ox, sw=-.35+(R()-.5)*.35; // aynı yöne kıvrılan yollar
    xs.push(x); ys.push(y); sx.push(ox); sy.push(oy); qx.push(mx+nx*sw); qy.push(my+ny*sw);
    st.push(.05+.6*((x-box[0])/Math.max(1,box[2]-box[0]))+.25*R());   // harfler soldan sağa dolar
    col.push(`rgb(${P.rgb[3*i]},${P.rgb[3*i+1]},${P.rgb[3*i+2]})`);
  }
  it.fxRender=(t,u)=>{
    const settle=smooth(T-.35,T,u);
    it.g.style.opacity=settle; it.g.style.transform=''; it.blur(0);
    if(u<=0||u>=T){ fo.setAttribute('display','none'); return true; }
    fo.removeAttribute('display'); ctx.clearRect(0,0,cv.width,cv.height);
    for(let i=0;i<n;i++){
      const q=clamp((u-st[i])/.95); if(q<=0) continue;
      const e=1-Math.pow(1-q,3), a=1-e, x=a*a*sx[i]+2*a*e*qx[i]+e*e*xs[i], y=a*a*sy[i]+2*a*e*qy[i]+e*e*ys[i];
      const fly=e<.85;                                   // uçarken toplamalı parıltı, varınca kendi rengi
      ctx.globalCompositeOperation=fly?'lighter':'source-over';
      ctx.globalAlpha=Math.min(1,q*4)*(1-settle)*(fly?.6:1); ctx.fillStyle=col[i];
      const s=dot*(1+1.4*(1-e)); ctx.fillRect(x*S-s/2,y*S-s/2,s,s);
    }
    ctx.globalAlpha=1; return true; };
}

// --- Odometre: her rakam kendi sütununda döner, kendi gecikmesiyle durur, hızla orantılı dikey hareket bulanıklığı ---
function odometer(it){
  const O=it.s.odo, g=it.g, imgs=[...g.querySelectorAll('image')];
  const fin=imgs.find(i=>!i.hasAttribute('display'))||imgs[imgs.length-1], fb=imageBox(fin);
  const y0=fb.y, H=fb.h;
  // sabit kısım: son görüntünün rakam sütunları dışındaki yeri (₺, %, M, ayraçlar)
  const cp=el('clipPath',{id:'sro'+(uid++),clipPathUnits:'userSpaceOnUse'});
  cp.appendChild(el('path',{'clip-rule':'evenodd',d:`M${fb.x-500},${y0-500}h${fb.w+1000}v${H+1000}h${-fb.w-1000}z`+
    O.cols.map(c=>`M${c.x0},${y0-500}H${c.x1}V${y0+H+500}H${c.x0}z`).join('')}));
  defs().appendChild(cp);
  const rest=set(fin.cloneNode(),{'clip-path':`url(#${cp.id})`,display:'none'}); rest.removeAttribute('data-n'); g.appendChild(rest);
  const m=O.cols.length;
  const cols=O.cols.map((c,j)=>{
    const ccp=el('clipPath',{id:'sro'+(uid++),clipPathUnits:'userSpaceOnUse'});
    ccp.appendChild(el('rect',{x:c.x0-60,y:y0,width:c.x1-c.x0+120,height:H})); defs().appendChild(ccp);
    const wrap=el('g',{'clip-path':`url(#${ccp.id})`,display:'none'}), inner=el('g'); wrap.appendChild(inner); g.appendChild(wrap);
    const ims=c.imgs.map(d=>{ const i=el('image',{x:d.x,y:d.y,width:d.w,height:d.h,preserveAspectRatio:'none',href:d.href,display:'none'});
      inner.appendChild(i); return i; });
    // sağdaki sütun daha çok döner ve daha geç durur
    return {wrap,inner,ims,blur:blurrer(inner,true),travel:c.d+10*Math.min(3,j+1),stop:1.0+.2*j};
  });
  it.odoRender=(t,u)=>{
    const done=u>=cols[cols.length-1].stop+.05;
    imgs.forEach(i=>i.setAttribute('display', done&&i===fin?'inline':'none'));
    rest.setAttribute('display',done||u<=0?'none':'inline');
    for(const c of cols){
      c.wrap.setAttribute('display',done||u<=0?'none':'inline'); if(done||u<=0) continue;
      const x=clamp(u/c.stop), pos=c.travel*out3(x), v=c.travel*3*Math.pow(1-x,2)/c.stop;   // basamak/sn
      const i=Math.floor(pos)%10, f=pos-Math.floor(pos), j=(i+1)%10;
      c.ims.forEach((im,k)=>{ const on=k===i||(k===j&&f>0.001);
        im.setAttribute('display',on?'inline':'none');
        if(on) im.style.transform=`translateY(${(k===i?-f:1-f)*H}px)`; });
      c.blur(Math.min(H*.1,v*H*.004));   // çıktıdaki hareket bulanıklığı bunun üstüne eklenir
    }
  };
}

// --- İki Gauss'lu ışık süzmesi (geniş hale + dar çekirdek), panelin saydamlığıyla maskeli ---
function sweepStops(gr,halo,core){
  const span=3*halo; gr.innerHTML='';
  for(let i=0;i<=16;i++){ const d=-span+2*span*i/16;
    const a=Math.min(1,.30*Math.exp(-d*d/(2*halo*halo))+.40*Math.exp(-d*d/(2*core*core)));
    gr.appendChild(el('stop',{offset:i/16,'stop-color':'#fff','stop-opacity':a.toFixed(3)})); }
  return span;
}

// --- Grafik: ilerleyen kenarda parlayan ışık ---
function chartEdge(it){
  const r=el('rect',{display:'none'}); r.style.mixBlendMode='screen';
  const id=uid++, gr=el('linearGradient',{id:'sre'+id,gradientUnits:'objectBoundingBox'});
  [[0,0],[.5,.55],[1,0]].forEach(([o,a])=>gr.appendChild(el('stop',{offset:o,'stop-color':`rgb(${PAL.accent.map(v=>v*255|0)})`,'stop-opacity':a})));
  if(it.s.chart==='column'){ set(gr,{x1:0,y1:0,x2:0,y2:1}); } defs().appendChild(gr); r.setAttribute('fill',`url(#sre${id})`);
  it.g.parentNode.insertBefore(r,it.g.nextSibling);
  it.edge=(u,p)=>{ const {x,y,w,h}=it.s, band=Math.max(w,h)*.05;
    if(u<=0||p>=.995){ r.setAttribute('display','none'); return; }
    r.removeAttribute('display'); r.setAttribute('opacity',1-p*p);
    if(it.s.chart==='column') set(r,{x:x,y:y+h-h*p-band/2,width:w,height:band});
    else set(r,{x:x+w*p-band/2,y:y,width:band,height:h}); };
}

function fxSetup(items){
  if(!FX) return [];
  const upd=[aurora(),continuity()].filter(Boolean);
  for(const it of items){
    if(it.s.fx==='particles'&&it.s.pts) particles(it);
    else if(it.s.fx==='ink') ink(it);
    if(it.s.kind==='number'&&it.s.odo) odometer(it);
    if(it.s.kind==='chart'&&it.s.chart!=='pie') chartEdge(it);
  }
  return upd;
}
