# Modulattice

**Create modules from descriptions with one click**. An AI module generator that designs and writes C# code into self-contained modules. Built for Unity video game developers who are tired of writing boilerplate code and want to focus on design.

<p align="center">
</p>

## Quickstart

Run pip install fastapi uvicorn[standard] aiofiles ollama websockets to setup all the python dependencies.
use start.bat to launch the app and interface.

## Web Interface

1. Type what you want: *"A player controller for a top-down view"*
2. Creates design docs and the requested module
3. Copy-paste folder once sanatized by you

<p align="center">
</p>

## Installation

```bash
pip install modulattice
```

**Supported LLMs:**

- `llama3` (default, hardcoded currently)
- `deepseek-coder`
- **Bring your own** (ollama, future feature)

## Example Outputs

```
"A player health module that will handle players taking damage and dying"

-> 5 files generated:
├── audit.jsonl (an audit of what the system was thinking)
├── design.txt (a design document for the module)
├── Config.cs (a data class for the module if used)
├── PlayerHealth.cs (the module code file)
└── README.md
```

## Contributing

1. Fork -> Clone -> Branch (`feat/amazing-feature`)
2. Submit PR with **squash merge**
3. Star the repo (helps visibility)
4. Join [Discussions](https://github.com/remelic/modulattice/discussions)

```bash
git clone https://github.com/YOURNAME/modulattice.git
cd modulattice
pip install -r requirements-dev.txt
start.bat
```

## Sponsor the Lattice

Help fuel cosmic code generation!


## Connect

- 🌐 [modulattice.com](https://modulattice.com)
- 🐦 [@remelic](https://x.com/remelic)
- 💬 [Discord] - Coming Soon...
- 📧 [info@modulattice.com](mailto:info@modulattice.com)


## License

MIT © [remelic](https://github.com/remelic)

<div align="center">
*** Smart - Fast - Helpful ***
</div>

**Made with [Modulattice](https://modulattice.com)**
