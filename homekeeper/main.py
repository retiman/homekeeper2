import logging
import os
import shutil

from homekeeper.common import (cd, makedirs)


class Main(object):
    def remove(self, target):
        if os.path.islink(target):
            os.unlink(target)
            logging.debug('removed symlink %s', target)
        if os.path.isfile(target):
            os.remove(target)
            logging.debug('removed file %s', target)
        if os.path.isdir(target):
            shutil.rmtree(target)
            logging.debug('removed directory %s', target)

    def symlink(self, source, target, overwrite=True):
        """Removes a target symlink/file/directory before replacing it with
        symlink. Also creates the parent directory if it does not exist.

        Args:
            source: Original source of the symlink.
            target: Path of symlink target, can be file or directory.
        """
        dirname = os.path.dirname(target)
        if not os.path.exists(dirname):
            makedirs(dirname)
        if source == target:
            logging.debug('skipping %s; source and target are the same', source)
            return
        if os.path.exists(target) and not overwrite:
            logging.debug('will not overwrite; skipping %s', target)
            return
        self.remove(target)
        os.symlink(source, target)
        logging.info('symlinked %s -> %s', source, target)

    def restore(self, source, target, overwrite=True):
        """Restores a symlink to its target. Afterwards, the target will no
        longer be a symlink.

        Args:
            source: Original source of the symlink.
            target: Path of symlink target, can be file or directory.
            overwrite: Overwrite the target even if the doesn't exist.
        """
        if source == target:
            logging.debug('skipping %s; source and target are the same', source)
            return
        if not overwrite:
            if not os.path.exists(target):
                logging.debug('skipping missing resource: %s', target)
                return
            if not os.path.islink(target):
                logging.debug('skipping non-symlink resource: %s', target)
                return
            if os.readlink(target) != source:
                logging.debug('skipping symlink resource: %s', target)
                return
        self.remove(target)
        if os.path.isfile(source):
            logging.debug('copying file %s to %s', source, target)
            shutil.copy(source, target)
        elif os.path.isdir(source):
            logging.debug('copying directory %s to %s', source, target)
            shutil.copytree(source, target, symlinks=True)
        else:
            logging.info('skipping resource: %s', target)
        logging.info('restored %s -> %s', target, source)

    def create_symlinks(self, source_directory, target_directory,
                        excludes=set(), overwrite=True):
        """Symlinks files from the source directory to the target directory.

        For example, suppose that your `source_directory` is your dotfiles
        directory and contains a file named '.vimrc'.  If the `target_directory`
        is your home directory, then this is the result:

            $HOME/.vimrc -> $HOME/dotfiles/.vimrc

        The existing $HOME/.vimrc will be removed.

        Args:
            source_directory: The source directory where your dotfiles are.
            target_directory: The target directory for symlinking.
            excludes: An array of paths excluded from symlinking.
            overwrite: Overwrite existing files.
        """
        self.process_directories(source_directory, target_directory,
                                 self.symlink, excludes=excludes,
                                 overwrite=overwrite)

    def restore_symlinks(self, source_directory, target_directory,
                         excludes=set(), overwrite=True):
        """Realizes the symlinks files in the source directory that have been
        symlinked to the target directory.

        For example, suppose your home directory contains:

            $HOME/.vimrc -> $HOME/dotfiles/.vimrc

        Then the result will be:

            $HOME/.vimrc

        The $HOME/.vimrc file will contain to contains of $HOME/dotfiles/.vimrc.
        Any symlinks in the source directory that do not point to the target
        directory will not be restored.

        Args:
            source_directory: The source directory where your dotfiles are.
            target_directory: The target directory for symlinking.
            excludes: An array of paths excluded from symlinking.
            overwrite: Overwrite existing target even if it's not a symlink.
        """
        self.process_directories(source_directory, target_directory,
                                 self.restore, excludes=excludes,
                                 overwrite=overwrite)

    def cleanup_symlinks(self, directory):
        """Removes broken symlinks from a directory.

        Args:
            directory: The directory to look for broken symlinks.
        """
        for item in os.listdir(directory):
            pathname = os.path.join(directory, item)
            if not os.path.islink(pathname):
                continue
            if os.path.exists(os.readlink(pathname)):
                continue
            logging.info('removing broken link: %s', pathname)
            os.unlink(pathname)

    def process_directories(self, source_directory, target_directory, process,
                            excludes=set(), overwrite=True):
        if not os.path.isdir(source_directory):
            logging.info('dotfiles directory not found: %s', source_directory)
            return
        logging.info('restoring files in %s', target_directory)
        with cd(source_directory):
            for pathname in os.listdir('.'):
                logging.debug('examining %s', pathname)
                basename = os.path.basename(pathname)
                source = os.path.join(source_directory, basename)
                target = os.path.join(target_directory, basename)
                if basename in excludes:
                    logging.debug('skipping excluded resource: %s', basename)
                    continue
                process(source, target, overwrite=overwrite)