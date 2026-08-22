# Languages
brew "go"          # programming language with built-in concurrency
brew "node"        # JavaScript runtime built on V8
brew "python"      # latest Python for general development
brew "typescript"  # typed superset of JavaScript that compiles to plain JS

# Development Tools
brew "ansible"     # provisioning; bundles the collections ansible/ needs
brew "bazelisk"    # Bazel launcher (auto-switches per .bazelversion)
brew "direnv"      # load/unload environment variables per directory
brew "cloc"        # code statistics
brew "git"         # distributed version control system
brew "gh"          # GitHub's official command line tool
brew "git-lfs"     # large-file storage; gitconfig marks the lfs filter required
brew "hyperfine"   # command-line benchmarking tool
brew "just"        # command runner for project-specific tasks
brew "lazygit"     # simple terminal UI for git commands
brew "pnpm"        # fast, disk space efficient package manager
brew "uv"          # extremely fast Python package manager and resolver
brew "vite"        # next generation frontend tooling
brew "util-linux"  # GNU column, getopt, flock, and friends (macOS ships BSD variants)

# Shell
brew "atuin"       # magical shell history database with sync
brew "bash"        # GNU Bourne Again SHell
brew "eza"         # modern ls replacement with icons and git integration
brew "starship"    # minimal, blazing-fast shell prompt
brew "zellij"      # modern terminal multiplexer written in Rust
brew "zoxide"      # smarter cd command that learns your habits
brew "zsh"         # extended Bourne shell with many improvements

# CLI Utilities
brew "bat"         # cat clone with syntax highlighting and Git integration
brew "btop"        # resource monitor with a rich terminal UI
brew "fd"          # simple, fast alternative to find
brew "ripgrep"     # ultra-fast grep with smart defaults
brew "jq"          # lightweight JSON processor
brew "yamllint"    # linter for YAML files
brew "yq"          # lightweight YAML processor
brew "watch"       # execute a command periodically

# Cloud Tools
brew "aws-cdk"                  # AWS Cloud Development Kit for infrastructure as code
brew "awscli"                   # official AWS command-line interface
brew "awscurl"                  # curl wrapper for AWS API calls with sigv4
brew "awslogs"                  # query and stream CloudWatch logs
brew "azure-cli"                # Microsoft Azure command-line interface
tap "hashicorp/tap"             # HashiCorp official tap
brew "hashicorp/tap/terraform", trusted: true  # infrastructure as code tool for cloud provisioning
tap "openfga/tap"               # OpenFGA official tap
brew "openfga/tap/fga", trusted: true          # OpenFGA/Auth0 FGA command-line interface

# Network Tools
brew "bind"        # includes dig, nslookup, and other DNS utilities
brew "curlie"      # curl with the ease of httpie
brew "doggo"       # command-line DNS client like dig
brew "wget"        # retrieve files from the web

# Media Tools
brew "ffmpeg"      # record, convert and stream audio/video
brew "exiftool"    # read and write EXIF metadata
brew "imagemagick" # create, edit, compose, or convert bitmap images
brew "libicns"     # library and tools for manipulating Mac OS icns files
brew "yt-dlp"      # download videos from YouTube and other sites

# Fonts
cask "font-caskaydia-cove-nerd-font"   # Microsoft's modern terminal font with icons
cask "font-fira-code-nerd-font"        # monospaced font with programming ligatures and icons
cask "font-jetbrains-mono-nerd-font"   # JetBrains IDE font with ligatures and icons
cask "font-zed-mono-nerd-font"         # Zed editor font with icons

# macOS only (no Linux formula/cask available)
if OS.mac?
  cask "codex"        # OpenAI's coding assistant (use npm on Linux)
  cask "gcloud-cli"   # Google Cloud CLI (use apt/dnf on Linux)
end

if OS.linux?
  tap "auth0/auth0-cli"
  brew "auth0/auth0-cli/auth0", trusted: true  # Auth0 command-line interface
end
