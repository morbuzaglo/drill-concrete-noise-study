*KEYWORD MEMORY=2000m
*TITLE
SSD-direct + acoustic BEM: concrete t=200 mm, partially buried, solid soil block
$ PREPARED, NOT RUN. *FREQUENCY_DOMAIN_SSD_DIRECT cards are assumed to follow *FREQUENCY_DOMAIN_SSD: check against the manual of your release.
$ Soil material damping (hysteretic eta = 0.05) is not reproduced; only the Lysmer dampers on the outer faces and DAMPF act.
*INCLUDE
mesh.k
*INCLUDE
loads.k
*CONTROL_IMPLICIT_GENERAL
$#  imflag       dt0    imform      nsbs       igs     cnstn      form    zero_v
         1     0.000         0         0         0         0         0         0
*CONTROL_IMPLICIT_SOLUTION
$#  nsolvr    ilimit    maxref     dctol     ectol     rctol     lstol    abstol
         1         0         0     0.000     0.000     0.000     0.000     0.000
*FREQUENCY_DOMAIN_SSD_DIRECT
$#   mdmin     mdmax     fnmin     fnmax    restmd    restdp    lcflag    relatv
         1         1     0.000     0.000         0         0
$#   dampf     lcdam     lctyp    dmpmas    dmpstf    dmpflg
  0.010000         0         0     0.000     0.000
$#                                                      nout     notyp      nova
                                                           1         2         0
$#     nid      ntyp       dof       vad       lc1       lc2       lc3       vid
     26545         0         1         0      1000       200         0         0
     26577         0         1         0      1001       200         0         0
     26609         0         1         0      1002       200         0         0
     26547         0         1         0      1003       200         0         0
     26579         0         1         0      1004       200         0         0
     26611         0         1         0      1005       200         0         0
     26549         0         1         0      1006       200         0         0
     26581         0         1         0      1007       200         0         0
     26613         0         1         0      1008       200         0         0
*DATABASE_FREQUENCY_BINARY_D3SSD
$#  binary
         1
$#    fmin      fmax     nfreq    fspace    lcfreq
   44.1900 1414.3000      1000         0         0
*FREQUENCY_DOMAIN_ACOUSTIC_BEM
$#      ro         c     fnmin     fnmax     nfreq    dt_out   t_start      pref
    1.2000  343.0000   44.1900 1414.3000      1000  0.001000     0.000 2.000E-05
$#nsid_ext  type_ext  nsid_int  type_int   fft_win     trslt    ipfile    iunits
         2         1         0         0         4         0         0         0
$#  method     maxit  tol_iter       ndd    tol_lr  tol_fact     ibdim       npg
         2      1000 1.0000E-6         8     0.000     0.000         0         0
$#               nbc    restrt     iedge      noel     nfrup
                   1                   1
$#    ssid    sstype      norm  bem_type       lc1       lc2
         1         2         0         0
*END
