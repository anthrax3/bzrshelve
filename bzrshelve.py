from __future__ import with_statement

import contextlib
import hashlib
import os
import os.path
import shelve
import sys
import UserDict

import bzrlib.errors
from bzrlib import bzrdir

# Extension for key index files.
INDEX_MARK = 'key'
INDEX_EXT = os.path.extsep + INDEX_MARK

def open(dirname, writeback = False):
  """Open a persistent dictionary for reading and writing."""

  return BzrShelve(dirname, writeback)

@contextlib.contextmanager
def _bzr_workingtree_lock(wt, mode = 'r'):
  """Manage the locking of a Bazaar WorkingTree for with-statements."""

  if 'r' in mode:
    wt.lock_read()
  elif 'w' in mode:
    wt.lock_write()
  else:
    raise ValueError("Mode string but begin with 'r' or 'w'.")

  try:
    yield wt
  finally:
    wt.unlock()

class BzrShelve(shelve.Shelf):
  """Shelf implementation build on Bazaar."""

  def __init__(self, dirname, writeback = False):
    shelve.Shelf.__init__(self, BzrDatabase(dirname), None, writeback)

  def commit(self, message, keys = None):
    """Commit changes with an associated message.

    By default, this will commit all changes. Use "keys" to specify a limit."""

    return this.dict.sync(message, keys)

class BzrDatabase(UserDict.DictMixin):
  def __init__(self, dirname):
    """Open a Bazaar backed key-value store based on strings."""

    try:
      # Check for an existing repository.
      bzr_directory = bzrdir.BzrDir.open(dirname)
    except bzrlib.errors.NotBranchError:
      # Create a new working tree.
      wt = bzrdir.BzrDir.create_standalone_workingtree(dirname)
    else:
      # Open the existing working tree.
      wt = bzr_directory.open_workingtree()

    self.workingtree = wt

  def _key_hash(self, key):
    return hashlib.sha512(key).hexdigest()

  def sync(self, message = None, keys = None):
    """Commit the history."""

    # Make a default message.
    if message is None:
      message = "%s (%u)" % (sys.argv[0], os.getpid())

    with _bzr_workingtree_lock(self.workingtree, 'w') as wt:
      if keys:
        # Write the specified keys and indexs.
        key_ids = [self._key_hash(key) for key in keys]
        key_paths = [wt.id2path(key_id) for key_id in key_ids]
        index_paths = [key_path + INDEX_EXT for key_path in key_paths]

        return wt.commit(message, specific_files = key_paths + index_paths)
      else:
        # Write all keys and indexes.
        return wt.commit(message)

  def __getitem__(self, key):
    key_id = self._key_hash(key)

    with _bzr_workingtree_lock(self.workingtree) as wt:
      # Ensure the key exists.
      if not wt.has_id(key_id):
        raise KeyError(key)

      # Return the value.
      return wt.get_file_text(key_id)

  def __setitem__(self, key, value):
    key_id = self._key_hash(key)

    with _bzr_workingtree_lock(self.workingtree, 'w') as wt:
      # Does the key exist?
      has_key = wt.has_id(key_id)

      # Get a key path.
      if has_key:       # Lookup
        key_path = wt.id2abspath(key_id)
      else:             # Generate
        key_path = wt.abspath(key_id)

      # Write the value.
      with file(key_path, 'w') as key_file:
        key_file.write(value)

      if not has_key:
        # Write the index.
        index_path = key_path + INDEX_EXT
        with file(index_path, 'w') as index_file:
          index_file.write(key)
          
        # Add the files.
        add_paths = [wt.relpath(path) for path in (key_path, index_path)]
        wt.add(files = add_paths, ids = [key_id, INDEX_MARK + key_id])

  def __delitem__(self, key):
    key_id = self._key_hash(key)

    with _bzr_workingtree_lock(self.workingtree, 'w') as wt:
      # Ensure the key exists.
      if not wt.has_id(key_id):
        raise KeyError(key)

      # Delete the key.
      key_path = wt.id2path(key_id)
      wt.remove(key_path, force = True)

      # Delete the index.
      wt.remove(key_path + INDEX_EXT, force = True)

  def keys(self):
    """List of keys."""

    with _bzr_workingtree_lock(self.workingtree) as wt:
      return [wt.get_file_text(key_id)
              for key_id in wt
              if key_id.startswith(INDEX_MARK)]

  def __contains__(self, key):
    key_id = self._key_hash(key)

    with _bzr_workingtree_lock(self.workingtree) as wt:
      return wt.has_id(key_id)
