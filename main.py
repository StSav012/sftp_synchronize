# coding=utf-8
from __future__ import annotations

import argparse
import getpass
import os
from pathlib import Path
from stat import S_ISDIR, S_ISREG

import paramiko

if __name__ == '__main__':
    def main() -> None:
        ap: argparse.ArgumentParser = argparse.ArgumentParser(
            description='like rsync, update local files with remote ones via SFTP',
            formatter_class=argparse.RawTextHelpFormatter)
        ap.add_argument('--exclude', action='append', help='the file name to exclude; may be used several times')
        ap.add_argument('host', metavar='[user@]host',
                        help='the username and the remote host location\n'
                             'If username is omitted, current local username is used.')
        ap.add_argument('remote_path', help='the path on the remote host to copy files from')
        ap.add_argument('local_path', help='the destination path on the local host')
        # # if no arguments, print help instead of usage
        ap.print_usage = ap.print_help
        args: argparse.Namespace = ap.parse_intermixed_args()

        sftp_url: str
        sftp_user: str
        if '@' in args.host:
            sftp_user, sftp_url = args.host.split('@', maxsplit=1)
        else:
            sftp_url = args.host
            sftp_user = getpass.getuser()
        sftp_pass: str = getpass.getpass('Password: ')

        remote_root: Path = Path(args.remote_path)
        local_root: Path = Path(args.local_path).expanduser()

        ssh: paramiko.SSHClient
        with paramiko.SSHClient() as ssh:
            # automatically add keys without requiring human intervention
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            ssh.connect(sftp_url, username=sftp_user, password=sftp_pass, timeout=1, compress=True)

            sftp: paramiko.sftp_client.SFTPClient
            with ssh.open_sftp() as sftp:

                def update_dir(remote_path: Path = Path('.')):
                    remote_dir: Path = remote_root / remote_path
                    local_dir: Path = local_root / remote_path
                    local_dir.mkdir(exist_ok=True)

                    files: list[paramiko.sftp_attr.SFTPAttributes] = sftp.listdir_attr(str(remote_dir))
                    file: paramiko.sftp_attr.SFTPAttributes

                    def get_file():
                        if (file.filename.startswith('~$')
                                or (file.filename.startswith('~') and file.filename.endswith('.tmp'))):
                            print('skipping', remote_dir / file.filename)
                            return
                        if args.exclude is not None and file.filename in args.exclude:
                            print('skipping', remote_dir / file.filename)
                            return
                        print('getting', remote_dir / file.filename)
                        try:
                            sftp.get(str(remote_dir / file.filename), str(local_dir / file.filename))
                        except OSError as ex:
                            print(f'{ex} when getting {remote_dir / file.filename}')
                        else:
                            os.utime(str(local_dir / file.filename), (file.st_atime, file.st_mtime))

                    for file in files:
                        if S_ISREG(file.st_mode):
                            if not (local_dir / file.filename).exists():
                                get_file()
                            else:
                                local_attributes: os.stat_result = (local_dir / file.filename).lstat()
                                if local_attributes.st_mtime != file.st_mtime:
                                    get_file()
                        elif S_ISDIR(file.st_mode):
                            update_dir(remote_path / file.filename)

                update_dir()


    main()
