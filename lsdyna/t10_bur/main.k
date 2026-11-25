*KEYWORD MEMORY=400m
*TITLE
SSD + acoustic BEM: drill on concrete t=100 mm, partially buried
$ Load case 1 (axial, uniform annulus) is active. For cases 2-4 replace the card-7 lines below by the lines in the comment block.
$ Not implemented here: the rigid ground plane for the BEM (the open-source study used the image method).
*INCLUDE
mesh.k
*INCLUDE
loads.k
*CONTROL_IMPLICIT_EIGENVALUE
$#    neig    center     lflag    lftend     rflag    rhtend    eigmth    shfscl
        60     0.000         0     0.000         0     0.000         0     0.000
$#  isolid     ibeam    ishell   itshell
         0         0         0         0
*CONTROL_IMPLICIT_GENERAL
$#  imflag       dt0    imform      nsbs       igs     cnstn      form    zero_v
         1     0.000         0         0         0         0         0         0
*CONTROL_IMPLICIT_SOLUTION
$#  nsolvr    ilimit    maxref     dctol     ectol     rctol     lstol    abstol
         1         0         0     0.000     0.000     0.000     0.000     0.000
*FREQUENCY_DOMAIN_SSD
$#   mdmin     mdmax     fnmin     fnmax    restmd    restdp    lcflag    relatv
         1        60     0.000     0.000         0         0
$#   dampf     lcdam     lctyp    dmpmas    dmpstf    dmpflg
  0.010000         0         0     0.000     0.000
$#                                                      nout     notyp      nova
                                                           1         2         0
$#     nid      ntyp       dof       vad       lc1       lc2       lc3       vid
       848         0         1         0      1000       200         0         0
       851         0         1         0      1001       200         0         0
       854         0         1         0      1002       200         0         0
       911         0         1         0      1003       200         0         0
       914         0         1         0      1004       200         0         0
       917         0         1         0      1005       200         0         0
       974         0         1         0      1006       200         0         0
       977         0         1         0      1007       200         0         0
       980         0         1         0      1008       200         0         0
$ --- load case 2: torque_uniform_1Nm
$ --- load case 3: axial_seg6_0deg_1N
$ --- load case 4: axial_seg6_30deg_1N
$      848         0         2         0      2000       200         0         0
$      848         0         3         0      2001       200         0         0
$      851         0         2         0      2002       200         0         0
$      848         0         1         0      3000       200         0         0
$      851         0         1         0      3001       200         0         0
$      854         0         1         0      3002       200         0         0
$      848         0         1         0      4000       200         0         0
$      851         0         1         0      4001       200         0         0
$      854         0         1         0      4002       200         0         0
*DATABASE_FREQUENCY_BINARY_D3SSD
$#  binary
         1
$#    fmin      fmax     nfreq    fspace    lcfreq
   44.1900 1414.3000      1000         0         0
*FREQUENCY_DOMAIN_ACOUSTIC_BEM
$#      ro         c     fnmin     fnmax     nfreq    dt_out   t_start      pref
    1.2000  343.0000   44.1900 1414.3000      1000  0.001000     0.0002.0000E-05
$#nsid_ext  type_ext  nsid_int  type_int   fft_win     trslt    ipfile    iunits
         2         1         0         0         4         0         0         0
$#  method     maxit  tol_iter       ndd    tol_lr  tol_fact     ibdim       npg
         2      1000 1.0000E-6         8     0.000     0.000         0         0
$#               nbc    restrt     iedge      noel     nfrup
                   1                   1
$#    ssid    sstype      norm  bem_type       lc1       lc2
         1         2         0         0
*END
