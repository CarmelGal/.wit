import datetime
import filecmp
import os
import random
import shutil
import string
import sys

from graphviz import Digraph


def init():
    current_dir = os.getcwd()
    print(current_dir)
    folders = ['\\.wit', '\\.wit\\images', '\\.wit\\staging_area']
    for folder in folders:
        os.mkdir(current_dir + folder)
    with open(os.path.join(current_dir, '.wit', 'activated.txt'), 'w') as active_file:
        active_file.write('master')
        

def find_wit(file_path):
    found_wit = False
    splited_path = os.path.split(file_path)
    backup_tree = []
    while not found_wit and splited_path[1] != '':
        print(f"File path is {file_path}")
        folder = splited_path[0]
        print(f"Folder (splited_path[0]) is {folder}")
        folder_contents = os.listdir(folder)
        if ('.wit' in folder_contents) and (os.path.isdir(os.path.join(folder, '.wit'))):
            found_wit = True
            print(f'Found .wit in {folder}')
            backup_tree.insert(0, folder)
            return backup_tree
        else:
            print("Didn't find .wit")
            backup_tree.insert(0, folder)
            file_path = folder 
            splited_path = os.path.split(file_path)
            print(f"new file path is {file_path}")
    return None


def copy_file(file_path, current_folder):
    if os.path.isfile(file_path):
        shutil.copy2(file_path, current_folder)
        print("copeid file")
    else:
        shutil.copytree(file_path, current_folder)
        print("copeid file")


def add():
    file_path = ' '.join(sys.argv[2:])
    if not os.path.isabs(file_path):
        file_path = os.path.join(os.getcwd(), file_path)
    folders_list = find_wit(file_path)
    if folders_list is None:
        return ".Wit folder was not found!"
    else:
        print(f"os get cwd is {os.getcwd()}")
        print(f"folders list[0] is {folders_list[0]}")
        staging_path = os.path.join(folders_list[0], '.wit', 'staging_area')
        print(f"Staging path is: {staging_path}")
        current_folder = staging_path
        if len(folders_list) == 1:
            copy_file(file_path, os.path.join(current_folder, os.path.split(file_path)[1]))
        else:
            for fld in folders_list[1:]:
                potential_fld = os.path.join(current_folder, os.path.split(fld)[1])
                current_folder = potential_fld
                if os.path.split(potential_fld)[1] not in os.listdir(staging_path):
                    os.mkdir(potential_fld)
                    print(f"created {os.path.split(potential_fld)[1]}")
            copy_file(file_path, current_folder)
        

def commit_name():
    options = string.hexdigits
    random_list = random.choices(options, k=40)
    folder_name = ''.join(random_list)
    return folder_name


def update_id_text(id_text_path, parent=None, another_parent=None):
    if another_parent is None:
        parent_content = parent
    else:
        parent_content = f"{parent}, {another_parent}"
    content = f"""parent: {parent_content}
    date: {datetime.datetime.now()}
    message: {sys.argv[2:]}
    """
    with open(id_text_path, 'w') as id_file:
        id_file.write(content)


def get_head(ref_path):
    with open(ref_path, 'r') as ref_file:
        data = ref_file.readlines()
        head = (data[0].split('='))[1].strip()
    return head


def create_id_elements(images_path, another_parent):
    commit_id = commit_name()
    new_commit_folder = os.path.join(images_path, commit_id)
    os.mkdir(new_commit_folder)
    id_text_path = os.path.join(images_path, (commit_id + '.txt'))
    references_potential_path = os.path.join(os.path.split(images_path)[0], 'references.txt')
    if os.path.isfile(references_potential_path):
        head_content = get_head(references_potential_path)
        update_id_text(id_text_path, head_content, another_parent)
    else:
        update_id_text(id_text_path)
    return commit_id


def create_image(wit_location, id_folder):
    staging_path = os.path.join(wit_location, '.wit', 'staging_area')
    staging_tree = os.listdir(staging_path)
    for entry in staging_tree:
        file_to_copy = os.path.join(staging_path, entry)
        if os.path.isfile(file_to_copy):
            shutil.copy2(file_to_copy, id_folder)
        else:
            new_folder = os.path.join(id_folder, os.path.split(file_to_copy)[1])
            shutil.copytree(file_to_copy, os.path.join(id_folder, new_folder))
    print("Image completed")


def check_references(ref_path):
    with open(ref_path, 'r') as ref_file:
        lines = ref_file.readlines()
    ref_dict = {line.split('=')[0]: (line.split('=')[1]).strip() for line in lines}
    if ref_dict['HEAD'] == ref_dict['master']:
        return (True, ref_dict)
    else:
        return (False, ref_dict)


