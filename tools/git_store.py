#!/usr/bin/python3

""" Utilities for Git-Notebook interconnect """

from git import Repo
from git.repo.fun import is_git_dir
from json import dump, load
from os import rename


"""
    Example Usage (Notebook --> Git):
        nb = open_notebook(nb_path)
        repo = open_repo(repo_path)
        update_repo(repo, nb)
        repo.close()

    Example Usage (Git --> Notebook):
        repo = open_repo(repo_path)
        checkout_revision(revision)
        write_notebook(repo, nb_path)
"""


def open_notebook(path):
    """ Load and return a Jupyter notebook specified by 'path' """
    with open(path, 'r') as f:
        nb = load(f)
    return nb


def open_repo(path):
    """ Load (or init if it does not exist) a git repo specified by 'path' """
    if is_git_dir(path):
        return Repo(path)
    else:
        return Repo.init(path)


def write_cells(repo, nb):
    """ Write all notebook cells from nb into repo, one cell per file """
    if repo.working_tree_dir is None:
        raise Exception("Repo not initialized correctly")

    for cell in nb['cells']:
        cell_filename = repo.working_tree_dir + cell['uuid']
        with open(cell_filename, 'w') as cell_file:
            dump(nb, cell_file)


def write_uuids(repo, uuids):
    """ Write contents of uuiids list to uuid file in specified repo """
    with open(uuid_filename(repo), 'w') as uuid_file:
        for uuid in uuids:
            uuid_file.write('{}\n'.format(uuid))


def uuids_from_git(repo):
    """ Read the uuid file and return a list of uuids from previous commit """
    with open(uuid_filename(repo), 'r') as uuid_file:
        uuids = uuid_file.read().splitlines()
    return uuids


def uuids_from_notebook(nb):
    """ Read Notebook and return the list of uuids, sorted by cell order """
    return [cell['uuid'] for cell in nb['cells']]


def removed_uuids(previous, current):
    """ Return a list of cell uuids that have been deleted (ie. are present in
        the git repo but not in the current notebook)
    """
    return list(set(previous) - set(current))


def added_uuids(previous, current):
    """ Return a list of cell uuids that have just been created (ie. are present
        in the current notebook but not yet in the git repo)
    """
    return list(set(current) - set(previous))


def change_uuids(repo, nb):
    """ Handle uuid processing. Get list of added and deleted uuids. Write
        updated list to uuid file and return tuple of added and deleted uuids
    """
    previous_uuids = uuids_from_git(repo)
    current_uuids = uuids_from_notebook(nb)

    new_uuids = added_uuids(previous_uuids, current_uuids)
    deleted_uuids = removed_uuids(previous_uuids, current_uuids)

    #
    # Even if no cells added or removed, write to ensure correct order
    #
    write_uuids(repo, current_uuids)

    return (new_uuids, deleted_uuids)


def update_repo(repo, nb):
    """ Write updated UUIDS and git add/rm changed cell files """
    #
    # Write all current cells to their own files
    #
    write_cells(repo, nb)

    #
    # Update UUIDS file, get changed uuids
    #
    new_uuids, deleted_uuids = change_uuids(repo, nb)

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
    """ Return the full path of the UUID order file for this repo """
    return repo.working_tree_dir + '/UUIDS'


def checkout_revision(repo, rev):
    """ Update repo to revision id rev """
    repo.checkout(rev)
    repo.index.write()


def write_notebook(repo, nb_path):
    """ Write a new notebook given a repo state """
    uuids = uuids_from_git(repo)
    with open(nb_path + '.tmp', 'a') as nb:
        for uuid in uuids:
            with open('{}/{}'.format(repo.working_tree_dir, uuid), 'r') as f:
                dump(nb, load(f))
    rename(nb_path + '.tmp', nb_path)
