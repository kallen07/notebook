#!/usr/bin/python3

''' Utilities for Git-Notebook interconnect '''

from json import dump, load
from os import path, mkdir
from shutil import copyfile
from subprocess import call

from git import Repo, InvalidGitRepositoryError


#####################################################################
#                                                                   #
#                            EndPoints                              #
#                                                                   #
#####################################################################


def save_notebook(nb_dir, nb_name, tag_name=None):
    ''' Write updated UUIDS and git add/rm changed cell files '''

    notebook = open_notebook(nb_dir, nb_name)
    repo = open_repo(nb_dir, nb_name)
    #
    # Checkout master to get most recent copy of git log
    #
    # 'Force' forces the current repo state to be discarded so that the current
    # repo now matches the checked out commit exactly. This overwrite of the
    # repo state is what lets us move between commits where cells are being
    # created and deleted without cluttering up our repo.
    #
    repo.git.checkout('master', force=True)

    #
    # Write all current cells to their own files
    #
    write_cells(repo, notebook)

    #
    # Write copy of notebook to make restores easier
    #
    write_snapshot(nb_dir, nb_name)

    #
    # Update UUIDS file, get changed uuids
    #
    new_uuids, deleted_uuids = change_uuids(repo, notebook)

    #
    # Update git index
    #
    index = repo.index
    if new_uuids:
        index.add(new_uuids)
    if deleted_uuids:
        index.remove(deleted_uuids)
    index.add([uuid_filename(repo), get_snapshot_path(nb_dir, nb_name)])
    index.write_tree()

    if tag_name is None:
        index.commit('Unnamed save')
    else:
        index.commit('Tagged Checkpoint: {}'.format(tag_name))
        repo.git.tag(tag_name, get_log(repo)[0])

    repo.close()


def restore_snapshot(nb_dir, nb_name, rev):
    ''' Overwrite notebook (.ipynb) file with a previous version, specified by
        revision identifier 'rev', which can be a tag name or a commit hash
    '''
    repo = open_repo(nb_dir, nb_name)
    checkout_revision(repo, rev)
    write_notebook(nb_dir, nb_name)
    repo.close()


def rename_notebook(nb_dir, old_name, new_name):
    ''' Rename a notebook by renaming the git repo directory that backs it up.
        Jupyter already renames the .ipynb file
    '''
    old_path = get_repo_path(nb_dir, old_name)
    new_path = get_repo_path(nb_dir, new_name)

    #
    # NOTE: What to do about names with spaces
    #
    call(['mv', old_path, new_path])


def get_tag_list(nb_dir, nb_name):
    ''' Get an ordered list of git tags for this repo.
        Git tags are used to mark revisions the users specify '''
    repo = open_repo(nb_dir, nb_name)
    tags = repo.git.tag().split('\n')
    repo.close()
    return tags


def delete_notebook(nb_dir, nb_name):
    ''' Delete a notebook by erasing the git repo '''
    call(['rm', '-rf', get_repo_path(nb_dir, nb_name)])


#####################################################################
#                                                                   #
#                           Not Endpoints                           #
#                                                                   #
#####################################################################


def open_notebook(nb_dir, nb_name):
    ''' Load and return a Jupyter notebook specified by 'path' '''
    nb_path = get_nb_path(nb_dir, nb_name)
    with open(nb_path, 'r') as nb_file:
        notebook = load(nb_file)
    return notebook


def get_nb_path(nb_dir, nb_name):
    ''' Get full path of notebook (.ipynb) file '''
    return path.join(nb_dir, nb_name)


def open_repo(nb_dir, nb_name):
    ''' Load (or init if it does not exist) a git repo specified by 'path' '''
    repo_path = get_repo_path(nb_dir, nb_name)

    if not path.isdir(repo_path):
        mkdir(repo_path)

    try:
        return Repo(repo_path)
    except InvalidGitRepositoryError:
        #
        # Otherwise, init git repo and create an empty cell ordering file
        # Add and commit this file. Doing a non-empty commit creates the branch
        # 'master' that we assume exists in `update_repo`
        #
        repo = Repo.init(repo_path)
        with open(uuid_filename(repo), 'w+') as uuid_file:
            uuid_file.write('')
        write_snapshot(nb_dir, nb_name)
        index = repo.index
        index.add([uuid_filename(repo), get_snapshot_path(nb_dir, nb_name)])
        index.commit('Init {} repo'.format(nb_name))
        return repo


