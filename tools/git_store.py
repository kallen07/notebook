#!/usr/bin/python3

''' Utilities for Git-Notebook interconnect '''

from json import dump, load
from os import rename, path

from git import Repo
from git.repo.fun import is_git_dir


'''
    Example Usage (Notebook --> Git):
        nb = open_notebook(nb_path)
        repo = open_repo(repo_path)
        update_repo(repo, nb)
        repo.close()

    Example Usage (Git --> Notebook):
        repo = open_repo(repo_path)
        checkout_revision(repo, revision)
        write_notebook(repo, nb_path)
        repo.close()
'''


def open_notebook(nb_path):
    ''' Load and return a Jupyter notebook specified by 'path' '''
    with open(nb_path, 'r') as nb_file:
        notebook = load(nb_file)
    return notebook


def open_repo(nb_path):
    ''' Load (or init if it does not exist) a git repo specified by 'path' '''
    if is_git_dir(nb_path):
        return Repo(nb_path)

    #
    # Otherwise, init git repo and create an empty cell ordering file
    #
    repo = Repo.init(nb_path)
    with open(uuid_filename(repo), 'w+') as uuid_file:
        uuid_file.write('\n')
    return repo


def write_cells(repo, notebook):
    ''' Write all notebook cells from nb into repo, one cell per file '''
    if repo.working_tree_dir is None:
        raise Exception('Repo not initialized correctly')

    for cell in notebook['cells']:
        cell_filename = path.join(repo.working_tree_dir,
                                  cell['metadata']['uuid'])
        with open(cell_filename, 'w+') as cell_file:
            dump(cell, cell_file)


def write_uuids(repo, uuids):
    ''' Write contents of uuiids list to uuid file in specified repo '''
    with open(uuid_filename(repo), 'w') as uuid_file:
        for uuid in uuids:
            uuid_file.write('{}\n'.format(uuid))


def uuids_from_git(repo):
    ''' Read the uuid file and return a list of uuids from previous commit '''
    with open(uuid_filename(repo), 'r') as uuid_file:
        uuids = uuid_file.read().splitlines()
    return uuids


def uuids_from_notebook(notebook):
    ''' Read Notebook and return the list of uuids, sorted by cell order '''
    return [cell['metadata']['uuid'] for cell in notebook['cells']]


def removed_uuids(previous, current):
    ''' Return a list of cell uuids that have been deleted (ie. are present in
        the git repo but not in the current notebook)
    '''
    return list(set(previous) - set(current))


def added_uuids(previous, current):
    ''' Return a list of cell uuids that have just been created (ie. are present
        in the current notebook but not yet in the git repo)
    '''
    return list(set(current) - set(previous))


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


def update_repo(repo, notebook):
    ''' Write updated UUIDS and git add/rm changed cell files '''
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
    index.add(['UUIDS'])
    index.write_tree()
    index.commit('a commit message')


def uuid_filename(repo):
    ''' Return the full path of the UUID order file for this repo '''
    return path.join(repo.working_tree_dir, 'UUIDS')


def checkout_revision(repo, rev):
    ''' Update repo to revision id rev '''
    repo.head.reference = repo.commit(rev)
    repo.head.reset(index=True, working_tree=True)


def write_notebook(repo, nb_path):
    ''' Write a new notebook given a repo state '''
    uuids = uuids_from_git(repo)
    with open(nb_path + '.tmp', 'a') as temp_nb_file:
        for uuid in uuids:
            with open(path.join(repo.working_tree_dir, uuid), 'r') as cell_file:
                dump(load(cell_file), temp_nb_file, indent=4)
    rename(nb_path + '.tmp', nb_path)
