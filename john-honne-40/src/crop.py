import sys, numpy as np
from PIL import Image
from rembg import remove, new_session
def bands(v,minlen=40,gap=8):
    out=[];s=None;g=0
    for k,x in enumerate(v):
        if x:
            if s is None:s=k
            g=0
        elif s is not None:
            g+=1
            if g>gap:
                if k-g-s>minlen: out.append((s,k-g))
                s=None;g=0
    if s is not None: out.append((s,len(v)))
    return out
su=new_session('u2net')
for path,start in [(sys.argv[1],1),(sys.argv[2],21)]:
    im=Image.open(path).convert('RGB'); W,H=im.size
    a=np.array(im.convert('L'))<238
    rows=bands(a.mean(1)>0.003); i=start
    print(path,len(rows))
    for r in rows:
        cols=bands(a[r[0]:r[1]].mean(0)>0.003); print(r,cols)
        for x0,x1 in cols:
            c=im.crop((max(0,x0-8),max(0,r[0]-8),min(W,x1+8),min(H,r[1]+8))); c.save(f'cells/c{i:02d}.png')
            remove(c,session=su,post_process_mask=True).save(f'cells/u2{i:02d}.png'); i+=1
sheet=Image.new('RGB',(5*360,8*330),(120,140,200))
for k in range(40):
    t=Image.open(f'cells/u2{k+1:02d}.png'); t.thumbnail((350,320)); sheet.paste(t,((k%5)*360,(k//5)*330),t)
sheet.save('u2sheet.png')
