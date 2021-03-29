import argparse
import importlib
import getpass
import os
import sys
from pathlib import Path
from typing import List, Type
from stat import S_ISDIR, S_ISREG

try:
    from typing import Final
except ImportError:
    class _Final:
        @staticmethod
        def __getitem__(item: Type):
            return item


    Final = _Final()

paramiko_package: Final[str] = 'paramiko'

try:
    paramiko = importlib.import_module(paramiko_package)
except (ImportError, ModuleNotFoundError) as ex:
    if sys.argv[0] == sys.executable:  # if embedded
        raise ex

    import subprocess

    if subprocess.check_call([sys.executable, '-m', 'pip', 'install', paramiko_package]):
        if __name__ == '__main__':
            print(f'Module `{paramiko_package}` can not be loaded. Make sure it is installed.')
            sys.exit(1)
        else:
            raise ex
    else:
        paramiko = importlib.import_module(paramiko_package)


if __name__ == '__main__':
    def main():
        ap: argparse.ArgumentParser = argparse.ArgumentParser(
            description='like rsync, update local files with remote ones via SFTP',
            formatter_class=argparse.RawTextHelpFormatter)
        ap.add_argument('--exclude', action='append', help='the file name to exclude; may be used several times')
        ap.add_argument('host', metavar='[user@]host',
                        help='the username and the remote host location\n'
                             'If username is omitted, current local username is used.')
        ap.add_argument('remote_path', help='the path on the remote host to copy files from')
        ap.add_argument('local_path', help='the destination path on the local host')
        # https://stackoverflow.com/a/4042861/8554611
        if len(sys.argv) == 1:
            ap.print_help(sys.stderr)
            sys.exit(1)
        args: argparse.Namespace = ap.parse_args()

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

        ssh: paramiko.SSHClient = paramiko.SSHClient()
        # automatically add keys without requiring human intervention
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        ssh.connect(sftp_url, username=sftp_user, password=sftp_pass, timeout=1)

        sftp: paramiko.sftp_client.SFTPClient = ssh.open_sftp()

        def update_dir(remote_path: Path = Path('.')):
            remote_dir: Path = remote_root / remote_path
            local_dir: Path = local_root / remote_path
            local_dir.mkdir(exist_ok=True)

            files: List[paramiko.sftp_attr.SFTPAttributes] = sftp.listdir_attr(str(remote_dir))
            file: paramiko.sftp_attr.SFTPAttributes

            def get_file():
                if file.filename.startswith('~$') or (file.filename.startswith('~') and file.filename.endswith('.tmp')):
                    print('skipping', remote_dir / file.filename)
                    return
                if args.exclude is not None and file.filename in args.exclude:
                    print('skipping', remote_dir / file.filename)
                    return
                print('getting', remote_dir / file.filename)
                sftp.get(str(remote_dir / file.filename), str(local_dir / file.filename))
                os.utime(str(local_dir / file.filename), (file.st_atime, file.st_mtime))

            for file in files:
                if S_ISREG(file.st_mode):
                    if not (local_dir / file.filename).exists():
                        get_file()
                    else:
                        local_attributes = (local_dir / file.filename).lstat()
                        if local_attributes.st_mtime != file.st_mtime:
                            get_file()
                elif S_ISDIR(file.st_mode):
                    update_dir(remote_path / file.filename)

        update_dir()

    main()
