*KEYWORD
*TITLE
unit drill loads (axial 1 N distributed on the annulus; torque 1 N m)
*DEFINE_CURVE
$#    lcid
         1
$                 a1                  o1
                 0.0                 1.0
           1.0E+06                 1.0
$ ---- load case 1: axial_uniform_1N  (switch on by including this block in main.k via the *INCLUDE lines)
*LOAD_NODE_POINT
$#     nid     dof    lcid      sf
       848       1       1 1.631259152E-02
       851       1       1 1.111925553E-01
       854       1       1 1.631259152E-02
       911       1       1 1.111925553E-01
       914       1       1 4.899794129E-01
       917       1       1 1.111925553E-01
       974       1       1 1.631259152E-02
       977       1       1 1.111925553E-01
       980       1       1 1.631259152E-02
$ ---- load case 2: torque_uniform_1Nm  (switch on by including this block in main.k via the *INCLUDE lines)
$*LOAD_NODE_POINT
$#     nid     dof    lcid      sf
$       848       2       1 4.813926667E-01
$       848       3       1-4.813926667E-01
$       851       2       1 4.037214667E+00
$       851       3       1 1.815171277E-15
$       854       2       1 4.813926667E-01
$       854       3       1 4.813926667E-01
$       911       2       1-4.892570724E-15
$       911       3       1-4.037214667E+00
$       914       2       1-3.385573072E-14
$       914       3       1 1.067201882E-14
$       917       2       1-5.151695043E-15
$       917       3       1 4.037214667E+00
$       974       2       1-4.813926667E-01
$       974       3       1-4.813926667E-01
$       977       2       1-4.037214667E+00
$       977       3       1 2.128288865E-15
$       980       2       1-4.813926667E-01
$       980       3       1 4.813926667E-01
$ ---- load case 3: axial_seg6_0deg_1N  (switch on by including this block in main.k via the *INCLUDE lines)
$*LOAD_NODE_POINT
$#     nid     dof    lcid      sf
$       848       1       1 1.624703042E-02
$       851       1       1 1.129114927E-01
$       854       1       1 1.624703042E-02
$       911       1       1 1.094536357E-01
$       914       1       1 4.902816215E-01
$       917       1       1 1.094536357E-01
$       974       1       1 1.624703042E-02
$       977       1       1 1.129114927E-01
$       980       1       1 1.624703042E-02
$ ---- load case 4: axial_seg6_30deg_1N  (switch on by including this block in main.k via the *INCLUDE lines)
$*LOAD_NODE_POINT
$#     nid     dof    lcid      sf
$       848       1       1 1.624703042E-02
$       851       1       1 1.094536357E-01
$       854       1       1 1.624703042E-02
$       911       1       1 1.129114927E-01
$       914       1       1 4.902816215E-01
$       917       1       1 1.129114927E-01
$       974       1       1 1.624703042E-02
$       977       1       1 1.094536357E-01
$       980       1       1 1.624703042E-02
*END
