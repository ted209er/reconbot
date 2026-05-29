# Tool Installation

Reconbot calls external recon tools through small Python wrappers. Install these
binaries yourself, then confirm they are available on `PATH`.

Required tools for the current workflow:

- `subfinder`
- `httpx`
- `gau`

## Ubuntu 20.04+

Install Python and Go:

```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip golang-go
```

Install the recon tools:

```bash
go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install github.com/projectdiscovery/httpx/cmd/httpx@latest
go install github.com/lc/gau/v2/cmd/gau@latest
```

Add Go-installed binaries to your shell path:

```bash
echo 'export PATH="$HOME/go/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

## WSL Ubuntu

Use the same commands as Ubuntu inside your WSL shell:

```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip golang-go
go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install github.com/projectdiscovery/httpx/cmd/httpx@latest
go install github.com/lc/gau/v2/cmd/gau@latest
echo 'export PATH="$HOME/go/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

Run Reconbot from the WSL filesystem, such as `~/Repos/reconbot`, rather than a
mounted Windows path when possible.

## macOS

Install Python and Go with your preferred package manager, then install the
tools with Go:

```bash
go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install github.com/projectdiscovery/httpx/cmd/httpx@latest
go install github.com/lc/gau/v2/cmd/gau@latest
```

Add Go-installed binaries to your shell path:

```bash
echo 'export PATH="$HOME/go/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

## Reconbot Setup

From the repo root:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
make validate
```

## Verify Tools

```bash
subfinder -version
httpx -version
gau --help
```

## Run Reconbot

```bash
reconbot --domain example.com --config configs/default.yaml
```

Use only domains you own or have explicit written authorization to test.

## Troubleshooting

### Missing Binary Errors

If Reconbot reports a missing binary, run the matching verification command:

```bash
subfinder -version
httpx -version
gau --help
```

If the command fails, install the tool or update `configs/default.yaml` to point
`binary` at the full executable path.

### PATH Issues

Go usually installs binaries into `~/go/bin`. Confirm your shell can find them:

```bash
which subfinder
which httpx
which gau
```

If these commands print nothing, add Go binaries to `PATH` and reopen your
terminal:

```bash
export PATH="$HOME/go/bin:$PATH"
```

### Virtualenv Issues

If `make validate` says `.venv` is missing, recreate the local environment:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Makefile targets use `.venv/bin/...` directly, so the `.venv` directory must
exist in the repo root.
