import hxtb
from idaapi import *

__author__ = "https://github.com/patois"

# ----------------------------------------------------------------------------
def fc(func_name, fuzzy=False):
    """find function calls to 'func_name'
    
    """

    if fuzzy:
        name = func_name.lower()
        query = lambda cf, e: (e.op is cot_call and
            e.x.op is cot_obj and
            name in get_name(e.x.obj_ea).lower())
        
        return hxtb.exec_query(query, Functions(), False)

    # else...
    ea = get_name_ea(BADADDR, func_name)
    if ea != BADADDR:
        query = lambda cf, e: (e.op is cot_call and
            e.x.op is cot_obj and
            get_name(e.x.obj_ea) == func_name)

        return hxtb.exec_query(query, list(set(CodeRefsTo(ea, True))), False)
    
    return list()

# ----------------------------------------------------------------------------
def find_memcpy():
    """find calls to memcpy() where the 'n' argument is signed
    we're going through all functions in order to pick up inlined memcpy() calls

    """

    query = lambda cf, e: (e.op is cot_call and
        e.x.op is cot_obj and
        'memcpy' in get_name(e.x.obj_ea) and
        len(e.a) == 3 and
        e.a[2].op is cot_var and
        cf.lvars[e.a[2].v.idx].tif.is_signed())

    return hxtb.exec_query(query, Functions(), False)

# ----------------------------------------------------------------------------
def find_sprintf():
    """find calls to sprintf() where the format string argument contains '%s'

    """
    func_name = 'sprintf'

    query = lambda cfunc, e: (e.op is cot_call and
        e.x.op is cot_obj and
        func_name in get_name(e.x.obj_ea) and
        len(e.a) >= 2 and
        e.a[1].op is cot_obj and
        is_strlit(get_flags(e.a[1].obj_ea)) and
        b'%s' in get_strlit_contents(e.a[1].obj_ea, -1, 0, STRCONV_ESCAPE))

    ea_malloc = get_name_ea_simple(func_name)
    ea_set = set([f.start_ea for f in [get_func(xref.frm) for xref in XrefsTo(ea_malloc, XREF_FAR)] if f])
    
    return hxtb.exec_query(query, ea_set, False)

# ----------------------------------------------------------------------------
def find_malloc():
    """calls to malloc() with a size argument that is anything
    but a variable or an immediate number.

    """
    func_name = 'malloc'

    query = lambda cf, e: (e.op is cot_call and 
        e.x.op is cot_obj and
        get_name(e.x.obj_ea) == func_name and
        len(e.a) == 1 and
        e.a[0].op not in [cot_num, cot_var])

    ea_malloc = get_name_ea_simple(func_name)
    ea_set = set([f.start_ea for f in [get_func(xref.frm) for xref in XrefsTo(ea_malloc, XREF_FAR)] if f])
    
    return hxtb.exec_query(query, ea_set, False)

# ----------------------------------------------------------------------------
def find_gpa():
    """find dynamically imported functions (Windows)
    example function to be passed to hr_toolbox.ic_t()

    """
    func_name = 'GetProcAddress'

    query = lambda cfunc, e: (e.op is cot_call and
        e.x.op is cot_obj and
        get_name(e.x.obj_ea) == func_name and
        len(e.a) == 2 and
        e.a[1].op is cot_obj and
        is_strlit(get_flags(e.a[1].obj_ea)))

    gpa = get_name_ea_simple(func_name)
    ea_set = set([f.start_ea for f in [get_func(xref.frm) for xref in XrefsTo(gpa, XREF_FAR)] if f])
    
    return hxtb.exec_query(query, ea_set, False)

# ----------------------------------------------------------------------------
def menu():
    print("""Example commands:

    menu()

    # query entire db, print results (ignore cit_...)
    qdb(lambda cf, e: e.op is cot_call, query_full=False)

    # query current function, print results
    q(lambda cf, e: e.op is cit_if and e.cif.expr.op is cot_land)

    # query list of predefined addresses, show results in chooser
    lst(lambda cf, e: (e.op is cot_call and
                        e.x.op is cot_obj and
                        get_name(e.x.obj_ea) == "strcat"),
                        Functions(), query_full=False)
    lst(lambda cf, e: e.op is cot_var and cf.lvars[e.v.idx].is_stk_var(), query_full=False)
    lst(lambda cf, i: i.op is cit_if)

    # call predefined query (check src for details)
    lst(fc("LoadLibrary", fuzzy=True))
    lst(find_memcpy())
    lst(find_gpa())
    lst(find_malloc())
    lst(find_sprintf())
    lst(qdb(lambda cf,i: is_loop(i.op)))
    """)
    return

if __name__ == "__main__":
    from hxtb import query as q
    from hxtb import query_db as qdb
    from hxtb import ic_t as lst
    menu()