def is_master_activated(wit_location):
    activated_path = os.path.join(wit_location, '.wit', 'activated.txt')
    with open(activated_path, 'r') as active_file:
        active_branch = active_file.read()
    if active_branch == 'master':
        return True
    else:
        return False


def update_references(wit_location, commit_id):
    references_path = os.path.join(wit_location, '.wit', 'references.txt')
    if os.path.isfile(references_path):
        check_result, ref_dict = check_references(references_path)
        if (check_result) and (is_master_activated(wit_location)):
            ref_dict['HEAD'] = commit_id
            ref_dict['master'] = commit_id
            new_lines = [f"{key}={value}" for key, value in ref_dict.items()]
            with open(references_path, 'w') as ref_file:
                ref_file.writelines(new_lines)
        else:
            ref_dict["HEAD"] = commit_id
            new_lines = [f"{key}={value}" for key, value in ref_dict.items()]
            with open(references_path, 'w') as ref_file:
                ref_file.writelines(new_lines)
    else:
        with open(references_path, 'w') as ref_file:
            data = [f"HEAD={commit_id}\n", f"master={commit_id}"]
            ref_file.writelines(data)


def maybe_update_branch(wit_location, new_commit_id):
    ref_path = os.path.join(wit_location, '.wit', 'references.txt')
    activated_path = os.path.join(wit_location, '.wit', 'activated.txt')
    with open(activated_path, 'r') as active_file:
        active_branch = active_file.read()
    with open(ref_path, 'r') as ref_file:
        lines = ref_file.readlines()
    possible_names_dict = {line.split('=')[0]: (line.split('=')[1]).strip() for line in lines}
    if possible_names_dict['HEAD'] == possible_names_dict[active_branch]:
        possible_names_dict[active_branch] = new_commit_id
        new_lines = [f"{key}={value}" for key, value in possible_names_dict.items()]
        with open(ref_path, 'w') as ref_file:
            ref_file.writelines(new_lines)
    else:
        return False


def commit(wit_location, another_parent=None):
    images_path = os.path.join(wit_location, '.wit', 'images')
    commit_id = create_id_elements(images_path, another_parent)
    id_folder = os.path.join(images_path, commit_id)
    create_image(wit_location, id_folder)
    maybe_update_branch(wit_location, commit_id)
    update_references(wit_location, commit_id)
    

def get_current_id(wit_location):
    references_path = os.path.join(wit_location, '.wit', 'references.txt') 
    with open(references_path, 'r') as ref_file:
        HEAD_line = ref_file.readlines()[0]
    current_committed_id = (HEAD_line.split('=')[1]).strip()
    return current_committed_id


def committed_vs_staged(folder_path, image_path, not_committed):
    for f in os.listdir(folder_path):
        if not os.path.exists(os.path.join(image_path, f)):
            print(F"the file {os.path.join(folder_path, f)} was not found in {os.path.join(image_path, f)}")
            not_committed.append(os.path.join(folder_path, f))
        elif os.path.isdir(f):
            print(F"the folder {os.path.join(folder_path, f)} was found in {os.path.join(image_path, f)}")
            not_committed.extend(committed_vs_staged(os.path.join(folder_path, f), image_path, not_committed))
        else:
            print(F"the file {os.path.join(folder_path, f)} was found in {os.path.join(image_path, f)}")
    return not_committed


def original_vs_stage(original_path, staging_path, not_updated, not_staged):
    lst = os.listdir(original_path)
    try:
        lst.remove('.wit')
    except ValueError:
        lst = os.listdir(original_path)
    for f in lst:
        orig = os.path.join(original_path, f)
        stage = os.path.join(staging_path, f)
        if os.path.exists(stage):
            if os.path.isdir(stage):
                original_vs_stage(orig, stage, not_updated, not_staged)
            else:
                if not filecmp.cmp(orig, stage, shallow=False):
                    not_updated.append(orig)
        else:
            not_staged.append(orig)    
    return not_updated, not_staged


def create_message(commit_id, not_committed, not_updated_files, not_staged_files):
    not_committed_string = '\n'.join(not_committed)
    not_updated_string = '\n'.join(not_updated_files)
    not_staged_string = '\n'.join(not_staged_files)
    message = f"""
    Status update, {datetime.datetime.now()}:
    Commit ID is {commit_id}
    {'-' * 50}
    Changes to be committed:
    {not_committed_string}
    {'-' * 50}
    Changes not staged for commit:
    {not_updated_string}
    {'-' * 50}
    Untracked files:
    {not_staged_string}
    """
    return message


def status(wit_location):
    commit_id = get_current_id(wit_location)
    image_path = os.path.join(wit_location, '.wit', 'images', commit_id)
    current_staging = os.path.join(wit_location, '.wit', 'staging_area')
    not_committed = committed_vs_staged(current_staging, image_path, [])
    not_updated_files, not_staged_files = original_vs_stage(wit_location, current_staging, [], [])
    ans_dict = {
        'commit id': commit_id, 
        'not committed': not_committed, 
        'not updated': not_updated_files,
        'not staged': not_staged_files
    }
    return ans_dict


