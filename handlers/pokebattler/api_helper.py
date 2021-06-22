tab_count = -1
recurse_limit = 2
def unwind(f, itera):
    global tab_count
    global recurse_limit
    if isinstance(itera, list):
        if tab_count < recurse_limit:
            f.write("--ENTER LIST--\n")
        print_list(f, itera)
        if tab_count < recurse_limit:
            f.write("--EXIT LIST--\n")
    
    if isinstance(itera, dict):
        if tab_count < recurse_limit:
            f.write("--ENTER DICT--\n")
        print_dict(f, itera)
        if tab_count < recurse_limit:
            f.write("--EXIT DICT--\n")
    
    if isinstance(itera, (int, str)):
        to_print = tab_count * "\t"
        if tab_count < recurse_limit + 1:
            f.write(f"{to_print} value: {itera}\n")

def print_dict(f, dictionary):
    global tab_count
    global recurse_limit
    tab_count = tab_count + 1
    for k,v in dictionary.items():
        to_print = tab_count * "\t"
        if tab_count < recurse_limit + 1:
            f.write(f"{to_print}key: {k}\n")
        unwind(f, v)
    tab_count = tab_count - 1

def print_list(f, itera):
    for item in itera:
        unwind(f, item)