import sys, os, zipfile, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
S=os.path.dirname(os.path.abspath(__file__)); OUT=sys.argv[1]; os.makedirs(OUT,exist_ok=True)
FONT=f'{S}/YuseiMagic-Regular.ttf'; EMO='/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf'
USE_GPT=os.environ.get('GPT','1')=='1'; GPT_SKIP={15}
K=2; W,H=370*K,320*K; M=10*K
C=dict(orange=(242,128,20),blue=(40,90,210),red=(228,48,72),green=(24,150,100),purple=(130,74,210),
       pink=(238,72,130),teal=(10,150,160),brown=(190,90,40),navy=(50,60,150))
# no, lines, honne, color, pos, tilt, emoji
D=[
(1,['了解です'],'（よくわかってない）','blue','top',-4,'❓'),
(2,['それな！'],None,'orange','top',5,'✨'),
(3,['知らんけど'],None,'purple','top',-3,None),
(4,['行けたら行く'],'（行かない）','green','bottom',-3,None),
(5,['既読スルー','じゃないよ'],None,'red','top',-4,'💦'),
(6,['今起きた'],None,'brown','bottom',3,'💤'),
(7,['何言ってるか','わからない'],None,'navy','top',-2,None),
(8,['考えとく'],'（考えない）','teal','top',-4,None),
(9,['あとでやる'],'（やらない）','orange','top',3,None),
(10,['大丈夫'],'（大丈夫じゃない）','pink','top',-3,'💦'),
(11,['帰りたい'],None,'blue','top',-4,None),
(12,['月曜日むり'],None,'purple','top',3,None),
(13,['明日から','本気出す'],None,'red','top',-4,'✨'),
(14,['定時なので'],None,'navy','top',-3,None),
(15,['会議','長くない？'],None,'teal','top',4,None),
(16,['金曜日','サイコー！'],None,'orange','left',-5,'🎉'),
(17,['もう無理'],None,'purple','top',-4,None),
(18,['がんばった','えらい'],None,'pink','left',4,'✨'),
(19,['ふとんから','出られない'],None,'brown','top',-3,None),
(20,['5分だけ…'],None,'blue','top',3,'💤'),
(21,['休日は','動かない'],None,'green','left',-4,None),
(22,['寒いのむり'],None,'blue','top',3,'⛄'),
(23,['今それどころ','じゃない'],None,'red','top',-3,None),
(24,['充電中'],None,'green','top',-4,'🔋'),
(25,['一口','ちょうだい'],'（全部）','orange','left',3,'✨'),
(26,['ダイエットは','明日から'],None,'pink','top',-3,None),
(27,['それおいしい','やつ？'],None,'brown','top',4,None),
(28,['別腹','です'],None,'purple','left',-4,None),
(29,['食べて','ない'],'（食べた）','teal','left',3,None),
(30,['かまって'],'（でも触らないで）','pink','top',-3,None),
(31,['べつに怒って','ないけど？'],None,'red','top',3,'💢'),
(32,['聞いてないフリ'],None,'navy','top',-3,None),
(33,['察して'],None,'purple','top',4,None),
(34,['今の聞かなかった','ことに'],None,'teal','top',-3,None),
(35,['ほめて！'],None,'orange','top',-4,'💕'),
(36,['うらや','ましい'],None,'green','left',-4,None),
(37,['気まずい'],None,'blue','left',3,'💦'),
(38,['言い訳','させて'],None,'brown','left',-4,None),
(39,['本音です'],None,'red','top',-3,None),
(40,['ここだけ','の話'],None,'purple','left',3,'🤫'),
]
def outline(L, r, col=(255,255,255), shadow=True):
    a=np.array(L.getchannel('A'))
    img=Image.fromarray(a).filter(ImageFilter.MaxFilter(3))
    big=Image.fromarray(a).filter(ImageFilter.GaussianBlur(r*0.5)).point(lambda v:255 if v>8 else 0).filter(ImageFilter.GaussianBlur(1.2))
    pad=Image.new('RGBA',L.size,(0,0,0,0))
    if shadow:
        sh=Image.new('RGBA',L.size,(60,50,70,0)); sh.putalpha(big.filter(ImageFilter.GaussianBlur(5)).point(lambda v:int(v*0.30)))
        pad.alpha_composite(sh,(0,4))
    base=Image.new('RGBA',L.size,col+(0,)); base.putalpha(big); pad.alpha_composite(base); pad.alpha_composite(L)
    return pad
def padimg(L,p):
    o=Image.new('RGBA',(L.width+2*p,L.height+2*p),(0,0,0,0)); o.alpha_composite(L,(p,p)); return o
def rounded_photo(cell):
    a=np.array(cell.convert('L')); ys,xs=np.where(a<238)
    # inner photo bbox: take rows/cols mostly non-white
    rows=np.where((a<238).mean(1)>0.6)[0]; cols=np.where((a<238).mean(0)>0.6)[0]
    box=(cols[0]+6,rows[0]+6,cols[-1]-5,rows[-1]-5); ph=cell.crop(box).convert('RGBA')
    m=Image.new('L',ph.size,0); ImageDraw.Draw(m).rounded_rectangle((0,0,ph.width-1,ph.height-1),radius=28,fill=255); ph.putalpha(m); return ph
