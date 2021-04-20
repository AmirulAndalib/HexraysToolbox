# Hexrays Toolbox

Hexrays Toolbox is a script for the Hexrays Decompiler which
can be used to find code patterns within decompiled code:

- scan binary files for known and unknown vulnerabilities
- locate code patterns from previously reverse engineered executables
  within newly decompiled code
- malware variant analysis
- find code similarities across several binaries
- find code patterns from one architecture within executable code of another
  architecture
- many more, limited (almost) only by the queries you'll come up with ;)

The query shown below can be used to detect CVE-2019-3568 in libwhatsapp.so.
Find the example script ![here](./examples/)

![toolbox animated gif](./rsrc/toolbox.gif?raw=true)

Loading hxtb.py with IDA (alt-f7) will make
available the "find_expr()" and "find_item()" functions
to the IDAPython CLI and the script interpreter (shift-f2).

```
    find_item(ea, q)
    find_expr(ea, q)

    Positional arguments:
        ea:         address of a valid function within
                    the current database
        q:          lambda function
                    custom lambda function with the following arguments:
                    1. cfunc: cfunc_t
                    2. i/e:   cinsn_t/cexpr_t
    Returns:
        list of query_result_t objects

    Example:
        find_expr(here(), lambda cf, e: e.op is cot_call)
    
        -> finds and returns all function calls within a current function.
        The returned data is a list of query_result_t objects (see hxtb.py).

        The returned list can be passed to an instance of the ic_t class,
        which causes the data to be displayed by a chooser as follows:

        from idaapi import *
        import hxtb
        hxtb.ic_t(find_expr(here(), lambda cf,e:e.op is cot_call))


    Please find the cfunc_t, citem_t, cinsn_t and cexpr_t structures
    within hexrays.hpp for further help and details.
```
Please also check out the [HRDevHelper](https://github.com/patois/HRDevHelper) plugin and the [IDAPyHelper](https://github.com/patois/IDAPyHelper) script which may assist in writing respective queries.

## Examples:

### - get list of expressions that compare anything to zero ("x == 0")
```
         cot_eq
         /   \
      x /     \ y
(anything)  cot_num --- n.numval() == 0
```
``` python
from idaapi import *
from hxtb import find_expr
query = lambda cfunc, e: e.op is cot_eq and e.y.op is cot_num and e.y.numval() == 0
r = [e for e in find_expr(here(), query)]
for e in r:
    print(e)
```
### - get list of function calls
```
        cot_call
         / 
      x /
 cot_obj
```
``` python
from idaapi import *
from hxtb import find_expr
query = lambda cfunc, e: e.op is cot_call and e.x.op is cot_obj
r = [e for e in find_expr(here(), query)]
for e in r:
    print(e)
```
![list of calls ](./rsrc/calls.png?raw=true)
### - print list of memcpy calls where "dst" argument is on stack
```
        cot_call --- arg1 is cot_var
         /           arg1 is on stack
      x /
 cot_obj --- name(obj_ea) == 'memcpy'
```
``` python
from idaapi import *
from hxtb import find_expr
r = []
query = lambda cfunc, e: (e.op is cot_call and
           e.x.op is cot_obj and
           get_name(e.x.obj_ea) == 'memcpy' and
           len(e.a) == 3 and
           e.a[0].op is cot_var and
           cfunc.lvars[e.a[0].v.idx].is_stk_var())
for ea in Functions():
    r += [e for e in find_expr(ea, query)]
for e in r:
    print(e)
```
### - get list of calls to sprintf(str, fmt, ...) where fmt contains "%s"
```
        cot_call --- arg2 ('fmt') contains '%s'
         /
      x /
 cot_obj --- name(obj_ea) == 'sprintf'
```
``` python
from idaapi import *
from hxtb import find_expr
r = []
query = lambda cfunc, e: (e.op is cot_call and
    e.x.op is cot_obj and
    get_name(e.x.obj_ea) == 'sprintf' and
    len(e.a) >= 2 and
    e.a[1].op is cot_obj and
    is_strlit(get_flags(e.a[1].obj_ea)) and
    b'%s' in get_strlit_contents(e.a[1].obj_ea, -1, 0, STRCONV_ESCAPE))
for ea in Functions():
    r += [e for e in find_expr(ea, query)]
for e in r:
    print(e)
```
### - get list of signed operators, display result in chooser
``` python
from idaapi import *
from hxtb import ic_t
query = lambda cfunc, e: (e.op in
            [hr.cot_asgsshr, hr.cot_asgsdiv,
            hr.cot_asgsmod, hr.cot_sge,
            hr.cot_sle, hr.cot_sgt,
            hr.cot_slt, hr.cot_sshr,
            hr.cot_sdiv, hr.cot_smod])
ic_t(query)
```
![list of signed operators](./rsrc/signed_ops.png?raw=true)
### - get list of "if" statements, display result in chooser
``` python
from idaapi import *
from hxtb import ic_t
ic_t(lambda cf, i: i.op is cit_if)
```
![list of if statements](./rsrc/if_stmt.png?raw=true)
### - get list of all loop statements in db, display result in chooser
``` python
from idaapi import *
from hxtb import ic_t, query_db
ic_t(query_db(lambda cf,i: is_loop(i.op)))
```
![list of loops](./rsrc/loops.png?raw=true)
### - get list of loop constructs containing copy operations
``` python
from hxtb import ic_t, query_db, find_child_expr
from ida_hexrays import *


find_copy_query = lambda cfunc, i: (i.op is cot_asg and
                                i.x.op is cot_ptr and
                                i.y.op is cot_ptr)

find_loop_query = lambda cfunc, i: (is_loop(i.op) and
                            find_child_expr(cfunc, i, find_copy_query))


ic_t(query_db(find_loop_query))
```
![list of copy loops](./rsrc/copy_loop.png?raw=true)
