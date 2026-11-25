*KEYWORD MEMORY=400m
*TITLE
LS-DYNA SSD + acoustic BEM: drill on concrete t=200 mm, exposed  [PREPARED, NOT RUN]
$ ==================================================================================
$ STATUS: not executed in this project (no usable LS-DYNA license). The mesh/material/discrete/load cards follow standard
$ keyword syntax. The *FREQUENCY_DOMAIN cards below follow the R13/R14 manual layout as documented in the comments; verify
$ the field positions against the manual of YOUR release (Example 8.4: SSD coupled to acoustic BEM) with a 5-frequency test run first.
$ ==================================================================================
*CONTROL_TERMINATION
$#  endtim
       1.0
*CONTROL_IMPLICIT_GENERAL
$#  imflag     dt0
         1       1.0
*CONTROL_IMPLICIT_EIGENVALUE
$#    neig  center   lflag  lfdtend   hflag  hfend  eigmth  shfscl
        60       0.0         0       0.0         0       0.0         2       0.0
*DATABASE_BINARY_D3PLOT
$#      dt
       1.0
*INCLUDE
mesh.k
*INCLUDE
loads.k
$ ---- steady-state dynamics ----------------------------------------------------
*FREQUENCY_DOMAIN_SSD
$#   mdmin   mdmax   fnmin   fnmax  restmd  restdp  lcflag  relatv
         1        60       0.0     2828.6         0         0         0         0
$#   dampf   lcdam   lctyp  dmpmas  dmpstf  dmpflg
    0.0100         0         0       0.0       0.0         0
$#   nfreq  fstart   fstop  fspace   lcfreq
      1000     44.19   1414.30         0         0
$ excitation: nodal loads defined by *LOAD_NODE_POINT with curve 1 (unit amplitude at all frequencies)
$ ---- acoustic BEM (rigid ground by image method: see README, section "ground plane") -----------
*FREQUENCY_DOMAIN_ACOUSTIC_BEM
$#  method   maxit  tollin    tolr
         3         0       0.0       0.0
$#      ro       c    fmin    fmax   nfreq   dtout  tstart    pref
       1.2     343.0   44.19 1414.30    1000       0.0       0.0   2.0E-05
$#  nsidext typext nsidint typint  (field points = node set 2; surface = part 2)
         2         0         0         0
*END
