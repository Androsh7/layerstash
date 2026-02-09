# Layerstash

Layerstash is a tool designed to store large files as image layers in container registries such as GHCR or Docker Hub. Files exceeding 5GB will be uploaded and downloaded as separate ~5GB image layers.

Tag schema: `<BASE_TAG>-<CHUNK_NUMBER>`

## Why does this exist?

While most storage providers (Google Drive, OneDrive, Dropbox, AWS, etc) charge for storage above a certain low minimum, Docker Hub ([disclaimer](https://docs.docker.com/docker-hub/usage/)) and GHCR ([disclaimer](https://docs.github.com/en/billing/concepts/)) provide unlimited storage for free accounts.

In my personal testing, I have stored a total of 1.8TB in a public repository on Docker Hub [androsh7/archive](https://hub.docker.com/repository/docker/androsh7/archive/general).

## Legal Disclaimer

Layerstash is not affiliated with or endorsed by Docker, GitHub, or any container registry provider. Users are responsible for complying with the Terms of Service and acceptable use policies of any registry they interact with. Registry providers may impose rate limits, storage limits, or account restrictions at their discretion.

## Security Disclaimer

Data is stored as-is inside container image layers. Do not upload secrets or sensitive data unless it is encrypted beforehand.

## Download

```
usage: layerstash download [-h] [--version] [--log-level {trace,debug,info,warning,critical}] -r REPOSITORY -t BASE_TAG --registry {docker,ghcr} -o OUTFILE [-u USERNAME] [-p TOKEN]

options:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  --log-level {trace,debug,info,warning,critical}
                        Set the application log level
  -r, --repository REPOSITORY
                        Name of the remote repository, i.e., androsh7/archive
  -t, --base-tag BASE_TAG
                        The base tag, i.e., "python-ftp" , each chunk will have "-<INDEX>" appended to the end
  --registry {docker,ghcr}
                        The registry to use ('docker', 'ghcr'), default: "docker"
  -o, --outfile OUTFILE
                        The file to write the downloaded chunks to
  -u, --username USERNAME
                        Docker username
  -p, --token TOKEN     Docker PAT token
```

Examples:

```
# Download without authentication (only possible for public repositories)
layerstash download -r androsh7/archive -t python-ftp -o python-ftp.tar

# Download with authentication
layerstash download -r androsh7/archive -t python-ftp -o python-ftp.tar -u androsh7 -p docker_pat_23492dx1c75812375dx82375
```

Note: Downloads can be resumed by rerunning the same command

## Upload

```
usage: layerstash upload [-h] [--version] [--log-level {trace,debug,info,warning,critical}] -r REPOSITORY -t BASE_TAG --registry {docker,ghcr} -i INFILE [--overwrite] -u USERNAME
                         -p TOKEN

options:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  --log-level {trace,debug,info,warning,critical}
                        Set the application log level
  -r, --repository REPOSITORY
                        Name of the remote repository, i.e., androsh7/archive
  -t, --base-tag BASE_TAG
                        The base tag, i.e., "python-ftp" , each chunk will have "-<INDEX>" appended to the end
  --registry {docker,ghcr}
                        The registry to use ('docker', 'ghcr'), default: "docker"
  -i, --infile INFILE   The file to upload
  --overwrite           Overwrite existing images if they have a different hash
  -u, --username USERNAME
                        Docker username
  -p, --token TOKEN     Docker PAT token
```

Examples:

```
# Docker upload
layerstash upload -r androsh7/archive -t python-ftp -i python-ftp.tar -u androsh7 -p docker_pat_23492dx1c75812375dx82375

# GHCR upload
layerstash upload --registry ghcr -r androsh7/archive -t python-ftp -i python-ftp.tar -u androsh7 -p docker_pat_23492dx1c75812375dx82375
```

## Development

To run the repository locally:

```
git clone https://github.com/androsh7/layerstash
cd layerstash
python3 -m venv .venv # Recommended to use python3.13
pip install -e .[dev]
python3 layerstash/main.py
```

To build the executables, use the `build.py` script:

```
usage: build.py [-h] [--windows] [--linux] [--build-all]

options:
  -h, --help   show this help message and exit
  --windows    Build the Windows executable
  --linux      Build the Linux executable
  --build-all  Build the Windows and Linux executable
```
