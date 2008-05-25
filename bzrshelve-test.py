import os
import os.path
import shutil
import tempfile
import unittest

import bzrlib.errors

import bzrshelve

test_data = {'str': 'abc123', 'num': 4321, 'float': 1.234,
             'list': list(), 'dict': dict(), 'tuple': tuple()}

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
    """Open shelf in a non-existent directory."""

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

    OpenCloseTests.tearDown(self)

  def test_set(self):
    """Set a key."""

    self.shelf['foobar'] = 'abc123'

    self.assertEqual('abc123', self.shelf['foobar'])

  def test_delete(self):
    """Set and delete a key."""

    self.shelf['foobar'] = 'abc123'
    del self.shelf['foobar']

    def test():
      return self.shelf['foobar']

    self.assertRaises(KeyError, test)

  def test_overwrite_value_short(self):
    """Overwrite a key with a shorter value."""

    self.shelf['foobar'] = 'abc123'
    self.shelf['foobar'] = 'a'

    self.assertEqual('a', self.shelf['foobar'])

  def test_overwrite_value_long(self):
    """Overwrite a key with a longer value."""

    self.shelf['foobar'] = 'abc123'
    self.shelf['foobar'] = 'abc1234'

    self.assertEqual('abc1234', self.shelf['foobar'])

  def test_overwrite_value_short_synced(self):
    """Overwrite a key with a shorter value. (synced)"""

    self.shelf['foobar'] = 'abc123'
    self.shelf.sync()

    self.shelf['foobar'] = 'a'
    self.shelf.sync()

    self.assertEqual('a', self.shelf['foobar'])

  def test_overwrite_value_long_synced(self):
    """Overwrite a key with a longer value. (synced)"""

    self.shelf['foobar'] = 'abc123'
    self.shelf.sync()

    self.shelf['foobar'] = 'abc1234'
    self.shelf.sync()

    self.assertEqual('abc1234', self.shelf['foobar'])

  def test_set_delete_set(self):
    """Repeated set and delete a key."""

    def test():
      return self.shelf['foobar']

    self.shelf['foobar'] = 'abc123'
    self.assertEqual('abc123', self.shelf['foobar'])

    del self.shelf['foobar']
    self.assertRaises(KeyError, test)

    self.shelf['foobar'] = 'abc'
    self.assertEqual('abc', self.shelf['foobar'])

    del self.shelf['foobar']
    self.assertRaises(KeyError, test)

  def test_keys_index(self):
    """Get a list of keys."""

    keys = ['abc', '123', 'longishstringnamewith somet places in it']

    for key in keys:
      self.shelf[str(key)] = key

    for key in keys:
      self.assertTrue(key in self.shelf)
      self.assertTrue(key in self.shelf.keys())

  def test_keys_index_synced(self):
    """Get a list of keys. (synced)"""

    keys = ['abc', '123', 'longishstringnamewith somet places in it']

    for key in keys:
      self.shelf[str(key)] = key
      self.shelf.sync()

    for key in keys:
      self.assertTrue(key in self.shelf)
      self.assertTrue(key in self.shelf.keys())

  def test_update(self):
    """Use the dictionary update interface."""

    self.shelf.update(test_data)
    self.shelf.sync()

    for key, value in test_data.iteritems():
      self.assertEquals(value, self.shelf[key])

class RoundtripTests(OpenCloseTests):
  def setUp(self):
    OpenCloseTests.setUp(self)

    # Open a new shelf.
    shelf = bzrshelve.open(self.workdir)

    # Fill the shelf with test data.
    shelf.update(test_data)
    shelf.sync()

    # Create and delete a key.
    shelf['foobar'] = 'abc123'
    del shelf['foobar']

    shelf.close()

    # Reopen the shelf for testing.
    self.shelf = bzrshelve.open(self.workdir)

  def tearDown(self):
    self.shelf.close()

    OpenCloseTests.tearDown(self)

  def test_check_data(self):
    """Reload test data."""

    for key, value in test_data.iteritems():
      self.assertEquals(value, self.shelf[key])

  def test_deleted_data(self):
    """Check if deleted keys are gone."""

    def test():
      return self.shelf['foobar']

    self.assertRaises(KeyError, test)
