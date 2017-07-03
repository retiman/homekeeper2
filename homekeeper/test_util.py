import homekeeper.testing
import homekeeper.util

os = None
cleanup_symlinks = homekeeper.util.cleanup_symlinks
create_symlinks = homekeeper.util.create_symlinks
firstdir = homekeeper.util.firstdir
prepare_target = homekeeper.util.prepare_target
restore = homekeeper.util.restore
shutil = None
testing = homekeeper.testing

class TestUtil(object):
    def setup_method(self):
        global os, shutil
        self.filesystem, os, shutil = testing.init()
        self.home = os.getenv('HOME')

    def teardown_method(self):
        del self.filesystem

    def test_create_symlinks(self):
        """Tests symlinking 'base/.vimrc' to '$HOME/.vimrc'."""
        source = os.path.join(testing.base_directory(), '.vimrc')
        target = os.path.join(self.home, '.vimrc')
        self.filesystem.CreateFile(source)
        assert os.path.exists(source)
        assert not os.path.exists(target)
        create_symlinks(testing.base_directory(), self.home)
        assert os.path.exists(source)
        assert os.path.exists(target)
        assert os.path.islink(target)
        assert source == os.readlink(target)

    def test_create_symlinks_with_excludes(self):
        """Tests that 'base/.vimrc' can be excluded from symlinking."""
        source = os.path.join(testing.base_directory(), '.vimrc')
        target = os.path.join(self.home, '.vimrc')
        excludes = ['.vimrc']
        self.filesystem.CreateFile(source)
        assert os.path.exists(source)
        assert not os.path.exists(target)
        create_symlinks(testing.base_directory(), self.home, excludes=excludes)
        assert os.path.exists(source)
        assert not os.path.exists(target)
        assert not os.path.islink(target)

    def test_create_symlinks(self):
        """Tests that only 'base/.config' is symlinked."""
        source = os.path.join(testing.base_directory(),
                              '.config',
                              'Terminal',
                              'terminalrc')
        target = os.path.join(self.home,
                              '.config',
                              'Terminal',
                              'terminalrc')
        self.filesystem.CreateFile(source)
        assert os.path.exists(source)
        assert not os.path.exists(target)
        create_symlinks(testing.base_directory(),
                        self.home,
                        excludes=None)
        assert os.path.exists(source)
        assert os.path.exists(target)
        assert os.path.islink(os.path.join(self.home, '.config'))
        expected = os.path.join(testing.base_directory(), '.config')
        result = os.readlink(os.path.join(self.home, '.config'))
        assert expected == result

    def test_cleanup_symlinks(self):
        """Tests that non-existant symlinks are removed."""
        self.filesystem.CreateFile('a.txt')
        os.symlink('a.txt', 'exists.txt')
        os.symlink('b.txt', 'nonexistent1.txt')
        os.symlink('c.txt', 'nonexistent2.txt')
        assert os.path.islink('nonexistent1.txt')
        assert os.path.islink('nonexistent2.txt')
        cleanup_symlinks('/')
        assert not os.path.exists('nonexistent1.txt')
        assert not os.path.exists('nonexistent2.txt')
        assert os.path.exists('exists.txt')

    def test_restore_file(self):
        """Tests symlinking 'base/.vimrc' to '$HOME/.vimrc' and then restoring
        will undo the action.
        """
        source = os.path.join(testing.base_directory(), '.vimrc')
        target = os.path.join(self.home, '.vimrc')
        self.filesystem.CreateFile(source)
        assert os.path.exists(source)
        assert not os.path.exists(target)
        create_symlinks(testing.base_directory(), self.home)
        restore(testing.base_directory(), self.home)
        assert os.path.exists(source)
        assert os.path.exists(target)
        assert not os.path.islink(source)
        assert not os.path.islink(target)

    def test_restore_directory(self):
        """Tests symlinking directory 'base/.foo' to '$HOME/.foo' and then
        restoring will undo the action.
        """
        source = os.path.join(testing.base_directory(), '.foo', 'bar')
        target = os.path.join(self.home, '.foo', 'bar')
        os.makedirs(source)
        shutil.rmtree(target)
        assert os.path.exists(source)
        assert not os.path.exists(target)
        create_symlinks(testing.base_directory(), self.home)
        restore(testing.base_directory(), self.home)
        assert os.path.exists(os.path.join(self.home, '.foo'))
        assert not os.path.islink(os.path.join(self.home, '.foo'))
        assert os.path.exists(os.path.join(self.home, '.foo', 'bar'))
        assert not os.path.islink(os.path.join(self.home, '.foo', 'bar'))

    def test_restore_with_excludes(self):
        """Test that excluded files are not restored."""
        source = os.path.join(testing.base_directory(), '.vimrc')
        unrelated = os.path.join(testing.base_directory(), '.git')
        excludes = ['.git']
        self.filesystem.CreateFile(source)
        self.filesystem.CreateFile(unrelated)
        assert os.path.exists(unrelated)
        assert not os.path.exists(os.path.join(self.home, '.git'))
        create_symlinks(testing.base_directory(), self.home, excludes=excludes)
        restore(testing.base_directory(), self.home, excludes=excludes)
        assert not os.path.exists(os.path.join(self.home, '.git'))

    def test_prepare_target(self):
        """Tests that targets are removed before symlinking."""
        target = os.path.join(self.home, '.vimrc')
        self.filesystem.CreateFile(target)
        assert os.path.exists(target)
        prepare_target(target)
        assert not os.path.exists(target)

    def test_prepare_target_creates_parent_directory(self):
        """Tests that target parent directories are created before symlinking.
        """
        target = os.path.join(self.home, '.foo', 'bar', 'bif')
        assert not os.path.exists(target)
        prepare_target(target)
        assert not os.path.exists(target)
        assert os.path.isdir(os.path.dirname(target))

    def test_firstdir(self):
        """Tests that the first directory of a path is returned."""
        assert 'home' == firstdir('home/johndoe/.vimrc')
        assert 'home' == firstdir('/home/johndoe/.vimrc')
        assert '.vimrc' == firstdir('.vimrc')
        assert not firstdir('')
        assert not firstdir('/')
