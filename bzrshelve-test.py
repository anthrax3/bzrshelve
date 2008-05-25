import os
import os.path
import shutil
import tempfile
import unittest
import exceptions

import bzrlib.errors

import bzrshelve

class OpenCloseTests(unittest.TestCase):
  def setUp(self):
    self.workdir = tempfile.mkdtemp()

  def tearDown(self):
    shutil.rmtree(self.workdir)

  def test_open_new(self):
    shelf = bzrshelve.open(self.workdir)
    assert shelf is not None

  def test_open_nonexistant(self):
    fakedir = tempfile.mkdtemp()
    os.rmdir(fakedir)

    self.assertRaises(bzrlib.errors.NoSuchFile,
                      bzrshelve.open, os.path.join(fakedir, 'a'))

  def test_close_new(self):
    assert not bzrshelve.open(self.workdir).close()

class KeyValueTests(OpenCloseTests):
  def setUp(self):
    OpenCloseTests.setUp(self)
  
    self.shelf = bzrshelve.open(self.workdir)

  def tearDown(self):
    self.shelf.close()

  def test_basic_set(self):
    self.shelf['foobar'] = 'abc123'

    self.assertEqual('abc123', self.shelf['foobar'])

  def test_basic_delete(self):
    self.shelf['foobar'] = 'abc123'
    del self.shelf['foobar']

    def test():
      return self.shelf['foobar']

    self.assertRaises(exceptions.KeyError, test)
