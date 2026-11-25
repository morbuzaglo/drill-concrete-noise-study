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
      1412       1       1 1.631259152E-02
      1417       1       1 1.111925553E-01
      1422       1       1 1.631259152E-02
      1517       1       1 1.111925553E-01
      1522       1       1 4.899794129E-01
      1527       1       1 1.111925553E-01
      1622       1       1 1.631259152E-02
      1627       1       1 1.111925553E-01
      1632       1       1 1.631259152E-02
$ ---- load case 2: torque_uniform_1Nm  (switch on by including this block in main.k via the *INCLUDE lines)
$*LOAD_NODE_POINT
$#     nid     dof    lcid      sf
$      1412       2       1 4.813926667E-01
$      1412       3       1-4.813926667E-01
$      1417       2       1 4.037214667E+00
$      1417       3       1 1.815171277E-15
$      1422       2       1 4.813926667E-01
$      1422       3       1 4.813926667E-01
$      1517       2       1-4.892570724E-15
$      1517       3       1-4.037214667E+00
$      1522       2       1-3.385573072E-14
$      1522       3       1 1.067201882E-14
$      1527       2       1-5.151695043E-15
$      1527       3       1 4.037214667E+00
$      1622       2       1-4.813926667E-01
$      1622       3       1-4.813926667E-01
$      1627       2       1-4.037214667E+00
$      1627       3       1 2.128288865E-15
$      1632       2       1-4.813926667E-01
$      1632       3       1 4.813926667E-01
$ ---- load case 3: axial_seg6_0deg_1N  (switch on by including this block in main.k via the *INCLUDE lines)
$*LOAD_NODE_POINT
$#     nid     dof    lcid      sf
$      1412       1       1 1.624703042E-02
$      1417       1       1 1.129114927E-01
$      1422       1       1 1.624703042E-02
$      1517       1       1 1.094536357E-01
$      1522       1       1 4.902816215E-01
$      1527       1       1 1.094536357E-01
$      1622       1       1 1.624703042E-02
$      1627       1       1 1.129114927E-01
$      1632       1       1 1.624703042E-02
$ ---- load case 4: axial_seg6_30deg_1N  (switch on by including this block in main.k via the *INCLUDE lines)
$*LOAD_NODE_POINT
$#     nid     dof    lcid      sf
$      1412       1       1 1.624703042E-02
$      1417       1       1 1.094536357E-01
$      1422       1       1 1.624703042E-02
$      1517       1       1 1.129114927E-01
$      1522       1       1 4.902816215E-01
$      1527       1       1 1.129114927E-01
$      1622       1       1 1.624703042E-02
$      1627       1       1 1.094536357E-01
$      1632       1       1 1.624703042E-02
*END