def update_folder(commit_path, original_path):
    for f in os.listdir(commit_path):
        orig = os.path.join(original_path, f)
        print(f"orig supposed to be {orig}")
        comt = os.path.join(commit_path, f)
        print(f"comit file is be {comt}")
        print(os.path.exists(orig))
        if os.path.exists(orig) and os.path.isdir(orig):
            print(F"entering folder {comt}")
            update_folder(comt, orig)
        elif (not os.path.exists(orig)) and os.path.isdir(comt):
            print(F"creating folder {orig}")
            shutil.copytree(comt, orig, copy_function=shutil.copy)
        else:
            print(F"updating/creating file {orig}")
            shutil.copy2(comt, orig)


def update_staging(wit_location, commit_path):
    staging_path = os.path.join(wit_location, '.wit', 'staging_area')
    shutil.rmtree(staging_path)
    shutil.copytree(commit_path, staging_path)


def find_master(wit_location):
    references_path = os.path.join(wit_location, '.wit', 'references.txt')
    with open(references_path, 'r') as ref_file:
        master_line = ref_file.readlines()[1]
    master_content = master_line.split('=')[1]
    return master_content


def update_HEAD(wit_location, commit_folder):
    references_path = os.path.join(wit_location, '.wit', 'references.txt')
    with open(references_path, 'r') as ref_file:
        lines = ref_file.readlines()
    ref_dict = {line.split('=')[0]: (line.split('=')[1]).strip() for line in lines}
    ref_dict['HEAD'] = commit_folder
    new_lines = [f"{key}={value}" for key, value in ref_dict.items()]
    with open(references_path, 'w') as ref_file:
        ref_file.writelines(new_lines)


def check_branches(wit_location, possible_branch):
    branch_id = False
    ref_path = os.path.join(wit_location, '.wit', 'references.txt')
    with open(ref_path, 'r') as ref_file:
        lines = ref_file.readlines()
    possible_names_dict = {line.split('=')[0]: (line.split('=')[1]).strip() for line in lines}
    if possible_branch in possible_names_dict:
        branch_id = possible_names_dict[possible_branch]
    return branch_id


def checkout_operation(wit_location, commit_folder):
    commit_path = os.path.join(wit_location, '.wit', 'images', commit_folder)
    original_path = wit_location
    update_folder(commit_path, original_path)
    update_staging(wit_location, commit_path)
    update_HEAD(wit_location, commit_folder)


def checkout(wit_location):
    checkout_input = sys.argv[2]
    check_branch_result = check_branches(wit_location, checkout_input)
    if check_branch_result:
        activated_path = os.path.join(wit_location, '.wit', 'activated.txt')
        with open(activated_path, 'w') as active_file:
            active_file.write(checkout_input)
        commit_folder = check_branch_result
    else:
        commit_folder = checkout_input
        with open(activated_path, 'w') as active_file:
            active_file.write('')
    checkout_operation(wit_location, commit_folder)


def get_parents(son_path):
    with open(son_path, 'r') as son_file:
        parent_line = son_file.readlines()[0]
    parents = parent_line.split()[1:]
    if len(parents) == 2:
        parents[0] = parents[0].strip(',')
    return parents


def recurese_parents(wit_location, son, g):
    current_son_path = os.path.join(wit_location, '.wit', 'images', (son + '.txt'))
    parents = get_parents(current_son_path)
    if parents[0] == 'None':
        g.edge(son, parents[0])
    elif len(parents) == 2:
        g.edge(son, parents[0])
        g.edge(son, parents[1])
        recurese_parents(wit_location, parents[0], g)
        recurese_parents(wit_location, parents[1], g)
    else:
        g.edge(son, parents[0])
        recurese_parents(wit_location, parents[0], g)
    return g
    
    
def graph(wit_location):
    ref_path = os.path.join(wit_location, '.wit', 'references.txt')
    head = get_head(ref_path)
    g = Digraph('G', filename='parents.gv')
    g = recurese_parents(wit_location, head, g)
    g.view()


def branch(wit_location):
    name = sys.argv[2:]
    ref_path = os.path.join(wit_location, '.wit', 'references.txt')
    commit_id = get_head(ref_path)
    branch_line = f"{name}={commit_id}"
    with open(ref_path, 'a') as ref_file:
        ref_file.write(branch_line)


def get_parents_chain(wit_location, son, parents_list):
    current_son_path = os.path.join(wit_location, '.wit', 'images', (son + '.txt'))
    parents = get_parents(current_son_path)
    if parents[0] == 'None':
        return parents_list
    elif len(parents) == 2:
        parents_list.append(parents[0])
        parents_list.append(parents[1])
        get_parents_chain(wit_location, parents[0], parents_list)
        get_parents_chain(wit_location, parents[1], parents_list)
    else:
        parents_list.append(parents[0])
        get_parents_chain(wit_location, parents[0], parents_list)


