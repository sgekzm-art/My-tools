// usage: node render.js <font.ttf> <outdir>
const {chromium}=require('playwright'); const fs=require('fs'); const path=require('path');
(async()=>{
  const [font,out]=process.argv.slice(2); fs.mkdirSync(out,{recursive:true});
  const html=fs.readFileSync(path.join(__dirname,'fuku.html'),'utf8').replace('FONT_URL','file://'+path.resolve(font));
  const tmp=path.join(out,'_page.html'); fs.writeFileSync(tmp,html);
  const b=await chromium.launch(); const p=await b.newPage({viewport:{width:1500,height:1300}});
  const errs=[]; p.on('pageerror',e=>errs.push(e.message));
  await p.goto('file://'+path.resolve(tmp)); await p.evaluate(()=>document.fonts.ready); await p.waitForTimeout(500);
  const n=await p.$$eval('svg',s=>s.length);
  for(let i=0;i<n;i++){ await (await p.$('#s'+i)).screenshot({path:path.join(out,`raw${i}.png`),omitBackground:true}); }
  fs.unlinkSync(tmp); console.log('rendered',n,errs); await b.close();
})();