def get_repo_path(nb_dir, nb_name):
    ''' Get full path of git repo for specified notebook '''
    repo_name = get_repo_name(nb_name)
    repo_path = path.join(nb_dir, repo_name)
    return repo_path


def get_repo_name(nb_name):
    ''' Get name of repo directory for specified notebook '''
    return '.' + nb_name.split('.ipynb')[0] + '_repo'


def write_snapshot(nb_dir, nb_name):
    ''' Write snapshot of notebook, duplicating whole file '''
    notebook = open_notebook(nb_dir, nb_name)
    with open(get_snapshot_path(nb_dir, nb_name), 'w+') as snapshot:
        dump(notebook, snapshot)


def get_snapshot_path(nb_dir, nb_name):
    ''' Get full path of snapshot file '''
    return path.join(get_repo_path(nb_dir, nb_name), 'snapshot.ipynb')


def uuid_filename(repo):
    ''' Return the full path of the UUID order file for this repo '''
    return path.join(repo.working_tree_dir, 'UUIDS')


def get_log(repo):
    ''' Get list of commits for this repo. Returns list of GitPython.Commit
        objects
    '''
    return repo.iter_commits()


def write_cells(repo, notebook):
    ''' Write all notebook cells from nb into repo, one cell per file '''
    if repo.working_tree_dir is None:
        raise Exception('Repo not initialized correctly')

    for cell in notebook['cells']:
        cell_filename = path.join(repo.working_tree_dir,
                                  cell['metadata']['uuid'])
        with open(cell_filename, 'w+') as cell_file:
            dump(cell, cell_file)


def change_uuids(repo, notebook):
    ''' Handle uuid processing. Get list of added and deleted uuids. Write
        updated list to uuid file and return tuple of added and deleted uuids
    '''
    previous_uuids = uuids_from_git(repo)
    current_uuids = uuids_from_notebook(notebook)

    new_uuids = added_uuids(previous_uuids, current_uuids)
    deleted_uuids = removed_uuids(previous_uuids, current_uuids)

    #
    # Even if no cells added or removed, write to ensure correct order
    #
    write_uuids(repo, current_uuids)

    return (new_uuids, deleted_uuids)


def uuids_from_git(repo):
    ''' Read the uuid file and return a list of uuids from previous commit '''
    with open(uuid_filename(repo), 'r') as uuid_file:
        uuids = uuid_file.read().splitlines()
    return uuids


def uuids_from_notebook(notebook):
    ''' Read Notebook and return the list of uuids, sorted by cell order '''
    return [cell['metadata']['uuid'] for cell in notebook['cells']]


def added_uuids(previous, current):
    ''' Return a list of cell uuids that have just been created (ie. are present
        in the current notebook but not yet in the git repo)
    '''
    return list(set(current) - set(previous))


def removed_uuids(previous, current):
    ''' Return a list of cell uuids that have been deleted (ie. are present in
        the git repo but not in the current notebook)
    '''
    return list(set(previous) - set(current))


def write_uuids(repo, uuids):
    ''' Write contents of uuiids list to uuid file in specified repo '''
    with open(uuid_filename(repo), 'w') as uuid_file:
        for uuid in uuids:
            uuid_file.write('{}\n'.format(uuid))


def checkout_revision(repo, rev):
    ''' Update repo to revision id rev '''
    if rev == "elena":
        logs = get_log(repo)
        for log in logs:
            print("Log: {}".format(log))
            rev = log
    print("Checking out {}".format(rev))
    repo.git.checkout(rev, force=True)


def write_notebook(nb_dir, nb_name):
    ''' Write a new notebook given a repo state '''
    ''' Work In Progress reconstruction. For now, restore from snapshot
    uuids = uuids_from_git(repo)
    with open(nb_path + '.tmp', 'a') as temp_nb_file:
        for uuid in uuids:
            with open(path.join(repo.working_tree_dir, uuid), 'r') as cell_file:
                dump(load(cell_file), temp_nb_file, indent=4)
    rename(nb_path + '.tmp', nb_path)
    '''

    snapshot = get_snapshot_path(nb_dir, nb_name)
    nb_path = get_nb_path(nb_dir, nb_name)
    copyfile(snapshot, nb_path)
