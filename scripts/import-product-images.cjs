// Chuyển ảnh sản phẩm (ảnh sàn TMĐT) sang WebP cho gallery trang chi tiết; dùng Chrome qua Playwright, không cần Pillow.
// Chạy: node scripts/import-product-images.cjs CS22 [CS23 ...]
// Nguồn: <PRODUCT_IMAGE_SOURCE>/<mã viết thường>/1.png, 2.png, ... (mặc định thư mục "Database Comfycare/Ảnh sản phẩm").
// Kết quả: assets/products/<MÃ>/gallery/<n>.webp (gốc), <n>-640.webp, <n>-160.webp. Ghi đè file cùng tên.
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'..');
const source=process.env.PRODUCT_IMAGE_SOURCE||'C:/Users/mrtua/OneDrive/Desktop/Database Comfycare/Ảnh sản phẩm';
const skus=process.argv.slice(2);
if(!skus.length){console.error('Cần ít nhất một mã, ví dụ: node scripts/import-product-images.cjs CS22');process.exit(1);}
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.CHROME_PATH||'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
 const page=await browser.newPage();
 const report={};
 for(const sku of skus){
  const dir=path.join(source,sku.toLowerCase());
  const files=fs.readdirSync(dir).filter(f=>/^\d+\.png$/i.test(f)).sort((a,b)=>parseInt(a)-parseInt(b));
  if(!files.length)throw new Error('Không có ảnh N.png trong '+dir);
  const out=path.join(root,'assets/products',sku,'gallery');fs.mkdirSync(out,{recursive:true});
  report[sku]=[];
  for(const file of files){
   const n=parseInt(file);
   const data=fs.readFileSync(path.join(dir,file)).toString('base64');
   const result=await page.evaluate(async({data})=>{
    const img=new Image();img.src='data:image/png;base64,'+data;await img.decode();
    const encode=width=>{const c=document.createElement('canvas');c.width=width;c.height=Math.round(img.naturalHeight*width/img.naturalWidth);
     const x=c.getContext('2d');x.imageSmoothingQuality='high';x.drawImage(img,0,0,c.width,c.height);return c.toDataURL('image/webp',0.84).split(',')[1];};
    return {width:img.naturalWidth,height:img.naturalHeight,full:encode(img.naturalWidth),medium:encode(640),thumb:encode(160)};
   },{data});
   for(const [suffix,key] of [['','full'],['-640','medium'],['-160','thumb']])
    fs.writeFileSync(path.join(out,`${n}${suffix}.webp`),Buffer.from(result[key],'base64'));
   report[sku].push({image:n,width:result.width,height:result.height});
  }
 }
 await browser.close();
 console.log(JSON.stringify(report));
})().catch(error=>{console.error(error);process.exit(1);});
