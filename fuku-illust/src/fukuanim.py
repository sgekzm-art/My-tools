import math, os, sys
src=open('fukumake3.py').read()
exec(src[:src.index("outs=[]")])
from PIL import Image, ImageFilter, ImageOps
OUTA='/home/user/My-tools/fuku-anim-sample'; os.makedirs(OUTA,exist_ok=True)
def bordered(L,border=7):
    a=L.getchannel('A'); r=border*S
    big=a.filter(ImageFilter.GaussianBlur(r*0.55)).point(lambda v:255 if v>6 else 0).filter(ImageFilter.GaussianBlur(1.2))
    base=Image.new('RGBA',L.size,(255,255,255,0)); base.putalpha(big)
    sh=Image.new('RGBA',L.size,(70,50,40,0)); sh.putalpha(big.filter(ImageFilter.GaussianBlur(5)).point(lambda v:int(v*0.28)))
    c=Image.new('RGBA',L.size,(0,0,0,0)); c.alpha_composite(sh,(0,4)); c.alpha_composite(base); c.alpha_composite(L); return c
def finish_frames(Ls,ow=320,oh=270,m=8):
    cs=[bordered(L) for L in Ls]
    bb=None
    for c in cs:
        b=c.getbbox(); bb=b if bb is None else (min(bb[0],b[0]),min(bb[1],b[1]),max(bb[2],b[2]),max(bb[3],b[3]))
    w,h=bb[2]-bb[0],bb[3]-bb[1]; s=min((ow-2*m)/w,(oh-2*m)/h)
    out=[]
    for c in cs:
        c=c.crop(bb).resize((round(w*s),round(h*s)),Image.LANCZOS)
        o=Image.new('RGBA',(ow,oh),(0,0,0,0)); o.alpha_composite(c,((ow-c.width)//2,(oh-c.height)//2)); out.append(o)
    return out
def xform(layer,center,scale=1,rot=0,dx=0,dy=0):
    if scale==1 and rot==0 and dx==0 and dy==0: return layer
    cx,cy=center
    t=layer.rotate(rot,resample=Image.BICUBIC,center=(cx,cy))
    if scale!=1:
        W2,H2=t.size; t2=t.resize((int(W2*scale),int(H2*scale)),Image.BICUBIC)
        c=Image.new('RGBA',t.size,(0,0,0,0)); c.alpha_composite(t2,(int(cx-cx*scale),int(cy-cy*scale))); t=c
    if dx or dy:
        c=Image.new('RGBA',t.size,(0,0,0,0)); c.alpha_composite(t,(int(dx),int(dy))); t=c
    return t
N=12
def save_apng(out,p,dur=100,loop=3):
    # shared 255-colour palette + index 255 = transparent
    W_,H_=out[0].size
    strip=Image.new('RGB',(W_,H_*len(out)))
    for i,f in enumerate(out):
        bg=Image.new('RGB',f.size,(255,255,255)); bg.paste(f,(0,0),f); strip.paste(bg,(0,i*H_))
    pal=strip.quantize(255,method=Image.Quantize.MEDIANCUT)
    fr=[]
    for f in out:
        bg=Image.new('RGB',f.size,(255,255,255)); bg.paste(f,(0,0),f)
        q=bg.quantize(palette=pal,dither=Image.Dither.NONE)
        a=f.getchannel('A').point(lambda v:255 if v>100 else 0)
        q.paste(255,(0,0),a.point(lambda v:255-v))
        fr.append(q)
    palette=pal.getpalette()[:255*3]+[0,0,0]
    for q in fr: q.putpalette(palette)
    fr[0].save(p,save_all=True,append_images=fr[1:],duration=dur,loop=loop,disposal=0,blend=0,transparency=255,optimize=True)
# motion styles: text boing / dog hop / dog shake / heart pulse(whole)
STYLE={1:'boing',2:'sway',9:'hop',19:'hop',20:'pulse',22:'shake',23:'jump',11:'boing'}
picks=[1,11,9,19,20,22,23,2]
cols={k:c for k,s,c in ITEMS}
for idx,k in enumerate(picks,1):
    n=img(k); t,pos,rot,size,font=LAY[k]; box,tc=POS[pos]
    D=new(); dog(D,n,B(*box))
    if k in EXTRA: EXTRA[k](D)
    T=new(); pop(T,t,P(*tc),size,cols[k],rot,font)
    bbD=D.getbbox(); dc=((bbD[0]+bbD[2])/2,bbD[3])
    st=STYLE[k]; frames=[]
    for i in range(N):
        ph=i/N; s=math.sin(2*math.pi*ph)
        d_kw={}; t_kw={}
        if st=='boing': t_kw=dict(scale=1+0.12*abs(math.sin(2*math.pi*ph)),rot=6*s)
        elif st=='sway': t_kw=dict(rot=5*s,dy=-12*abs(s))
        elif st=='hop': d_kw=dict(dy=-40*abs(math.sin(2*math.pi*ph))); t_kw=dict(scale=1+0.06*abs(s))
        elif st=='pulse': d_kw=dict(scale=1+0.05*abs(s)); t_kw=dict(scale=1+0.12*abs(s))
        elif st=='shake': d_kw=dict(dx=14*math.sin(6*math.pi*ph)); t_kw=dict(rot=5*math.sin(6*math.pi*ph))
        elif st=='jump': d_kw=dict(dy=-50*max(0,math.sin(2*math.pi*ph))); t_kw=dict(scale=1+0.15*max(0,s))
        F=Image.new('RGBA',D.size,(0,0,0,0))
        F.alpha_composite(xform(D,dc,**d_kw)); F.alpha_composite(xform(T,P(*tc),**t_kw)); frames.append(F)
    out=finish_frames(frames)
    p=f'{OUTA}/{idx:02d}.png'
    save_apng(out,p)
    print(k,st,os.path.getsize(p)//1024,'KB')
