#!/usr/bin/env python

import argparse, subprocess, os, logging, zipfile
from datetime import datetime
from progress.bar import Bar

class Keeper:

    def __init__(self, show_progress):
        self.count = 0
        self.bar = None
        self.show_progress = show_progress
        # Directories to include in backup and restore
        self.source_directories = [
            # "/var/lib/rundeck/data",            # database
            # "/var/lib/rundeck/logs",            # execution logs (by far biggest)
            # "/var/lib/rundeck/.ssh",            # ssh keys
            # "/var/lib/rundeck/var/storage",     # key storage files and metadata
            "/var/rundeck/projects"             # project definitions
        ]

    def _rundeck_is_running(self):
        """
        Returns True if rundeckd is running, False otherwise
        """
        try:
            status = subprocess.check_output(["service", "rundeckd", "status"])
        except subprocess.CalledProcessError as error:
            if "rundeckd is not running" not in error.output:
                raise Exception("error running service command")
            else:
                status = error.output
        if "rundeckd is running" in status:
            return True
        else:
            return False

    def _add_directory_to_zip(self, zip_handle, path):

        for root, dirs, files in os.walk(path):
            logging.debug("directory: {}".format(root))
            for f in files:
                if self.show_progress:
                    self.bar.next()
                logging.debug("file: {}".format(f))
                zip_handle.write(os.path.join(root, f))


    def backup(self, destination_path, filename):
        # Start message
        logging.debug("starting backup")

        # Fail if backup dir is not found
        if not os.path.exists(destination_path):
            logging.error("backup directory {} not found".format(destination_path))
            raise Exception("could not find backup directory")

        file_path = os.path.join(destination_path, filename)
        logging.debug("using full backup path {}".format(file_path))

        if self.show_progress:
            # Count files in all directories
            logging.info("counting files...")
            for directory in self.source_directories:
                for root, dirs, files in os.walk(directory):
                    for f in files:
                        self.count += 1
            logging.debug("total number of files is {}".format(self.count))
            # Create progress bar
            self.bar = Bar('Processing', max=self.count)

        # Create zip file and save all directories to it
        # allowZip64 must be True to allow file size > 4GB
        with zipfile.ZipFile(file_path, 'w', allowZip64=True) as zip_file:
            for directory in self.source_directories:
                logging.info("adding directory {}".format(directory))
                self._add_directory_to_zip(zip_file, directory)
                print("") # To get the progress bar on separate line from
                          # log messages when printing log to stdout

        if self.show_progress:
            # Close progress bar
            self.bar.finish()

    def restore(self, filename):
        return

def main(arguments):
    # Refuse to do anything if RunDeck is running
    # This is best practice according to the docs:
    # http://rundeck.org/2.6.11/administration/backup-and-recovery.html
    if self._rundeck_is_running():
        logging.error("rundeckd cannot be running while you take a backup")
        raise Exception("rundeckd is still running")
    # Gather arguments
    parser_name = arguments.subparser_name
    debug_mode = arguments.debug
    if arguments.no_progress:
        show_progress = False
    else:
        show_progress = True

    # Enable debug logging if flag is set
    if debug_mode:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
    # Set up logging
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',level=log_level)

    keeper = Keeper(show_progress=show_progress)

    if parser_name == "backup":
        # Run backup
        keeper.backup(destination_path=arguments.dest,
                      filename=arguments.filename)
    elif parser_name == "restore":
        keeper.restore(filename=arguments.file)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='dinghy: helper for backup and restore of RunDeck')
    parser.add_argument('--debug',
                        '-d',
                        action='store_true',
                        help='enable debug logging')
    parser.add_argument('--no-progress',
                        action='store_true',
                        help='disable progress bar')

    subparsers = parser.add_subparsers(help='command help',
                                       dest='subparser_name')

    # Backup options
    backup_parser = subparsers.add_parser('backup', help='create a backup')
    backup_parser.add_argument('--dest',
                                type=str,
                                required=True,
                                help='path to write backup file to')
    backup_parser.add_argument('--filename',
                                type=str,
                                help='override the filename used the for backup file',
                                default='rundeck-backup-{}.zip'.format(
                            datetime.now().strftime('%Y-%M-%d--%H-%m-%S')))

    # Restore options
    restore_parsers = subparsers.add_parser('restore',
                                            help='restore from a backup file')
    restore_parser.add_argument('--file',
                                type=str,
                                help='path to backup file to restore from')
    main(parser.parse_args())
