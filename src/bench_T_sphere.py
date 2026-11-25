import numpy as np, time
from bem import sphere_panels, pulsating_sphere_exact, C0
from bempp_T import *
a=0.25; v0=1.0
c=sphere_panels(a,8,half=True); ctx=Ctx(c); print('half-sphere quads',ctx.nq_exp,'tris',len(ctx.tris))
mics=np.array([[0.5,0,0.01],[1.0,0,0.3],[2.0,0,0.5]]); rr=np.linalg.norm(mics,axis=1)
for ka in (0.3,1,2,3,np.pi,4):
    w=ka*C0/a; f=w/2/np.pi; t=time.time()
    T=T_at(ctx,f,mics); p=T@np.full(ctx.nq_exp,v0)
    pe=pulsating_sphere_exact(w,a,v0,rr)
    print(f' ka={ka:.2f} dB err',np.round(20*np.log10(np.abs(p)/np.abs(pe)),3),'phase err deg',np.round(np.degrees(np.angle(p/pe)),2),f'{time.time()-t:.1f}s')