def get_mutual_father(wit_location, head_commit, branch_commit):
    head_chain = get_parents_chain(wit_location, head_commit, [])
    branch_chain = get_parents_chain(wit_location, branch_commit, [])
    for i in range(len(head_chain)):
        if head_chain[i] in branch_chain:
            return head_chain[i]


def check_valid_execution(wit_location):
    ref_path = os.path.join(wit_location, '.wit', 'references.txt')
    commit_id = get_head(ref_path)
    image_path = os.path.join(wit_location, '.wit', 'images', commit_id)
    current_staging = os.path.join(wit_location, '.wit', 'staging_area')
    result1 = committed_vs_staged(current_staging, image_path, [])
    result2 = committed_vs_staged(image_path, current_staging, [])
    if (not result1) and (not result2):
        return True
    else:
        return False


def check_staging_vs_father(staging_path, branch_path, father_path):  # go over stage (HEAD) folder and update files that hasn't changed since father with the branch version
    for f in os.listdir(staging_path):
        current_staging = os.path.join(staging_path, f)
        possible_father = os.path.join(father_path, f)
        possible_branch = os.path.join(branch_path, f)
        if os.path.isdir(possible_father):
            check_staging_vs_father(current_staging, possible_father, possible_branch)
        elif os.path.isfile(possible_father):
            if filecmp.cmp(current_staging, possible_father, shallow=False):
                if os.path.isfile(possible_branch):
                    shutil.copy2(possible_branch, current_staging)


def update_staging_with_branch(staging_path, branch_path, father_path):
    for f in os.listdir(branch_path):
        current_branch = os.path.join(branch_path, f)
        possible_father = os.path.join(father_path, f)
        possible_staging = os.path.join(father_path, f)
        if os.path.isdir(branch_path) and os.path.isdir(possible_father):
            update_staging_with_branch(possible_staging, current_branch, possible_father)
        elif (not os.path.exists(possible_father)) and (os.path.isdir(current_branch)):
            shutil.copytree(current_branch, possible_staging)
        elif os.path.isfile(possible_father):
            if filecmp.cmp(possible_father, current_branch, shallow=False):
                if not os.path.isfile(possible_staging):
                    shutil.copy2(branch_path, possible_staging)


def merge(wit_location):
    valid = check_valid_execution(wit_location)
    if not valid:
        message = "Staging area is not the same as current commit "
        return message
    else:
        ref_path = os.path.join(wit_location, '.wit', 'references.txt')
        head_commit = get_head(ref_path)
        branch_name = sys.argv[2]
        branch_commit = check_branches(wit_location, branch_name)
        branch_commit_path = os.path.join(wit_location, '.wit', 'images', branch_commit + '.txt')
        father_commit = get_mutual_father(wit_location, head_commit, branch_commit)
        father_path = os.path.join(wit_location, '.wit', 'images', father_commit + '.txt')
        staging_path = os.path.join(wit_location, '.wit', 'staging_area')
        check_staging_vs_father(staging_path, branch_commit_path, father_path)
        update_staging_with_branch(staging_path, branch_commit_path, father_path)
    commit(wit_location, branch_commit)

        
if sys.argv[1] == 'init':
    init()
    print("init executed")
elif sys.argv[1] == 'add':
    add()
    print("add executed")
elif sys.argv[1] == 'commit':
    check_wit = find_wit(os.getcwd())
    if check_wit:
        commit(check_wit[0])
        print("commit executed")
elif sys.argv[1] == 'status':
    check_wit = find_wit(os.getcwd())
    if check_wit:
        ans_dict = status(check_wit[0])
        print(create_message(ans_dict['commit id'], ans_dict['not committed'], ans_dict['not updated'], ans_dict['not staged']))
        print("status executed")
elif sys.argv[1] == 'checkout':
    check_wit = find_wit(os.getcwd())
    not_committed_status = status(check_wit[0])['not committed']
    not_updated_status = status(check_wit[0])['not updated']
    if check_wit and not not_committed_status and not not_updated_status:
        checkout(check_wit[0])
        print("checkout executed")
elif sys.argv[1] == 'graph':
    check_wit = find_wit(os.getcwd())
    if check_wit:
        graph(check_wit[0])
elif sys.argv[1] == 'branch':
    check_wit = find_wit(os.getcwd())
    if check_wit:
        branch(check_wit[0])
elif sys.argv[1] == 'merge':
    check_wit = find_wit(os.getcwd())
    if check_wit:
        merge(check_wit[0])
else:
    print("No command was entered. try again")