# Like `rsync`, but without `rsync`

Suitable for systems without `rsync`, just with `sftp`.

The files are checked by their modification time to determine
whether they should be received. The modification time of the local files
is set identical to the remote values.

### Update local files with remote ones via SFTP

**Usage**: `main.py [-h] [--exclude EXCLUDE] [user@]host remote_path local_path`

Positional arguments:
* `[user@]host` is the username and the remote host location.
                If username is omitted, current local username is used.
* `remote_path` is the path on the remote host to copy files from.
* `local_path`  is the destination path on the local host.

Optional arguments:
* `-h` or `--help` to show this help message and exit.
* `--exclude EXCLUDE` is the file name to exclude; may be used several times.
