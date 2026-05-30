# Tool Installation

Reconbot calls external recon tools through small Python wrappers. Install the
binaries yourself, confirm they are on `PATH`, then run the local validation
target before the first real recon run.

Use Reconbot only against assets you own or have explicit written authorization
to test.

## Supported Tools

| Feature | Tool | Local binary |
| --- | --- | --- |
| Subdomain Discovery | `subfinder` | `subfinder` |
| Subdomain Discovery | `assetfinder` | `assetfinder` |
| Certificate Transparency | `crt.sh` | `curl` |
| Historical URLs | `gau` | `gau` |
| Historical URLs | `waybackurls` | `waybackurls` |
| Fingerprinting | `httpx` | `httpx` |
| Screenshots | `gowitness` | `gowitness` |

`crt.sh` is a public web source, not an installed recon binary. Reconbot queries
it with `curl`.

## Ubuntu 20.04+

Install Python, Go, curl, and Chromium for screenshot support:

```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip golang-go curl chromium-browser
```

If your Ubuntu release does not provide `chromium-browser`, install `chromium`
instead:

```bash
sudo apt install chromium
```

Install the recon tools:

```bash
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install github.com/tomnomnom/assetfinder@latest
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest
go install github.com/lc/gau/v2/cmd/gau@latest
go install github.com/tomnomnom/waybackurls@latest
go install github.com/sensepost/gowitness@latest
```

Add Go-installed binaries to your shell path:

```bash
echo 'export PATH="$HOME/go/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

## WSL Ubuntu

Use the Ubuntu commands inside your WSL shell:

```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip golang-go curl chromium-browser
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install github.com/tomnomnom/assetfinder@latest
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest
go install github.com/lc/gau/v2/cmd/gau@latest
go install github.com/tomnomnom/waybackurls@latest
go install github.com/sensepost/gowitness@latest
echo 'export PATH="$HOME/go/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

Run Reconbot from the WSL filesystem, such as `~/Repos/reconbot` or
`~/Recon/company-a`, rather than a mounted Windows path when possible. This
avoids slow file I/O and path translation surprises.

## macOS

Install Python, Go, curl, and Chrome or Chromium with your preferred package
manager. With Homebrew:

```bash
brew install python@3.11 go curl
brew install --cask google-chrome
```

Install the recon tools:

```bash
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install github.com/tomnomnom/assetfinder@latest
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest
go install github.com/lc/gau/v2/cmd/gau@latest
go install github.com/tomnomnom/waybackurls@latest
go install github.com/sensepost/gowitness@latest
```

Add Go-installed binaries to your shell path:

```bash
echo 'export PATH="$HOME/go/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

## Verify Tools

Run these commands from a new terminal after updating `PATH`:

```bash
subfinder -version
assetfinder --help
httpx -version
gau --help
waybackurls --help
gowitness version
```

Also confirm `curl` is available for crt.sh lookups:

```bash
curl --version
```

If any command prints `command not found`, fix that tool before starting a
Reconbot run.

## First Run

From the repo root:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"

make validate

reconbot --help
reconbot --domain example.com --config configs/default.yaml
```

The first real run creates local `data/`, `reports/`, and `logs/` directories.
Reports include output paths, discovery source counts, technology summaries,
screenshot metadata, and changes compared with the previous run for the same
target.

## Running From A Workspace

Use a separate workspace directory when you want target-specific output outside
the Git checkout:

```text
~/Recon/company-a
```

Example:

```bash
mkdir -p ~/Recon/company-a
cd ~/Recon/company-a
/home/user/Repos/reconbot/.venv/bin/reconbot \
  --domain example.com \
  --config /home/user/Repos/reconbot/configs/default.yaml \
  --run-name first-run
```

Output paths in `configs/default.yaml` are relative. When you run from
`~/Recon/company-a`, Reconbot writes to `~/Recon/company-a/data`,
`~/Recon/company-a/reports`, and `~/Recon/company-a/logs`.

## Troubleshooting

### Missing Tool

Reconbot checks enabled tool binaries before running the workflow. If it reports
a missing tool, run the matching verification command:

```bash
subfinder -version
assetfinder --help
httpx -version
gau --help
waybackurls --help
gowitness version
curl --version
```

If the command fails, install the tool, reopen your terminal, or update the
matching `tools.<name>.binary` value in `configs/default.yaml` to the full
executable path.

### Missing Config

`reconbot --config` must point to an existing YAML file. From outside the repo,
use an absolute config path:

```bash
reconbot --domain example.com --config /home/user/Repos/reconbot/configs/default.yaml
```

From the repo root, the default works:

```bash
reconbot --domain example.com
```

### pyenv Issues

If `python3.11` is missing but you use pyenv, install and select Python 3.11:

```bash
pyenv install 3.11
pyenv local 3.11
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

If `make validate` still uses an old interpreter, remove and recreate `.venv`
from the selected Python:

```bash
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Go Installation Issues

Go installs binaries into `~/go/bin` by default. Confirm Go and the install
directory are visible:

```bash
go version
go env GOPATH
ls "$(go env GOPATH)/bin"
```

If the tools exist but your shell cannot find them, add Go's bin directory to
`PATH`:

```bash
export PATH="$(go env GOPATH)/bin:$PATH"
```

Persist that line in `~/.bashrc` for Ubuntu and WSL Ubuntu, or `~/.zshrc` for
macOS.

Some Go-installed tools, including `httpx` and `gowitness`, may require a newer
Go release than the one packaged by older operating systems. If `go install`
fails with a Go version error, install a current Go release from your OS package
manager, Homebrew, or the official Go downloads, then rerun the failed
`go install` command.
