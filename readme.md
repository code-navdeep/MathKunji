# MathKunji

MathKunji is a symbolic mathematics solver that runs entirely on your own
machine. Type an expression, click an operation, and get an exact answer
typeset in LaTeX — algebra, calculus, matrices, graphs and special functions.

It opens in your browser but it is not a website. Nothing you type leaves your
computer, and the app makes no network requests at all.

## What it does

**Algebra** — simplify, expand, factor, solve, and evaluate with substitutions.
Solve takes either a bare expression set to zero (`x^2 - 4`) or a full equation
(`x^2 - 1 = 2*x`).

**Calculus** — derivatives to any order, indefinite and definite integrals,
limits (including at infinity), and Taylor series. Tick **Show steps** to see
which rule was applied at each stage of a derivative or an indefinite integral.

**Matrices** — determinant, inverse, transpose, eigenvalues, eigenvectors,
rank, reduced row echelon form, and multiplication.

**Graphs** — 2D plots of up to three functions at once, 3D surfaces, and
parametric curves.

**Special functions** — 17 of them: Gamma, Riemann Zeta, factorial, binomial,
error function and its complement, Bessel J/Y/I/K, Hermite, Legendre, Laguerre,
Chebyshev T/U, and associated Legendre and Laguerre.

Alongside those: copy any result's raw LaTeX to the clipboard, send a computed
expression straight to the plotter, show a decimal next to an exact result so
`ζ(3)` also reads as `1.202056903`, and export your session's working as a
Markdown transcript.

## Run it

MathKunji runs in Docker. You need
[Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and
running; nothing else.

**The one-click way.** Double-click the launcher for your platform:

| Platform | File |
|---|---|
| macOS | `start.command` |
| Windows | `start.bat` |

Either one checks that Docker is running, builds the image, starts the
container, waits until the app is actually answering, and opens your browser.
The first run takes a few minutes while the image builds. Every run after that
is quick.

**The command-line way**, from this directory:

```bash
docker compose up -d --build
```

Then open <http://localhost:7860>.

**To stop it**, use Docker Desktop, or:

```bash
docker compose down
```

### Without Docker

You can run it directly if you prefer. Python 3.11 or newer:

```bash
pip install -r requirements.txt
python scripts/strip_external_requests.py
python app.py
```

This also serves it at <http://localhost:7860>.

The middle step is one the Docker build runs for you. It removes the font
preconnects and the iframe-resizer script that Gradio hardcodes into its own
page template. Skip it and the app still works, but it will contact Google and
Cloudflare every time you open it.

## It stays on your machine

This is a local tool and it is built to stay that way:

- **No network requests.** Three separate things reach out by default and all
  three are closed: Gradio's usage analytics are switched off, the two typefaces
  are bundled here rather than pulled from a font CDN, and Gradio's own page
  template — which hardcodes two preconnects to Google's font hosts and an
  iframe-resizer script from cdnjs — has them stripped out when the image is
  built. The page it serves contains no external `src` or `href` at all.
- **Reachable only from this computer.** The Docker port is published to
  `127.0.0.1`, not to every network interface, so the app is not visible to
  anyone else on your network.
- **No public tunnel.** There is no share or tunnel option anywhere in the app.
- **No account, no database, no telemetry.** Nothing is stored between runs.
  Closing the tab clears everything.

The container is also locked down beyond that: it runs as an unprivileged user,
drops all Linux capabilities, cannot gain new privileges, and has memory, CPU
and process ceilings so that no single pathological input can affect the host.

## Writing expressions

| You type | Meaning |
|---|---|
| `x^2` or `x**2` | x squared |
| `3x` or `3*x` | three times x |
| `sin(x)`, `cos(x)`, `exp(x)`, `log(x)`, `sqrt(x)` | the usual functions |
| `pi`, `e` | π and Euler's number |
| `oo`, `inf`, `-oo` | infinity, for limits |
| `[[1, 2], [3, 4]]` | a matrix — `Matrix([[…]])` also works |
| `x=2, y=3` | substitutions, in Evaluate |

Because `e` means Euler's number, **it cannot be used as a variable name** —
`e^x` is `exp(x)`. Use another letter.

Every tab has worked examples; click one to fill the fields in.

## How input is handled

MathKunji evaluates mathematical expressions you type, so the parser is
written defensively. Input is restricted to a hand-curated allowlist of around
sixty mathematical names and checked against a syntax gate before anything is
evaluated — attribute access and subscripting are rejected outright, since
maths never needs them.

Every calculation also runs in a separate worker process under a time limit.
If something pathological would run forever, the worker is genuinely killed
rather than abandoned, so one bad expression can neither hang the app nor keep
burning CPU. The limit is deliberately generous (about a minute) so that slow
machines do not fail legitimate work.

## Tests

```bash
pip install -r requirements.txt pytest
pytest
```

The suite covers every module in `core/` and `utils/`, and includes a dedicated
security regression file asserting that sandbox-escape and builtin-call
payloads are rejected by the parser, plus a regression for the worker-pool
timeout behaviour.

## Built with

Python · SymPy · Gradio · matplotlib · NumPy · Docker

Two dependency files, with different jobs:

- **`requirements.txt`** — every dependency, direct and transitive, pinned to an
  exact version. This is the readable list, and the one to edit when upgrading.
- **`requirements.lock`** — generated from it with a SHA-256 for every
  distribution. The Docker build installs from this with `--require-hashes`, so
  pip verifies the bytes of each download and aborts on any mismatch.

A version pin says *gradio 4.44.1* and trusts the index to serve the same
artifact under that name. The hash says *these exact bytes*. Together they mean
an image built in a year contains what was actually tested today.

## Licence

MIT — see [LICENSE](LICENSE).

The bundled Atkinson Hyperlegible and IBM Plex Mono typefaces are licensed
separately under the SIL Open Font License 1.1 — see
[THIRD_PARTY_LICENSES](THIRD_PARTY_LICENSES).

Copyright (c) 2026 Nav Virdi — Liberated.Info
