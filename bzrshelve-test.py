import os
import os.path
import shutil
import tempfile
import unittest
import exceptions

import bzrlib.errors

import bzrshelve

class OpenCloseTests(unittest.TestCase):
  """Tests for open and close operations."""

  def setUp(self):
    self.workdir = tempfile.mkdtemp()

  def tearDown(self):
    shutil.rmtree(self.workdir)

  def test_open_new(self):
    """Create a new shelf."""

    shelf = bzrshelve.open(self.workdir)
    assert shelf is not None

  def test_open_nonexistent(self):
    """Try to open shelf in a non-existent directory."""

    fakedir = tempfile.mkdtemp()
    os.rmdir(fakedir)

    self.assertRaises(bzrlib.errors.NoSuchFile,
                      bzrshelve.open, os.path.join(fakedir, 'a'))

  def test_close_new(self):
    """Close an empty shelf."""

    assert not bzrshelve.open(self.workdir).close()

class DictionaryTests(OpenCloseTests):
  """Tests for dictionary operations."""

  def setUp(self):
    OpenCloseTests.setUp(self)
  
    self.shelf = bzrshelve.open(self.workdir)

  def tearDown(self):
    self.shelf.close()

  def test_basic_set(self):
    """Set a key."""

    self.shelf['foobar'] = 'abc123'

    self.assertEqual('abc123', self.shelf['foobar'])

  def test_basic_delete(self):
    """Set and delete a key."""

    self.shelf['foobar'] = 'abc123'
    del self.shelf['foobar']

    def test():
      return self.shelf['foobar']

    self.assertRaises(exceptions.KeyError, test)

  def test_overwrite_value_short(self):
    """Overwrite a key with a shorter value."""

    self.shelf['foobar'] = 'abc123'
    self.shelf['foobar'] = 'a'

    self.assertEqual('a', self.shelf['foobar'])

  def test_overwrite_value_short(self):
    """Overwrite a key with a longer value."""

    self.shelf['foobar'] = 'abc123'
    self.shelf['foobar'] = 'abc1234'

    self.assertEqual('abc1234', self.shelf['foobar'])

  def test_overwrite_value_short_synced(self):
    """Synchronously overwrite a key with a shorter value."""

    self.shelf['foobar'] = 'abc123'
    self.shelf.sync()

    self.shelf['foobar'] = 'a'
    self.shelf.sync()

    self.assertEqual('a', self.shelf['foobar'])

  def test_overwrite_value_short_synced(self):
    """Overwrite a key with a longer value."""

    self.shelf['foobar'] = 'abc123'
    self.shelf.sync()

    self.shelf['foobar'] = 'abc1234'
    self.shelf.sync()

    self.assertEqual('abc1234', self.shelf['foobar'])
