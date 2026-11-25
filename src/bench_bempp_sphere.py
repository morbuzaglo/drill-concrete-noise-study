import numpy as np, time
from bem import sphere_panels, pulsating_sphere_exact
from bempp_ac import *
a=0.25; v0=1.0
for N in (6,10):
    c=sphere_panels(a,N); R=Radiator(c); print('N',N,'tris',R.ntri,'p1 dofs',R.p1.global_dof_count)
    pts=np.array([[0.5,0,0],[1.0,0,0.3],[2.0,0,0]]); rr=np.linalg.norm(pts,axis=1)
    for ka in (0.3,1,2,3,np.pi,4,5):
        w=ka*C0/a; t=time.time()
        p=R.solve(w/2/np.pi,np.full((R.nq,1),v0,complex),pts)[:,0]
        pe=pulsating_sphere_exact(w,a,v0,rr)
        print(f' ka={ka:.2f} dB err',np.round(20*np.log10(np.abs(p)/np.abs(pe)),3),'phase err deg',np.round(np.degrees(np.angle(p/pe)),2),f'{time.time()-t:.1f}s')