def shape_photo(cell):
    from scipy import ndimage
    a=np.array(cell.convert('L'))<236
    a=ndimage.binary_closing(a,iterations=3); a=ndimage.binary_fill_holes(a); a=ndimage.binary_erosion(a,iterations=10)
    lab,n=ndimage.label(a); k=np.argmax(np.bincount(lab.ravel())[1:])+1; a=lab==k
    L=cell.convert('RGBA'); L.putalpha(Image.fromarray((a*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1))); return L
def dog_layer(i):
    if i in (4,36): L=rounded_photo(Image.open(f'{S}/cells/c{i:02d}.png').convert('RGB'))
    elif i==21: L=shape_photo(Image.open(f'{S}/cells/c21.png').convert('RGB'))
    elif i in (13,14) or i>20: L=Image.open(f'{S}/cells/u2{i:02d}.png').convert('RGBA')
    else: L=Image.open(f'{S}/cells/cut{i:02d}.png').convert('RGBA')
    a=np.array(L.getchannel('A')); a[a<40]=0; L.putalpha(Image.fromarray(a))
    L=L.crop(L.getbbox()); return L
def text_block(lines, honne, col):
    f=lambda s:ImageFont.truetype(FONT,s)
    maxw=W-2*M-30
    imgs=[]
    for ln in lines:
        size=150 if len(lines)==1 else 120
        while f(size).getlength(ln)>maxw: size-=4
        size=min(size,int(maxw/ max(1,len(ln))*1.05)) if len(ln)<=3 else size
        imgs.append([ln,size,col])
    if len(imgs)>1:
        m_=min(x[1] for x in imgs)
        for x in imgs: x[1]=min(x[1],int(m_*1.1))
    imgs=[(t,f(sz),c) for t,sz,c in imgs]
    if honne:
        s=72
        while f(s).getlength(honne)>maxw: s-=2
        imgs.append((honne,f(s),(70,70,80)))
    import random
    rend=[]
    for li,(t,ft,c) in enumerate(imgs):
        rnd=random.Random(hash(t)%9973)
        sw=max(8,int(ft.size*0.14)); bold=max(1,int(ft.size*0.025))
        chars=[]
        bold=max(1,int(ft.size*0.012))
        for ch in t:
            adv=ft.getlength(ch)
            cw,chh=int(adv)+2*sw+20,int(ft.size*1.4)+2*sw
            o=(sw+10,sw); ang=rnd.uniform(-6,6); dy=int(rnd.uniform(-0.05,0.05)*ft.size)
            wl=Image.new('RGBA',(cw,chh),(0,0,0,0)); ImageDraw.Draw(wl).text(o,ch,font=ft,fill=(255,255,255,255),stroke_width=sw+bold,stroke_fill=(255,255,255,255))
            cl=Image.new('RGBA',(cw,chh),(0,0,0,0)); ImageDraw.Draw(cl).text(o,ch,font=ft,fill=c+(255,),stroke_width=bold,stroke_fill=c+(255,))
            wl=wl.rotate(ang,resample=Image.BICUBIC,center=(cw/2,chh/2)); cl=cl.rotate(ang,resample=Image.BICUBIC,center=(cw/2,chh/2))
            chars.append((wl,cl,adv,dy))
        tot=int(sum(x[2] for x in chars)*0.97)+chars[0][0].width
        hh=max(x[0].height for x in chars)+int(ft.size*0.12)
        line=Image.new('RGBA',(tot,hh),(0,0,0,0))
        for layer in (0,1):
            x=0
            for ch in chars:
                line.alpha_composite(ch[layer],(int(x),max(0,ch[3]+int(ft.size*0.06)))); x+=ch[2]*0.97
        line=line.crop(line.getbbox()); rend.append(line)
    tw=max(r.width for r in rend); th=sum(r.height for r in rend)-28*(len(rend)-1)
    blk=Image.new('RGBA',(tw,th),(0,0,0,0)); y=0
    for k,r in enumerate(rend):
        x=(tw-r.width)//2 if k<len(lines) else (tw-r.width)//2
        blk.alpha_composite(r,(x,y)); y+=r.height-28
    sh=Image.new('RGBA',blk.size,(40,30,60,0)); sh.putalpha(blk.getchannel('A').filter(ImageFilter.GaussianBlur(4)).point(lambda v:int(v*0.25)))
    o=Image.new('RGBA',(blk.width,blk.height+6),(0,0,0,0)); o.alpha_composite(sh,(0,5)); o.alpha_composite(blk)
    return o
def emoji(ch,size):
    ft=ImageFont.truetype(EMO,109); im=Image.new('RGBA',(160,160),(0,0,0,0))
    ImageDraw.Draw(im).text((10,10),ch,font=ft,embedded_color=True); im=im.crop(im.getbbox())
    im=im.resize((size,int(size*im.height/im.width)),Image.LANCZOS)
    return outline(padimg(im,14),10,shadow=False)
