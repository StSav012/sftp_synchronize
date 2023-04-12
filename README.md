# Like `rsync`, but without `rsync`

Suitable for systems without `rsync`, just with `sftp`.

The files are checked by their modification time to determine
whether they should be received. The modification time of the local files
is set identical to the remote values.

### Update local files with remote ones via SFTP

**Usage**: `main.py [-h] [-s] [--exclude EXCLUDE] [--move] [user@]host remote_path local_path`

Positional arguments:
* `[user@]host` is the username and the remote host location.
                If username is omitted, current local username is used.
* `remote_path` is the path on the remote host to copy files from.
* `local_path`  is the destination path on the local host.

Optional arguments:
* `-h` or `--help` to show this help message and exit;
* `-s`, `--check-size` to fetch a remote file if its size differs from the one if the local file;
* `--exclude EXCLUDE` is the file name to exclude; may be used several times;
* `--move` to remove the remote file after receiving its copy.
