# Languages
brew "dart-sdk"    # client-optimized language for multi-platform apps
brew "dotnet"      # Microsoft's cross-platform .NET development framework
brew "ghc"         # Glasgow Haskell Compiler
brew "go"          # programming language with built-in concurrency
brew "llvm"        # C/C++/Objective-C compiler with clang frontend
brew "lua"         # lightweight, embeddable scripting language
brew "mono"        # cross-platform .NET runtime with mcs C# compiler
brew "node"        # JavaScript runtime built on V8
brew "perl"        # highly capable, feature-rich programming language
brew "php"         # general-purpose server-side scripting language
brew "python"      # latest Python for general development
brew "ruby"        # dynamic, object-oriented programming language
brew "rust"        # systems programming language focused on safety and performance
brew "swift"       # Apple's compiled programming language for all platforms
brew "openjdk"     # OpenJDK distribution (cross-platform)
brew "typescript"  # typed superset of JavaScript that compiles to plain JS
brew "zig"         # systems programming language with manual memory management

# Pinned versions for Tongues compatibility
brew "dotnet@8"    # .NET 8 for Tongues C# backend
brew "gcc@13"      # GCC 13 for Tongues C backend
brew "go@1.21"     # Go 1.21 for Tongues Go backend
brew "node@20"     # Node 20 for Tongues JS/TS backend (closest to Docker's 21)
brew "openjdk@21"  # Java 21 for Tongues Java backend
brew "php@8.3"     # PHP 8.3 for Tongues PHP backend
brew "python@3.12" # Python 3.12 for Tongues
brew "ruby@3.3"    # Ruby 3.3 for Tongues Ruby backend
brew "util-linux"

# Formatters (for Tongues codegen)
brew "clang-format"   # C/C++/Objective-C code formatter
brew "php-cs-fixer"   # PHP coding standards fixer
brew "stylua"         # Lua code formatter
brew "swiftformat"    # Swift code formatter

# Development Tools
tap "ldayton/dippy"
tap "ldayton/tongues"
brew "dippy"       # permission system for Claude Code
brew "direnv"      # load/unload environment variables per directory
brew "cloc"        # code statistics
brew "git"         # distributed version control system
brew "gh"          # GitHub's official command line tool
brew "rustup"      # Rust toolchain installer and version manager
brew "hyperfine"   # command-line benchmarking tool
brew "just"        # command runner for project-specific tasks
brew "lazygit"     # simple terminal UI for git commands
brew "node"        # JavaScript runtime built on V8
brew "pnpm"        # fast, disk space efficient package manager
brew "tongues"     # Python source-to-source transpiler
brew "uv"          # extremely fast Python package manager and resolver
brew "vite"        # next generation frontend tooling

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
brew "fd"          # simple, fast alternative to find
brew "ripgrep"     # ultra-fast grep with smart defaults
brew "jq"          # lightweight JSON processor
brew "yamllint"    # linter for YAML files
brew "yq"          # lightweight YAML processor
brew "watch"       # execute a command periodically

# Cloud Tools
tap "openfga/tap"               # OpenFGA/Auth0 FGA command-line interface
brew "openfga/tap/fga"
brew "aws-cdk"                  # AWS Cloud Development Kit for infrastructure as code
brew "awscli"                   # official AWS command-line interface
brew "awscurl"                  # curl wrapper for AWS API calls with sigv4
brew "awslogs"                  # query and stream CloudWatch logs
brew "azure-cli"                # Microsoft Azure command-line interface
brew "helm"                     # Kubernetes package manager
tap "hashicorp/tap"             # HashiCorp official tap
brew "hashicorp/tap/terraform"  # infrastructure as code tool for cloud provisioning

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

# Fonts (casks work on Linux since Homebrew 4.4.17)
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
  brew "auth0"            # Auth0 command-line interface
end