def fit(L,bw,bh,maxs=10):
    s=min(bw/L.width,bh/L.height,maxs); return L.resize((max(1,int(L.width*s)),max(1,int(L.height*s))),Image.LANCZOS)
def make(i,lines,honne,col,pos,tilt,emo):
    dog=outline(padimg(dog_layer(i),30),18)
    dog=dog.crop(dog.getbbox())
    GPTI=False
    gp=f'{S}/gpt/txt/t{i:02d}.png'
    if USE_GPT and os.path.exists(gp) and i not in GPT_SKIP:
        g=Image.open(gp).convert('RGBA'); g=g.resize((g.width*3,g.height*3),Image.LANCZOS)
        tb=outline(padimg(g,24),14)
        tb=tb.crop(tb.getbbox())
        emo=None; GPTI=True
        if i not in (4,): pos='left' if tb.height/tb.width>0.62 else 'top'
    else:
        tb=text_block(lines,honne,C[col]).rotate(tilt,expand=True,resample=Image.BICUBIC)
    if pos=='left':
        canvas=Image.new('RGBA',(W,H),(0,0,0,0))
        d=fit(dog,(W-2*M)*0.54,(H-2*M)*0.96); canvas.alpha_composite(d,(W-M-d.width,(H-d.height)//2))
        if emo:
            e=emoji(emo,70); canvas.alpha_composite(e,(max(M,W-M-d.width-e.width//2-10),M+30))
        if i in (21,36):
            t=fit(tb,max(W-2*M-d.width+30,(W-2*M)*0.45),(H-2*M)*0.8,1.0); canvas.alpha_composite(t,(M,(H-t.height)//2+10))
        else:
            t=fit(tb,(W-2*M)*0.66,(H-2*M)*0.75,1.0); canvas.alpha_composite(t,(M,(H-t.height)//2 if GPTI else H-M-t.height-8))
        c=canvas.crop(canvas.getbbox()); c=fit(c,W-2*M,H-2*M,1.0)
        o=Image.new('RGBA',(W,H),(0,0,0,0)); o.alpha_composite(c,((W-c.width)//2,(H-c.height)//2))
        return o.resize((370,320),Image.LANCZOS)
    tb=fit(tb,W-2*M,(H-2*M)*0.55,1.0)
    th=tb.height
    overlap=int(th*{16:0.15,18:0.05,10:0.3,40:0.6}.get(i,0.40 if i<=20 else 0.30))
    area_h=H-2*M-th+overlap
    d=fit(dog,W-2*M,area_h)
    canvas=Image.new('RGBA',(W,H),(0,0,0,0))
    if pos=='top':
        dy=H-M-d.height; ty=max(M,dy-th+overlap)
    else:
        dy=M; ty=min(H-M-th,dy+d.height-overlap)
    dx=(W-d.width)//2
    canvas.alpha_composite(d,(dx,dy))
    if emo:
        e=emoji(emo,70)
        ex = min(W-M-e.width, dx+d.width-e.width//2) if i%2 else max(M, dx-e.width//2)
        ey = dy+d.height//3
        canvas.alpha_composite(e,(int(ex),int(ey)))
    canvas.alpha_composite(tb,((W-tb.width)//2,int(ty)))
    bb=canvas.getbbox()
    # recentre & ensure margin
    c=canvas.crop(bb); c=fit(c,W-2*M,H-2*M,1.0)
    o=Image.new('RGBA',(W,H),(0,0,0,0)); o.alpha_composite(c,((W-c.width)//2,(H-c.height)//2))
    return o.resize((370,320),Image.LANCZOS)
for row in D:
    make(*row).save(f'{OUT}/{row[0]:02d}.png',optimize=True)
# main / tab from 04 dog+text
m=make(*D[3]); 
def sq(im,w,h,mg):
    c=im.crop(im.getbbox()); c=fit(c,w-2*mg,h-2*mg,1.0); o=Image.new('RGBA',(w,h),(0,0,0,0)); o.alpha_composite(c,((w-c.width)//2,(h-c.height)//2)); return o
sq(m,240,240,10).save(f'{OUT}/main.png',optimize=True)
t=outline(padimg(rounded_photo(Image.open(f'{S}/cells/c04.png').convert('RGB')),20),14); t=t.crop(t.getbbox())
sq(t,96,74,2).save(f'{OUT}/tab.png',optimize=True)
zp=f'{OUT}/fuku-honne-40-line-stamps.zip'
with zipfile.ZipFile(zp,'w',zipfile.ZIP_DEFLATED) as z:
    for k in range(len(D)): z.write(f'{OUT}/{k+1:02d}.png',f'{k+1:02d}.png')
    z.write(f'{OUT}/main.png','main.png'); z.write(f'{OUT}/tab.png','tab.png')
cols=5; n=len(D); rows=(n+cols-1)//cols
sheet=Image.new('RGB',(cols*390+20,rows*340+20),(140,171,216))
for k in range(n):
    im=Image.open(f'{OUT}/{k+1:02d}.png'); sheet.paste(im,(20+(k%cols)*390,20+(k//cols)*340),im)
sheet.save(f'{OUT}/preview.png'); print('ok')
