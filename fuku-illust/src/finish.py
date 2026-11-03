# usage: python3 finish.py <rawdir> <outdir>
import sys, os, zipfile
from PIL import Image, ImageFilter
raw, out = sys.argv[1:3]; os.makedirs(out, exist_ok=True)
def finish(L, ow, oh, margin, border):
    a=L.getchannel('A'); r=border*2
    big=a.filter(ImageFilter.GaussianBlur(r*0.55)).point(lambda v:255 if v>6 else 0).filter(ImageFilter.GaussianBlur(1.2))
    base=Image.new('RGBA',L.size,(255,255,255,0)); base.putalpha(big)
    sh=Image.new('RGBA',L.size,(70,50,40,0)); sh.putalpha(big.filter(ImageFilter.GaussianBlur(5)).point(lambda v:int(v*0.28)))
    comp=Image.new('RGBA',L.size,(0,0,0,0)); comp.alpha_composite(sh,(0,4)); comp.alpha_composite(base); comp.alpha_composite(L)
    comp=comp.crop(comp.getbbox())
    s=min((ow-2*margin)/comp.width,(oh-2*margin)/comp.height,0.5)
    comp=comp.resize((max(1,round(comp.width*s)),max(1,round(comp.height*s))),Image.LANCZOS)
    o=Image.new('RGBA',(ow,oh),(0,0,0,0)); o.alpha_composite(comp,((ow-comp.width)//2,(oh-comp.height)//2)); return o
names=sorted([f for f in os.listdir(raw) if f.startswith('raw')], key=lambda f:int(f[3:-4]))
n=len(names)-2
for i in range(n): finish(Image.open(f'{raw}/raw{i}.png').convert('RGBA'),370,320,10,9).save(f'{out}/{i+1:02d}.png',optimize=True)
finish(Image.open(f'{raw}/raw{n}.png').convert('RGBA'),240,240,10,9).save(f'{out}/main.png',optimize=True)
finish(Image.open(f'{raw}/raw{n+1}.png').convert('RGBA'),96,74,2,6).save(f'{out}/tab.png',optimize=True)
zp=f'{out}/fuku-illust-line-stamps.zip'
with zipfile.ZipFile(zp,'w',zipfile.ZIP_DEFLATED) as z:
    for i in range(n): z.write(f'{out}/{i+1:02d}.png',f'{i+1:02d}.png')
    z.write(f'{out}/main.png','main.png'); z.write(f'{out}/tab.png','tab.png')
cols=4; rows=(n+cols-1)//cols
sheet=Image.new('RGB',(cols*390+20,rows*340+20),(140,171,216))
for i in range(n):
    im=Image.open(f'{out}/{i+1:02d}.png'); sheet.paste(im,(20+(i%cols)*390,20+(i//cols)*340),im)
sheet.save(f'{out}/preview.png'); print('done',n)
