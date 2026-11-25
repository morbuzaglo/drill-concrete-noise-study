import numpy as np, time, pathlib, sys
from model import *
from fem import soil_props
from ccx_runner import *
job=pathlib.Path(r'../openradioss/../results/ccx_smoke'); job.mkdir(parents=True,exist_ok=True)
t0=time.time()
c=Case(0.1,False,dx=0.05,dp=0.1,nmodes=40,soil=soil_props(eta=0.0),modal=True,bem=False)
print('case built %.1fs'%(time.time()-t0),'my modes',np.round(c.modal.f[:10],1))
bands=[(100.0,200.0,11)]
sn=write_inp(c,job/'s.inp',bands,nmodes=40,loads=c.F[:,:1])
print('inp written',(job/'s.inp').stat().st_size/1e6,'MB; surf nodes',len(sn))
rc,dt,out=run_ccx(str(job),'s',log=job/'s.log'); print('ccx rc',rc,'%.1fs'%dt)
print(out[-600:] if rc else '')
fr,ids,U,eig=collect(job/'s.dat',len(sn),1,bands)
print('freqs',fr[:3],U.shape)
# acceleration at sensors from ccx
Aop=c.Asens.tocsr()
w=2*np.pi*fr
# build full u vector at surf nodes
def accel(Uc):   # Uc (nf,nsurf,3)
    res=[]
    for i in range(len(fr)):
        u=np.zeros(c.slab.ndof,complex)
        for k,nid in enumerate(ids): u[3*(nid-1):3*(nid-1)+3]=Uc[i,k]
        res.append(-w[i]**2*(Aop@u))
    return np.array(res)
a_ccx=accel(U[0])
r=c.sweep(fr,loads=c.F[:,:1],keep_v=False) if False else None
# own: structural only
acc_own=[]
for f in fr:
    q=c.modal.solve(2*np.pi*f,c.F[:,:1]); acc_own.append(-(2*np.pi*f)**2*(c.AsPhi@q)[:,0])
acc_own=np.array(acc_own)
for s in range(3):
    print('sensor',s,'ccx |a|',np.round(np.abs(a_ccx[:,s])[::2],4),'\n          own |a|',np.round(np.abs(acc_own[:,s])[::2],4))
    print('   phase diff deg',np.round(np.degrees(np.angle(a_ccx[:,s]/acc_own[:,s]))[::2],1))
