"""
MathKunji - Mathematical Solver (Gradio Edition)
A clean, desktop-focused mathematical computation tool.
"""

import base64
import functools
import os

import gradio as gr
from utils.parser import parse_expression
from utils.latex_formatter import extract_latex
from utils.timeout import run_with_timeout, ComputationTimeoutError
from core.algebra import (
    simplify_expression,
    expand_expression,
    factor_expression,
    solve_equation,
    evaluate_expression,
    algebra_result_value,
)
from core.calculus import (
    calculate_derivative,
    calculate_integral,
    calculate_limit,
    taylor_series,
    calculus_result_value,
)
from core.steps import derivative_steps, integral_steps_markdown
from core.matrices import (
    matrix_determinant,
    matrix_inverse,
    matrix_transpose,
    matrix_eigenvalues,
    matrix_eigenvectors,
    matrix_rank,
    matrix_rref,
    matrix_multiply,
)
from core.graphing import plot_2d, plot_3d, plot_parametric
from core.special_functions import (
    evaluate_gamma,
    evaluate_zeta,
    evaluate_factorial,
    evaluate_binomial,
    evaluate_hermite,
    evaluate_legendre,
    evaluate_laguerre,
    evaluate_erf,
    evaluate_erfc,
    evaluate_besselj,
    evaluate_bessely,
    evaluate_besseli,
    evaluate_besselk,
    evaluate_chebyshevt,
    evaluate_chebyshevu,
    evaluate_assoc_legendre,
    evaluate_assoc_laguerre,
)


# =============================================================================
# Theme
# =============================================================================
mathkunji_theme = gr.themes.Base(
    primary_hue=gr.themes.Color(
        c50="#e8f0ec",  c100="#c5d8cd", c200="#9ec2af", c300="#74a98e",
        c400="#549175", c500="#1a4d3a", c600="#15402f", c700="#103224",
        c800="#0a2419", c900="#05140e", c950="#020a07",
    ),
    neutral_hue=gr.themes.Color(
        c50="#fafafa",  c100="#f0f0f0", c200="#e0e0e0", c300="#c0c0c0",
        c400="#a0a0a0", c500="#808080", c600="#666666", c700="#4a4a4a",
        c800="#2a2a2a", c900="#1a1a1a", c950="#0d0d0d",
    ),
    # Plain font names, never gr.themes.GoogleFont. Base defaults font to
    # GoogleFont("Source Sans Pro") and font_mono to GoogleFont("IBM Plex
    # Mono"), and a GoogleFont emits a fonts.googleapis.com stylesheet URL into
    # the page config which the browser then fetches -- so the app would call
    # out to Google on every load however the stylesheet is written. A plain
    # string becomes a Font whose stylesheet() is None and nothing is emitted.
    # These are the two typefaces bundled in assets/fonts, so the theme renders
    # in the same faces the stylesheet does.
    font=["Atkinson Hyperlegible", "sans-serif"],
    font_mono=["IBM Plex Mono", "monospace"],
).set(
    body_background_fill="#fafafa",
    body_text_color="#1a1a1a",
    background_fill_primary="#fafafa",
    background_fill_secondary="#fafafa",
    border_color_primary="#e0e0e0",
    block_background_fill="transparent",
    block_border_color="transparent",
    block_label_text_color="#666666",
    block_title_text_color="#1a1a1a",
    input_background_fill="#ffffff",
    input_border_color="#e0e0e0",
    input_border_color_focus="#1a4d3a",
    button_primary_background_fill="#1a4d3a",
    button_primary_background_fill_hover="#103224",
    button_primary_text_color="#ffffff",
    button_primary_border_color="#1a4d3a",
    button_secondary_background_fill="#ffffff",
    button_secondary_text_color="#1a1a1a",
    button_secondary_border_color="#e0e0e0",
    body_text_color_dark="#1a1a1a",
    block_label_text_color_dark="#666666",
    block_title_text_color_dark="#1a1a1a",
)


# =============================================================================
# Bundled typefaces
# =============================================================================
# Both typefaces ship inside the repository and are inlined into the stylesheet
# as base64 data: URIs. MathKunji makes no network request for fonts.
#
# The data: URI is not an arbitrary choice and a served file will not do:
# Gradio's static file route changes shape between versions, so a relative
# url() in this stylesheet is not dependable. A self-contained URI needs no
# server support at all and resolves identically under Docker and under a bare
# `python app.py`.
#
# A missing file here is a packaging error, so open() is left to raise at
# import time rather than silently falling back to a system font.

_FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'fonts')

_BUNDLED_FONTS = (
    ('Atkinson Hyperlegible', 400, 'atkinson-hyperlegible-400.woff2'),
    ('Atkinson Hyperlegible', 700, 'atkinson-hyperlegible-700.woff2'),
    ('IBM Plex Mono', 400, 'ibm-plex-mono-400.woff2'),
    ('IBM Plex Mono', 500, 'ibm-plex-mono-500.woff2'),
)


def _font_face_css():
    """Build @font-face rules with each .woff2 embedded as a data: URI."""
    rules = []
    for family, weight, filename in _BUNDLED_FONTS:
        with open(os.path.join(_FONT_DIR, filename), 'rb') as fh:
            payload = base64.b64encode(fh.read()).decode('ascii')
        rules.append(
            "@font-face {\n"
            f"  font-family: '{family}';\n"
            "  font-style: normal;\n"
            f"  font-weight: {weight};\n"
            "  font-display: swap;\n"
            f"  src: url(data:font/woff2;base64,{payload}) format('woff2');\n"
            "}\n"
        )
    return "\n".join(rules)


# =============================================================================
# Stylesheet
# =============================================================================
# NOTE: this is a plain string, never an f-string -- it contains over a hundred
# literal CSS braces. The font block is concatenated on instead.
custom_css = _font_face_css() + """
:root {
  --bg:          #fafafa;
  --text:        #1a1a1a;
  --accent:      #1a4d3a;
  --accent-deep: #103224;
  --border:      #e0e0e0;
  --muted:       #666666;
  --font-ui:     'Atkinson Hyperlegible', sans-serif;
  --font-mono:   'IBM Plex Mono', monospace;
}

/* === Full-width container, no max-width centering === */
/* Explicit color (not just background) so this stays legible even when the
   OS/browser is in dark mode -- Gradio's own base CSS sets a light-gray
   body text color under prefers-color-scheme: dark that otherwise silently
   overrides everything here that doesn't set its own color. */
html, body { margin: 0 !important; padding: 0 !important; height: 100% !important; background: var(--bg) !important; color: var(--text) !important; color-scheme: light !important; }
.gradio-container, .gradio-container > .main, .gradio-container .contain {
  max-width: 100% !important;
  width: 100% !important;
  margin: 0 !important;
  padding: 0 !important;
  background: var(--bg) !important;
  color: var(--text) !important;
  font-family: var(--font-ui) !important;
}

/* === App root row: sidebar + main === */
.app-root {
  display: flex !important;
  height: 100vh !important;
  width: 100% !important;
  gap: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
  /* Gradio's own default for a Row is flex-wrap: wrap. The sidebar is a fixed
     flex: 0 0 240px and .main is flex: 1 1 auto, so as soon as .main's
     min-content width exceeds the space left over, .main wraps onto a second
     flex line -- and because both children are height: 100vh, that line
     starts one entire viewport BELOW the fold. The result is a blank screen:
     the panes render correctly, just off-screen (measured: .main at x=0,
     y=686 in a 686px-tall viewport, with the 3D pane at y=714).

     Whether it wrapped depended on which pane was active, because each pane
     has a different min-content width -- 2D has two number inputs, while 3D
     has four numbers plus two text boxes and Parametric has two of each. That
     is why 2D appeared to work while 3D and Parametric appeared broken.

     Same fix, and same reason, as the flex-wrap: nowrap already on .sidebar
     and .main below; this row was the one that got missed. */
  flex-wrap: nowrap !important;
}

/* === Sidebar === */
.sidebar {
  width: 240px !important;
  min-width: 240px !important;
  max-width: 240px !important;
  flex: 0 0 240px !important;
  background: var(--bg) !important;
  border-right: 1px solid var(--border) !important;
  padding: 0 !important;
  height: 100vh !important;
  overflow-y: auto !important;
  display: flex !important;
  flex-direction: column !important;
  /* Gradio's own default for this column is flex-wrap: wrap. Combined with
     flex-direction: column and a fixed height, opening any accordion whose
     content pushes past 100vh gets wrapped into an invisible second column
     off to the right instead of scrolling -- that's what made whole
     accordions (Special Functions, Matrices, ...) appear to vanish. */
  flex-wrap: nowrap !important;
}
.app-name {
  font-family: var(--font-ui);
  font-size: 18px;
  font-weight: 700;
  color: var(--text);
  padding: 20px 20px 16px;
  border-bottom: 1px solid var(--border);
  letter-spacing: -0.01em;
}

/* Accordion category headers */
.sidebar .cat-accordion {
  border: none !important;
  background: transparent !important;
  border-radius: 0 !important;
  border-bottom: 1px solid var(--border) !important;
  margin: 0 !important;
  padding: 0 !important;
}
.sidebar .cat-accordion > .label-wrap,
.sidebar .cat-accordion > button:first-child {
  padding: 12px 20px !important;
  font-family: var(--font-ui) !important;
  font-size: 13px !important;
  font-weight: 700 !important;
  color: var(--text) !important;
  background: transparent !important;
  border: none !important;
  border-radius: 0 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.06em !important;
}
.sidebar .cat-accordion > .label-wrap:hover { background: rgba(0,0,0,0.025) !important; }

/* Operation list items inside the accordion */
.sidebar .cat-accordion button {
  background: transparent !important;
  border: none !important;
  border-left: 2px solid transparent !important;
  border-radius: 0 !important;
  font-family: var(--font-ui) !important;
  font-size: 13px !important;
  font-weight: 400 !important;
  color: var(--text) !important;
  text-align: left !important;
  padding: 6px 20px 6px 24px !important;
  width: 100% !important;
  cursor: pointer;
  transition: background 80ms ease, border-color 80ms ease, font-weight 80ms ease;
  min-height: auto !important;
  display: block !important;
  text-transform: none !important;
  letter-spacing: 0 !important;
  box-shadow: none !important;
}
.sidebar .cat-accordion button:hover {
  background: rgba(26, 77, 58, 0.06) !important;
  color: var(--text) !important;
  border-left-color: rgba(26, 77, 58, 0.4) !important;
}
.sidebar .cat-accordion button.active {
  border-left-color: var(--accent) !important;
  font-weight: 700 !important;
  background: rgba(26, 77, 58, 0.04) !important;
}

/* Syntax reference at bottom of sidebar */
.syntax-ref {
  margin-top: auto;
  padding: 14px 20px 18px;
  border-top: 1px solid var(--border);
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--muted);
  line-height: 1.7;
  word-break: break-word;
}

/* === Main area === */
.main {
  flex: 1 1 auto !important;
  padding: 28px 36px !important;
  height: 100vh !important;
  overflow-y: auto !important;
  display: flex !important;
  flex-direction: column !important;
  min-width: 0 !important;
  /* Same fix as .sidebar: prevents the history strip from wrapping into an
     off-screen second column when tab content pushes past 100vh. */
  flex-wrap: nowrap !important;
}

/* Hide Gradio's tab nav — sidebar is the navigation.
   IMPORTANT: must NOT use display:none. Gradio's own Tabs.svelte JS
   refuses to programmatically .select() a tab whose nav button is
   display:none ("Attempted to select a non-interactive or hidden tab"),
   which silently breaks every sidebar button's tab-switch -- clicking a
   button in any non-active category would compute the result but never
   show it, since the pane never became visible. Use the standard
   visually-hidden-but-still-interactive technique instead so Gradio's JS
   still considers the tab selectable. */
.hidden-tabnav > div[role="tablist"],
.hidden-tabnav > .tab-nav {
  position: absolute !important;
  width: 1px !important;
  height: 1px !important;
  padding: 0 !important;
  margin: -1px !important;
  overflow: hidden !important;
  clip: rect(0, 0, 0, 0) !important;
  white-space: nowrap !important;
  border: 0 !important;
}
.hidden-tabnav .tabitem {
  padding: 0 !important;
}

/* Input fields */
input[type="text"], input[type="number"], textarea {
  background: #ffffff !important;
  border: 1px solid var(--border) !important;
  border-radius: 4px !important;
  font-family: var(--font-mono) !important;
  font-size: 14px !important;
  color: var(--text) !important;
  padding: 8px 12px !important;
  box-shadow: none !important;
  outline: none !important;
  transition: border-color 100ms ease;
}
input[type="text"]:focus, input[type="number"]:focus, textarea:focus {
  outline: none !important;
  border-color: var(--accent) !important;
  box-shadow: none !important;
}
input::placeholder, textarea::placeholder {
  color: var(--muted) !important;
  font-style: italic;
  opacity: 0.6;
}

/* Labels */
label > span:first-child, .block > label, .label-wrap {
  font-family: var(--font-ui) !important;
  font-size: 12px !important;
  font-weight: 400 !important;
  color: var(--muted) !important;
  margin-bottom: 4px !important;
  text-transform: none !important;
  letter-spacing: 0 !important;
}

/* Dropdowns (no gr.Dropdown is currently used, but kept for future use) */
select {
  background: #ffffff !important;
  border: 1px solid var(--border) !important;
  border-radius: 4px !important;
  font-family: var(--font-mono) !important;
  color: var(--text) !important;
  box-shadow: none !important;
}

/* Checkbox */
input[type="checkbox"] { accent-color: var(--accent); }

/* === Result markdown ===
   .markdown/.gr-markdown are dead in current Gradio (confirmed zero DOM
   matches) -- .prose and [data-testid="markdown"] are the real ones. */
.prose, div[data-testid="markdown"] {
  background: transparent !important;
  border: none !important;
  padding: 12px 0 !important;
  font-family: var(--font-ui) !important;
  color: var(--text) !important;
  font-size: 14px !important;
  margin: 0 !important;
  border-radius: 0 !important;
}
div[data-testid="markdown"]:empty { display: none !important; }
.prose h3 {
  font-family: var(--font-ui) !important;
  font-size: 12px !important;
  font-weight: 700 !important;
  color: var(--muted) !important;
  margin: 0 0 12px !important;
  text-transform: uppercase !important;
  letter-spacing: 0.06em !important;
  border: none !important;
  padding: 0 !important;
}
.prose h4 {
  font-family: var(--font-ui) !important;
  font-size: 13px !important;
  font-weight: 700 !important;
  color: var(--text) !important;
  margin: 14px 0 6px !important;
}
.prose strong { font-weight: 700 !important; color: var(--text) !important; }
.prose p { margin: 8px 0 !important; line-height: 1.65; color: var(--text) !important; }
.prose .katex-display {
  margin: 16px 0 !important;
  font-size: 1.5em !important;
}

/* Inputs and result vertical split (~30 / ~70 visual) */
.input-zone {
  flex: 0 0 auto;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 12px;
}
.result-zone {
  flex: 1 1 auto;
  min-height: 200px;
}

/* === Buttons in main area === */
.main button {
  background: #ffffff !important;
  border: 1px solid var(--border) !important;
  border-radius: 4px !important;
  font-family: var(--font-ui) !important;
  font-size: 12px !important;
  font-weight: 700 !important;
  color: var(--text) !important;
  padding: 7px 14px !important;
  cursor: pointer;
  transition: all 100ms ease-out;
  box-shadow: none !important;
}
.main button:hover {
  background: var(--bg) !important;
  border-color: var(--text) !important;
}
.main button.primary, .main button[variant="primary"] {
  background: var(--accent) !important;
  color: #ffffff !important;
  border: 1px solid var(--accent) !important;
}
.main button.primary:hover {
  background: var(--accent-deep) !important;
  border-color: var(--accent-deep) !important;
}

/* The in-pane "Plot" button. The only trigger used to be the sidebar button,
   which sits nowhere near the fields being edited -- and Enter worked in just
   one field per pane -- so there was no obvious way to say "draw it now". */
.plot-btn-row { margin: 12px 0 4px; }
.plot-btn-row button {
  width: auto !important;
  flex-grow: 0 !important;
  padding: 8px 22px !important;
}

/* Selected-tab styling. `.main button` above styles every button in the main
   area identically and with !important, which also swallowed Gradio's own
   selected-tab styling. Kept for any visible tab nav: the top-level nav is
   currently hidden by .hidden-tabnav, but without this rule an unhidden nav
   would show the highlight on the wrong tab. Gradio marks the active tab with
   both class="selected" and aria-selected="true"; matching either keeps this
   working if one of them changes. */
.main button.selected,
.main button[aria-selected="true"] {
  background: var(--bg) !important;
  color: var(--accent) !important;
  border-color: var(--accent) !important;
  font-weight: 700 !important;
}
.main button.selected:hover,
.main button[aria-selected="true"]:hover {
  background: rgba(26, 77, 58, 0.06) !important;
  border-color: var(--accent) !important;
}

/* === History strip === */
.history-strip {
  margin-top: 18px !important;
  padding-top: 12px !important;
  border-top: 1px solid var(--border) !important;
  background: transparent !important;
}
.history-strip h4 {
  font-family: var(--font-ui) !important;
  font-size: 11px !important;
  font-weight: 700 !important;
  color: var(--muted) !important;
  margin: 0 0 6px !important;
  text-transform: uppercase !important;
  letter-spacing: 0.07em !important;
}
.history-strip ul { padding-left: 0 !important; margin: 0 !important; list-style: none !important; }
.history-strip li {
  margin: 3px 0 !important;
  line-height: 1.5;
  font-family: var(--font-mono) !important;
  font-size: 11px !important;
  color: var(--muted) !important;
  list-style: none !important;
}

/* === Plot container ===
   Gradio's own plot-component class/testid have no stable name across
   versions (both .gr-plot and [data-testid="plot"] are dead in current
   Gradio -- confirmed zero DOM matches), so g2d_plot/g3d_plot/gpa_plot
   are each given our own elem_classes="plot-output" to target instead. */
.plot-output {
  background: transparent !important;
  border: none !important;
  padding: 0 !important;
}
/* Scroll lock, keyed off a class the toggle adds rather than off a
   `body.fullscreen-active ...` descendant selector -- see the note below. */
.gradio-container.fs-lock { overflow: hidden !important; }

/* Only the plot the user actually expanded is promoted -- the toggle tags it
   with .fs-target first. The old rule matched every .plot-output at once.

   Note there is NO `body.fullscreen-active` prefix here, and there must not
   be one. Gradio emits every custom rule twice: the original, plus a copy
   prefixed with "gradio-app .gradio-container... .contain ". A selector
   containing `body` gets a prefixed copy that can never match -- body is not
   a descendant of .contain -- so only its low-specificity original survives,
   and that loses to the *prefixed* copy of any competing simpler selector.
   Concretely: `.plot-output` above becomes a (0,4,1) rule, so a
   `body.fullscreen-active .plot-output.fs-target` rule at (0,3,1) silently
   lost `background` and `padding` to it and the expanded plot rendered
   transparent with no inset. Keying off .fs-target alone lets this rule be
   prefixed too, at (0,5,1), so it wins outright. */
.plot-output.fs-target {
  position: fixed !important;
  inset: 0 !important;
  width: 100vw !important;
  height: 100vh !important;
  z-index: 9999 !important;
  background: var(--bg) !important;
  padding: 32px !important;
  margin: 0 !important;
}

/* Way out of fullscreen.
   The "⛶ Fullscreen plot" toggle is a sibling of the plot, so once the plot
   became a full-viewport element at z-index 9999 the toggle sat underneath it
   and could not be clicked -- and the Esc handler only cleared text inputs.
   There was no way back out short of reloading the page. This control is
   fixed above the overlay and only exists while fullscreen is active. */
/* Visibility keys off .fs-visible on the button itself, NOT off a
   body.fullscreen-active ancestor selector. Gradio rewrites custom CSS by
   prefixing selectors with "gradio-app .gradio-container... .contain ", but it
   leaves selectors that start with `body` alone -- so ".fs-exit{display:none}"
   became a (0,4,1) rule while "body.fullscreen-active .fs-exit{display:block}"
   stayed at (0,2,1), and the hide rule silently outranked the show rule. The
   button stayed invisible and fullscreen had no visible way out again.
   Keying both off classes means Gradio prefixes them identically, so the
   two-class rule genuinely wins. */
.fs-exit { display: none !important; }
.fs-exit.fs-visible {
  display: block !important;
  position: fixed !important;
  top: 18px !important;
  right: 18px !important;
  width: auto !important;
  z-index: 10000 !important;
  background: var(--accent) !important;
  color: #ffffff !important;
  border: 1px solid var(--accent) !important;
  border-radius: 4px !important;
  padding: 8px 14px !important;
  font-family: var(--font-ui) !important;
  font-size: 12px !important;
  font-weight: 700 !important;
  cursor: pointer;
  box-shadow: 0 2px 10px rgba(0,0,0,0.18) !important;
}
.fs-exit.fs-visible:hover {
  background: var(--accent-deep) !important;
  border-color: var(--accent-deep) !important;
}

/* === Result actions (Copy LaTeX / Graph result / Export) === */
.result-actions { margin: 4px 0 10px; gap: 8px !important; }
.result-actions button {
  background: transparent !important;
  border: 1px solid var(--border) !important;
  color: var(--muted) !important;
  font-size: 11px !important;
  padding: 5px 12px !important;
  width: auto !important;
  flex-grow: 0 !important;
}
.result-actions button:hover {
  border-color: var(--accent) !important;
  color: var(--accent) !important;
}

/* Off-screen holding pens for the raw LaTeX and the plain result expression.
   Hidden with CSS rather than gr.Textbox(visible=False) because the <textarea>
   must stay in the DOM -- the Copy button reads its value from JS, and the
   Graph button feeds it back into the plotter. */
.value-buffer {
  position: absolute !important;
  width: 1px !important;
  height: 1px !important;
  overflow: hidden !important;
  clip: rect(0, 0, 0, 0) !important;
  margin: -1px !important;
}

/* === Examples ===
   Gradio 4.x's Examples table has no stable class/testid of its own
   (it's an internal Svelte-scoped-hash class that changes across Gradio
   versions) -- so this targets it structurally via our own .input-zone
   wrapper instead of guessing at Gradio's internal class names. */
.input-zone table {
  background: transparent !important;
  border: none !important;
  border-collapse: collapse !important;
  margin-top: 14px !important;
  width: 100% !important;
}
/* Gradio applies its own dark zebra-stripe background directly on <tr>
   (alternating ~rgb(26,26,26)/rgb(13,13,13)), independent of <td>'s own
   background. Since <td> text is also dark, one of the two alternating
   rows ends up with text and background the same color -- invisible. */
.input-zone table tr {
  background: transparent !important;
}
.input-zone table td {
  font-family: var(--font-mono) !important;
  font-size: 12px !important;
  background: transparent !important;
  border: none !important;
  border-bottom: 1px solid var(--border) !important;
  padding: 6px 10px !important;
  color: var(--text) !important;
}
.input-zone table tr:hover td {
  background: rgba(26, 77, 58, 0.04) !important;
  cursor: pointer;
}
.input-zone table th { display: none !important; }

/* Strip Gradio chrome */
footer, .show-api, .built-with { display: none !important; }
.form, .block {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  padding: 0 !important;
}

/* Fullscreen toggle button — a discreet pill above the plot */
.fs-btn-row { margin: 8px 0; }
"""


# =============================================================================
# Client-side behaviour
# =============================================================================
# Passed to gr.Blocks(js=...), which is Gradio's supported hook for custom
# client-side code: it takes a single function and runs it once the app has
# loaded.
#
# Do NOT move this back into a `<script>` inside a gr.HTML() component: it
# never executed there, not once. Gradio's HTML component renders by assigning
# innerHTML, and per the HTML spec a <script> inserted that way is inert.
# Confirmed in the browser -- the tag was in the DOM, every window.mathkunji*
# helper was undefined, and `.cat-accordion button.active` matched nothing, so
# the sidebar active-item highlighting and Esc-to-clear-input had never
# actually worked.
#
# gr.Blocks(head=...) also defines the helpers correctly and is a viable
# alternative. js= is kept because it is Gradio's documented hook for exactly
# this, and because it runs after the app has loaded, so the DOM already exists
# here -- no DOMContentLoaded dance needed.
custom_js = """
() => {
    // Promote only the plot the user is actually looking at. The CSS rule
    // keys off .fs-target for exactly this reason -- the earlier rule matched
    // every .plot-output at once, including the ones in hidden tabs.
    // Show the exit control for whichever pane owns the expanded plot. Its
    // visibility is driven by the .fs-visible class rather than by a
    // body.fullscreen-active ancestor selector -- see the CSS note on .fs-exit
    // for why an ancestor selector loses to Gradio's rewritten rules.
    function showExitControl(pane) {
        document.querySelectorAll('.fs-exit.fs-visible')
            .forEach(el => el.classList.remove('fs-visible'));
        const exit = pane ? pane.querySelector('.fs-exit') : null;
        if (exit) exit.classList.add('fs-visible');
    }

    window.mathkunjiEnterFullscreen = function () {
        const target = Array.from(document.querySelectorAll('.plot-output'))
            .find(el => el.offsetParent !== null);
        if (!target) return;
        document.querySelectorAll('.plot-output.fs-target')
            .forEach(el => el.classList.remove('fs-target'));
        target.classList.add('fs-target');
        // body.fullscreen-active is what the Esc handler and the toggle read
        // to know the current state; it is deliberately NOT what any CSS rule
        // keys off (see the .plot-output.fs-target note in the stylesheet).
        document.body.classList.add('fullscreen-active');
        document.querySelectorAll('.gradio-container')
            .forEach(el => el.classList.add('fs-lock'));
        showExitControl(target.closest('.tabitem') || document);
    };

    window.mathkunjiExitFullscreen = function () {
        document.body.classList.remove('fullscreen-active');
        document.querySelectorAll('.plot-output.fs-target')
            .forEach(el => el.classList.remove('fs-target'));
        document.querySelectorAll('.gradio-container.fs-lock')
            .forEach(el => el.classList.remove('fs-lock'));
        document.querySelectorAll('.fs-exit.fs-visible')
            .forEach(el => el.classList.remove('fs-visible'));
    };

    window.mathkunjiToggleFullscreen = function () {
        if (document.body.classList.contains('fullscreen-active')) {
            window.mathkunjiExitFullscreen();
        } else {
            window.mathkunjiEnterFullscreen();
        }
    };

    function attachSidebarTracking() {
        const sidebar = document.querySelector('.sidebar');
        if (!sidebar) { setTimeout(attachSidebarTracking, 300); return; }
        sidebar.addEventListener('click', function (e) {
            const btn = e.target.closest('.cat-accordion button');
            if (!btn) return;
            if (btn.matches('.label-wrap, .label-wrap *')) return;
            sidebar.querySelectorAll('.cat-accordion button.active')
                .forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        });
    }

    // Copy the raw LaTeX of the current result to the clipboard. The value
    // lives in an off-screen textarea (.value-buffer) that the result handler
    // fills in, because the rendered markdown only contains typeset maths.
    window.mathkunjiCopyLatex = function (bufferId) {
        const field = document.querySelector('#' + bufferId + ' textarea, #' + bufferId + ' input');
        if (!field || !field.value) return;
        navigator.clipboard.writeText(field.value).then(function () {
            const button = document.activeElement;
            if (!button || button.tagName !== 'BUTTON') return;
            const original = button.textContent;
            button.textContent = '✓ Copied';
            setTimeout(function () { button.textContent = original; }, 1200);
        }).catch(function () { /* clipboard blocked; nothing useful to do */ });
    };

    // Save the session transcript. The markdown is put into an off-screen
    // textarea by the server, and turned into a download here.
    window.mathkunjiDownloadSession = function () {
        const field = document.querySelector('#export-buffer textarea, #export-buffer input');
        if (!field || !field.value) return;
        const stamp = new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-');
        const blob = new Blob([field.value], { type: 'text/markdown;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = 'mathkunji-session-' + stamp + '.md';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
    };

    attachSidebarTracking();

    document.addEventListener('keydown', function (e) {
        if (e.key !== 'Escape') return;
        // Leaving fullscreen takes priority: it is the state a user is most
        // likely to be stuck in, and Esc is the conventional way out. Only
        // fall through to clearing a focused field when there is no
        // fullscreen plot to dismiss.
        if (document.body.classList.contains('fullscreen-active')) {
            window.mathkunjiExitFullscreen();
            e.preventDefault();
            return;
        }
        const a = document.activeElement;
        if (a && (a.tagName === 'INPUT' || a.tagName === 'TEXTAREA')) {
            a.value = '';
            a.dispatchEvent(new Event('input', { bubbles: true }));
        }
    });
}
"""


# =============================================================================
# History helpers
# =============================================================================
HISTORY_LIMIT = 5


def push_history(op_name, primary, history, result=None):
    """
    Record an operation.

    Entries are dicts rather than plain strings because the strip is no longer
    the only consumer: "Export session" turns them into a transcript, and a
    transcript of "derivative: x^3" with no answers would not be worth saving.
    The label is kept pre-truncated so rendering the strip stays trivial.
    """
    history = list(history or [])
    label = (primary or "").strip()
    if len(label) > 40:
        label = label[:37] + "..."

    entry = {
        "operation": op_name,
        "input": (primary or "").strip(),
        "label": f"{op_name}: {label}" if label else op_name,
        "result": result if isinstance(result, str) else "",
    }
    return ([entry] + history)[:HISTORY_LIMIT]


def render_history(history):
    if not history:
        return ""
    items = "\n".join(f"- {entry['label']}" for entry in history)
    return f"#### Recent\n{items}"


def build_transcript(history):
    """Render the recorded operations as a standalone Markdown document."""
    if not history:
        return "# MathKunji session\n\nNo operations recorded yet.\n"

    lines = ["# MathKunji session", ""]
    # history is newest-first; a transcript reads better oldest-first.
    for index, entry in enumerate(reversed(history), start=1):
        lines.append(f"## {index}. {entry['operation']}")
        lines.append("")
        if entry["input"]:
            lines.append(f"**Input:** `{entry['input']}`")
            lines.append("")
        if entry["result"]:
            lines.append(entry["result"].rstrip())
            lines.append("")
        lines.append("---")
        lines.append("")
    return "\n".join(lines)


# =============================================================================
# App
# =============================================================================
def create_app():
    with gr.Blocks(title="MathKunji", theme=mathkunji_theme, css=custom_css, js=custom_js) as app:
        history = gr.State([])

        with gr.Row(elem_classes="app-root"):
            # =================== SIDEBAR ===================
            with gr.Column(elem_classes="sidebar", scale=0, min_width=240):
                gr.HTML('<div class="app-name">MathKunji</div>')

                with gr.Accordion("Algebra", open=True, elem_classes="cat-accordion"):
                    sb_simplify = gr.Button("Simplify")
                    sb_expand   = gr.Button("Expand")
                    sb_factor   = gr.Button("Factor")
                    sb_solve    = gr.Button("Solve")
                    sb_evaluate = gr.Button("Evaluate")

                with gr.Accordion("Calculus", open=False, elem_classes="cat-accordion"):
                    sb_derivative = gr.Button("Derivative")
                    sb_integral   = gr.Button("Integral")
                    sb_limit      = gr.Button("Limit")
                    sb_taylor     = gr.Button("Taylor Series")

                with gr.Accordion("Matrices", open=False, elem_classes="cat-accordion"):
                    sb_det       = gr.Button("Determinant")
                    sb_inv       = gr.Button("Inverse")
                    sb_transpose = gr.Button("Transpose")
                    sb_eigenval  = gr.Button("Eigenvalues")
                    sb_eigenvec  = gr.Button("Eigenvectors")
                    sb_rank      = gr.Button("Rank")
                    sb_rref      = gr.Button("RREF")
                    sb_multiply  = gr.Button("Multiply A×B")

                with gr.Accordion("Graphs", open=False, elem_classes="cat-accordion"):
                    sb_plot2d    = gr.Button("2D Plot")
                    sb_plot3d    = gr.Button("3D Plot")
                    sb_plotparam = gr.Button("Parametric")

                with gr.Accordion("Special Functions", open=False, elem_classes="cat-accordion"):
                    sb_gamma       = gr.Button("Gamma")
                    sb_zeta        = gr.Button("Zeta")
                    sb_factorial   = gr.Button("Factorial")
                    sb_binomial    = gr.Button("Binomial")
                    sb_erf         = gr.Button("Error Function")
                    sb_erfc        = gr.Button("Complementary erf")
                    sb_besselj     = gr.Button("Bessel J")
                    sb_bessely     = gr.Button("Bessel Y")
                    sb_besseli     = gr.Button("Bessel I")
                    sb_besselk     = gr.Button("Bessel K")
                    sb_hermite     = gr.Button("Hermite")
                    sb_legendre    = gr.Button("Legendre")
                    sb_laguerre    = gr.Button("Laguerre")
                    sb_chebyshevt  = gr.Button("Chebyshev T")
                    sb_chebyshevu  = gr.Button("Chebyshev U")
                    sb_asslegendre = gr.Button("Assoc Legendre")
                    sb_asslaguerre = gr.Button("Assoc Laguerre")

                gr.HTML(
                    '<div class="syntax-ref">'
                    '<b>^</b> &nbsp; <b>**</b> &nbsp;·&nbsp; '
                    'sin&nbsp;cos&nbsp;exp&nbsp;log&nbsp;sqrt &nbsp;·&nbsp; '
                    'pi&nbsp;e&nbsp;oo &nbsp;·&nbsp; '
                    '[[1,2],[3,4]]'
                    '</div>'
                )

            # =================== MAIN ===================
            with gr.Column(elem_classes="main"):
                with gr.Tabs(elem_classes="hidden-tabnav", selected="alg") as main_tabs:

                    # ---------- Algebra ----------
                    with gr.Tab("Algebra", id="alg"):
                        with gr.Column(elem_classes="input-zone"):
                            with gr.Row():
                                alg_expr = gr.Textbox(label="Expression", placeholder="x^2 + 3*x + 2", lines=2, scale=4)
                                alg_var  = gr.Textbox(label="Variable", value="x", scale=1)
                            alg_subs = gr.Textbox(label="Substitutions (for Evaluate)", placeholder="x=2, y=3")
                            gr.Examples(
                                examples=[
                                    ["x^2 + 2*x + 1", "x", ""],
                                    ["(x + 1)*(x - 1)", "x", ""],
                                    ["x^2 - 4", "x", ""],
                                    ["sin(x)^2 + cos(x)^2", "x", ""],
                                ],
                                inputs=[alg_expr, alg_var, alg_subs],
                            )
                        with gr.Column(elem_classes="result-zone"):
                            with gr.Row(elem_classes="result-actions"):
                                alg_copy  = gr.Button("⧉ Copy LaTeX")
                                alg_graph = gr.Button("📈 Graph result")
                            alg_output = gr.Markdown(latex_delimiters=[
                                {"left": "$$", "right": "$$", "display": True},
                                {"left": "$", "right": "$", "display": False},
                            ])
                            alg_latex = gr.Textbox(elem_id="alg-latex", elem_classes="value-buffer", label="latex")
                            alg_value = gr.Textbox(elem_classes="value-buffer", label="value")

                    # ---------- Calculus ----------
                    with gr.Tab("Calculus", id="cal"):
                        with gr.Column(elem_classes="input-zone"):
                            with gr.Row():
                                cal_expr = gr.Textbox(label="Function", placeholder="x^3 + 2*x^2 - 5*x + 1", lines=2, scale=4)
                                cal_var  = gr.Textbox(label="Variable", value="x", scale=1)
                            with gr.Row():
                                cal_order = gr.Number(label="Order (deriv / Taylor)", value=1, precision=0, scale=1)
                                cal_point = gr.Textbox(label="Point (limit / Taylor)", value="0", scale=1)
                                cal_dir   = gr.Dropdown(choices=["+", "-", "+-"], label="Direction (limit)", value="+", scale=1)
                            with gr.Row():
                                cal_definite = gr.Checkbox(label="Definite integral", value=False, scale=1)
                                cal_lower    = gr.Textbox(label="Lower bound", placeholder="0", scale=1)
                                cal_upper    = gr.Textbox(label="Upper bound", placeholder="1", scale=1)
                            with gr.Row():
                                cal_steps   = gr.Checkbox(label="Show steps (derivative / indefinite integral)", value=False)
                                cal_numeric = gr.Checkbox(label="Show numeric value", value=False)
                            gr.Examples(
                                examples=[
                                    ["x^2 + 3*x", "x", 1, "0", "+", False, "", ""],
                                    ["sin(x)", "x", 1, "0", "+", False, "", ""],
                                    ["x^3", "x", 2, "0", "+", False, "", ""],
                                    ["exp(x)", "x", 1, "0", "+", False, "", ""],
                                ],
                                inputs=[cal_expr, cal_var, cal_order, cal_point, cal_dir, cal_definite, cal_lower, cal_upper],
                            )
                        with gr.Column(elem_classes="result-zone"):
                            with gr.Row(elem_classes="result-actions"):
                                cal_copy  = gr.Button("⧉ Copy LaTeX")
                                cal_graph = gr.Button("📈 Graph result")
                            # Inline delimiters: the step-by-step working and
                            # the numeric line are written with single-$ maths.
                            cal_output = gr.Markdown(latex_delimiters=[
                                {"left": "$$", "right": "$$", "display": True},
                                {"left": "$", "right": "$", "display": False},
                            ])
                            cal_latex = gr.Textbox(elem_id="cal-latex", elem_classes="value-buffer", label="latex")
                            cal_value = gr.Textbox(elem_classes="value-buffer", label="value")

                    # ---------- Matrices ----------
                    with gr.Tab("Matrices", id="mat"):
                        with gr.Column(elem_classes="input-zone"):
                            with gr.Row():
                                mat_a = gr.Textbox(label="Matrix A", placeholder="[[1, 2], [3, 4]]", lines=4)
                                mat_b = gr.Textbox(label="Matrix B (for Multiply)", placeholder="[[5, 6], [7, 8]]", lines=4)
                            gr.Examples(
                                examples=[
                                    ["[[1, 2], [3, 4]]", "[[1, 0], [0, 1]]"],
                                    ["[[2, -1], [-1, 2]]", ""],
                                    ["[[1, 2, 3], [4, 5, 6], [7, 8, 9]]", ""],
                                ],
                                inputs=[mat_a, mat_b],
                            )
                        with gr.Column(elem_classes="result-zone"):
                            with gr.Row(elem_classes="result-actions"):
                                mat_copy = gr.Button("⧉ Copy LaTeX")
                            mat_output = gr.Markdown(latex_delimiters=[
                                {"left": "$$", "right": "$$", "display": True},
                                {"left": "$", "right": "$", "display": False},
                            ])
                            mat_latex = gr.Textbox(elem_id="mat-latex", elem_classes="value-buffer", label="latex")

                    # ---------- Graphs ----------
                    # 2D / 3D / Parametric are TOP-LEVEL tabs, not a nested
                    # gr.Tabs inside a "Graphs" tab. They used to be nested,
                    # which made every graph click the only operation in the
                    # app that had to update two Tabs components in a single
                    # response -- and Gradio refuses that, logging
                    # "Attempted to select a non-interactive or hidden tab"
                    # once per Tabs and silently leaving both panes as they
                    # were. The plot was computed and placed correctly; its
                    # pane was just never revealed, which is why switching
                    # tabs by hand made it appear and waiting never did.
                    # Flattened, a graph click updates exactly one Tabs, the
                    # same as every other operation.
                    with gr.Tab("2D Plot", id="g2d"):
                        with gr.Column(elem_classes="input-zone"):
                            g2d_e1 = gr.Textbox(label="Function 1", placeholder="sin(x)")
                            g2d_e2 = gr.Textbox(label="Function 2 (optional)", placeholder="cos(x)")
                            g2d_e3 = gr.Textbox(label="Function 3 (optional)")
                            with gr.Row():
                                g2d_xmin = gr.Number(label="x min", value=-10)
                                g2d_xmax = gr.Number(label="x max", value=10)
                            gr.Examples(
                                examples=[
                                    ["sin(x)", "cos(x)", "", -10, 10],
                                    ["x^2", "x^3", "x^4", -5, 5],
                                    ["exp(-x^2)", "", "", -3, 3],
                                ],
                                inputs=[g2d_e1, g2d_e2, g2d_e3, g2d_xmin, g2d_xmax],
                            )
                            with gr.Row(elem_classes="plot-btn-row"):
                                g2d_go = gr.Button("Plot", variant="primary")
                        with gr.Column(elem_classes="result-zone"):
                            with gr.Row(elem_classes="fs-btn-row"):
                                g2d_fs = gr.Button("⛶ Fullscreen plot")
                            g2d_fs_exit = gr.Button("✕ Exit fullscreen", elem_classes="fs-exit")
                            g2d_plot   = gr.Plot(elem_classes="plot-output")
                            g2d_status = gr.Markdown()

                    with gr.Tab("3D Plot", id="g3d"):
                        with gr.Column(elem_classes="input-zone"):
                            g3d_expr = gr.Textbox(label="Function", placeholder="x^2 + y^2")
                            with gr.Row():
                                g3d_xvar = gr.Textbox(label="x var", value="x")
                                g3d_yvar = gr.Textbox(label="y var", value="y")
                            with gr.Row():
                                g3d_xmin = gr.Number(label="x min", value=-5)
                                g3d_xmax = gr.Number(label="x max", value=5)
                                g3d_ymin = gr.Number(label="y min", value=-5)
                                g3d_ymax = gr.Number(label="y max", value=5)
                            gr.Examples(
                                examples=[
                                    ["x^2 + y^2", -5, 5, -5, 5, "x", "y"],
                                    ["sin(sqrt(x^2 + y^2))", -5, 5, -5, 5, "x", "y"],
                                    ["a*b", -3, 3, -3, 3, "a", "b"],
                                ],
                                inputs=[g3d_expr, g3d_xmin, g3d_xmax, g3d_ymin, g3d_ymax, g3d_xvar, g3d_yvar],
                            )
                            with gr.Row(elem_classes="plot-btn-row"):
                                g3d_go = gr.Button("Plot", variant="primary")
                        with gr.Column(elem_classes="result-zone"):
                            with gr.Row(elem_classes="fs-btn-row"):
                                g3d_fs = gr.Button("⛶ Fullscreen plot")
                            g3d_fs_exit = gr.Button("✕ Exit fullscreen", elem_classes="fs-exit")
                            g3d_plot   = gr.Plot(elem_classes="plot-output")
                            g3d_status = gr.Markdown()

                    with gr.Tab("Parametric", id="gpa"):
                        with gr.Column(elem_classes="input-zone"):
                            with gr.Row():
                                gpa_xe = gr.Textbox(label="x(t)", placeholder="cos(t)")
                                gpa_ye = gr.Textbox(label="y(t)", placeholder="sin(t)")
                            with gr.Row():
                                gpa_tmin = gr.Number(label="t min", value=0)
                                gpa_tmax = gr.Number(label="t max", value=6.28)
                            gr.Examples(
                                examples=[
                                    ["cos(t)", "sin(t)", 0, 6.28],
                                    ["t*cos(t)", "t*sin(t)", 0, 20],
                                    ["sin(2*t)", "sin(3*t)", 0, 6.28],
                                ],
                                inputs=[gpa_xe, gpa_ye, gpa_tmin, gpa_tmax],
                            )
                            with gr.Row(elem_classes="plot-btn-row"):
                                gpa_go = gr.Button("Plot", variant="primary")
                        with gr.Column(elem_classes="result-zone"):
                            with gr.Row(elem_classes="fs-btn-row"):
                                gpa_fs = gr.Button("⛶ Fullscreen plot")
                            gpa_fs_exit = gr.Button("✕ Exit fullscreen", elem_classes="fs-exit")
                            gpa_plot   = gr.Plot(elem_classes="plot-output")
                            gpa_status = gr.Markdown()

                    # ---------- Special Functions ----------
                    with gr.Tab("Special", id="spc"):
                        with gr.Column(elem_classes="input-zone"):
                            with gr.Row():
                                sp_arg1 = gr.Textbox(label="Argument 1 (n / order / value)", placeholder="5")
                                sp_arg2 = gr.Textbox(label="Argument 2 (x / k / m)", placeholder="x")
                                sp_arg3 = gr.Textbox(label="Argument 3 (for associated)", placeholder="x")
                            gr.Examples(
                                examples=[
                                    ["5", "", ""],
                                    ["10", "", ""],
                                    ["10", "3", ""],
                                    ["0", "x", ""],
                                    ["3", "x", ""],
                                    ["2", "1", "x"],
                                ],
                                inputs=[sp_arg1, sp_arg2, sp_arg3],
                            )
                            sp_numeric = gr.Checkbox(label="Show numeric value", value=False)
                        with gr.Column(elem_classes="result-zone"):
                            with gr.Row(elem_classes="result-actions"):
                                sp_copy = gr.Button("⧉ Copy LaTeX")
                            # Inline delimiters: the numeric line uses single-$.
                            sp_output = gr.Markdown(latex_delimiters=[
                                {"left": "$$", "right": "$$", "display": True},
                                {"left": "$", "right": "$", "display": False},
                            ])
                            sp_latex = gr.Textbox(elem_id="spc-latex", elem_classes="value-buffer", label="latex")

                # History strip
                history_display = gr.Markdown(elem_classes="history-strip")
                with gr.Row(elem_classes="result-actions"):
                    export_btn = gr.Button("⭳ Export session")
                # The transcript is handed to the browser through this buffer
                # and saved with a Blob, rather than through gr.DownloadButton
                # or gr.File. Both of those crash this Gradio/gradio_client
                # pairing: their api_info emits a schema whose
                # additionalProperties is a bool, the client's schema converter
                # cannot walk it, and the resulting TypeError makes the main
                # page return HTTP 500 -- the app does not load at all.
                export_buffer = gr.Textbox(elem_id="export-buffer", elem_classes="value-buffer", label="export")

        # =================== WIRING ===================
        # Timeout guard shared by every core/*.py call below. Markdown-output
        # operations get a "❌ ..." string on expiry; plot operations get
        # (None, "❌ ...") so they match their (figure, status) return shape.
        def guarded(func, *args, returns_figure=False):
            try:
                return run_with_timeout(func, *args)
            except ComputationTimeoutError as e:
                msg = f"❌ {e}"
            except Exception as e:
                # Backstop so nothing can surface as a raw Gradio error.
                # core/* functions are written to turn their own failures into
                # "❌ ..." strings, but anything they miss used to escape --
                # a cleared gr.Number sent None straight into a comparison and
                # raised TypeError right through this wrapper. run_with_timeout
                # also raises RuntimeError if a worker process reports an
                # unexpected exception. Every user-visible failure in this app
                # is an "❌" value, and this is the one place every handler
                # passes through, so it is enforced here.
                msg = f"❌ Unexpected error: {type(e).__name__}: {e}"
            return (None, msg) if returns_figure else msg

        # Tab switching is returned by the operation's own handler, not chained
        # after it with .then().
        #
        # The chained form was unreliable. Clicking a graph button logged
        # "Attempted to select a non-interactive or hidden tab" twice and left
        # the pane unchanged; a second click was needed before it landed. Each
        # .then() is a separate server round-trip that re-applies component
        # props, and the Tabs component rebuilds its internal registry of tabs
        # as that happens -- so a selection arriving in its own event can find
        # no tab to match. Folding the selection into the primary handler makes
        # it one atomic application of outputs, and drops two round-trips per
        # click as a side benefit.
        def with_tab(fn, tab_id):
            """
            Non-graph operations: append the raw LaTeX of the result (for the
            Copy button) and the tab selection.

            The LaTeX is recovered from the rendered markdown rather than
            returned separately by core/*, so that every handler's own body
            stays untouched -- see extract_latex() for why.
            """
            @functools.wraps(fn)
            def inner(*args):
                result = fn(*args)
                if not isinstance(result, tuple):
                    result = (result,)
                markdown = result[0] if result else ""
                latex_source = extract_latex(markdown if isinstance(markdown, str) else "")
                return result + (latex_source, gr.update(selected=tab_id))
            return inner

        def with_graph_tab(fn, tab_id):
            """
            Graph operations: select the graph's own top-level tab.

            One tab update, not two. The graph panes used to be a nested
            gr.Tabs inside a "Graphs" tab, which made these the only handlers
            in the app that updated two Tabs components in one response --
            and Gradio refuses that, logging "Attempted to select a
            non-interactive or hidden tab" once per Tabs and leaving both
            panes untouched. See the layout comment on the 2D Plot tab.

            Unlike with_tab() there is no LaTeX buffer here -- a plot has no
            LaTeX result to copy.
            """
            @functools.wraps(fn)
            def inner(*args):
                result = fn(*args)
                if not isinstance(result, tuple):
                    result = (result,)
                return result + (gr.update(selected=tab_id),)
            return inner

        # ---- Algebra ----
        def graphable_value(operation, kind, *args, **kwargs):
            """
            Plain-text result expression for the "📈 Graph result" button.

            Returns "" when there is nothing sensible to plot -- a failed
            computation, an operation with no single expression (solve returns
            a set of roots), or a result in more than one variable, which the
            2D plotter cannot draw.
            """
            resolver = algebra_result_value if kind == "algebra" else calculus_result_value
            try:
                ok, value = resolver(operation, *args, **kwargs)
            except Exception:
                return ""
            if not ok:
                return ""
            if len(getattr(value, "free_symbols", set())) > 1:
                return ""
            return str(value)

        def op_simplify(expr, hist):
            r = guarded(simplify_expression, expr); h = push_history("simplify", expr, hist, r)
            return r, h, render_history(h), graphable_value("simplify", "algebra", expr)
        def op_expand(expr, hist):
            r = guarded(expand_expression, expr); h = push_history("expand", expr, hist, r)
            return r, h, render_history(h), graphable_value("expand", "algebra", expr)
        def op_factor(expr, hist):
            r = guarded(factor_expression, expr); h = push_history("factor", expr, hist, r)
            return r, h, render_history(h), graphable_value("factor", "algebra", expr)
        def op_solve(expr, var, hist):
            r = guarded(solve_equation, expr, var); h = push_history("solve", expr, hist, r)
            # solve returns a set of roots, not one curve -- nothing to graph.
            return r, h, render_history(h), ""
        def op_evaluate(expr, subs_str, hist):
            if not subs_str or not subs_str.strip():
                r = guarded(evaluate_expression, expr)
            else:
                subs = {}
                parse_error = None
                for pair in subs_str.split(','):
                    if '=' not in pair:
                        continue
                    k, v = pair.split('=', 1)
                    v_success, v_parsed = parse_expression(v.strip())
                    if not v_success:
                        parse_error = f"❌ Error parsing substitution '{pair.strip()}': {v_parsed}"
                        break
                    subs[k.strip()] = v_parsed
                r = parse_error if parse_error else guarded(evaluate_expression, expr, subs)
            h = push_history("evaluate", expr, hist, r)
            # Only graphable when nothing was substituted; with substitutions
            # the result is a number, not a curve.
            value = "" if (subs_str or "").strip() else graphable_value("evaluate", "algebra", expr)
            return r, h, render_history(h), value

        ALG_OUT = [alg_output, history, history_display, alg_value, alg_latex, main_tabs]
        sb_simplify.click(with_tab(op_simplify, "alg"), inputs=[alg_expr, history], outputs=ALG_OUT)
        sb_expand.click(with_tab(op_expand, "alg"),     inputs=[alg_expr, history], outputs=ALG_OUT)
        sb_factor.click(with_tab(op_factor, "alg"),     inputs=[alg_expr, history], outputs=ALG_OUT)
        sb_solve.click(with_tab(op_solve, "alg"),       inputs=[alg_expr, alg_var, history], outputs=ALG_OUT)
        sb_evaluate.click(with_tab(op_evaluate, "alg"), inputs=[alg_expr, alg_subs, history], outputs=ALG_OUT)

        # ---- Calculus ----
        def append_steps(result, steps_markdown):
            """Attach step-by-step working, unless either part failed."""
            if result.startswith("❌") or not steps_markdown:
                return result
            if steps_markdown.startswith("❌"):
                return result + f"\n\n_Steps unavailable: {steps_markdown.lstrip('❌ ')}_\n"
            return result + "\n\n" + steps_markdown

        def op_deriv(expr, var, order, steps, numeric, hist):
            order = int(order)
            r = guarded(calculate_derivative, expr, var, order, bool(numeric))
            if steps:
                if order == 1:
                    r = append_steps(r, guarded(derivative_steps, expr, var))
                else:
                    # The stepper explains one differentiation; showing it for
                    # an nth derivative would describe only the last pass.
                    r = append_steps(r, "_Steps are shown for first-order derivatives only._")
            h = push_history("derivative", expr, hist, r)
            return r, h, render_history(h), graphable_value("derivative", "calculus", expr, var, order)

        def op_integ(expr, var, definite, lower, upper, steps, numeric, hist):
            if definite:
                if not lower or not upper:
                    r = "❌ Definite integral is checked but Lower Bound and/or Upper Bound is empty. Provide both, or uncheck Definite Integral."
                else:
                    r = guarded(calculate_integral, expr, var, True, lower, upper, bool(numeric))
            else:
                r = guarded(calculate_integral, expr, var, False, None, None, bool(numeric))
            if steps:
                if definite:
                    # SymPy's stepper works on the antiderivative; the bounds
                    # are applied afterwards and have no rules of their own.
                    r = append_steps(r, "_Steps are shown for indefinite integrals only._")
                else:
                    r = append_steps(r, guarded(integral_steps_markdown, expr, var))
            h = push_history("integral", expr, hist, r)
            value = "" if definite else graphable_value("integral", "calculus", expr, var)
            return r, h, render_history(h), value

        def op_limit(expr, var, point, direction, numeric, hist):
            r = guarded(calculate_limit, expr, var, point, direction, bool(numeric))
            h = push_history("limit", expr, hist, r)
            # A limit is a single number, not a curve.
            return r, h, render_history(h), ""

        def op_taylor(expr, var, point, order, hist):
            order = int(order)
            r = guarded(taylor_series, expr, var, point, order)
            h = push_history("taylor", expr, hist, r)
            return r, h, render_history(h), graphable_value("taylor", "calculus", expr, var, order, point)

        CAL_OUT = [cal_output, history, history_display, cal_value, cal_latex, main_tabs]
        sb_derivative.click(with_tab(op_deriv, "cal"),  inputs=[cal_expr, cal_var, cal_order, cal_steps, cal_numeric, history],                                    outputs=CAL_OUT)
        sb_integral.click(with_tab(op_integ, "cal"),    inputs=[cal_expr, cal_var, cal_definite, cal_lower, cal_upper, cal_steps, cal_numeric, history],           outputs=CAL_OUT)
        sb_limit.click(with_tab(op_limit, "cal"),       inputs=[cal_expr, cal_var, cal_point, cal_dir, cal_numeric, history],                                      outputs=CAL_OUT)
        sb_taylor.click(with_tab(op_taylor, "cal"),     inputs=[cal_expr, cal_var, cal_point, cal_order, history],                                                 outputs=CAL_OUT)

        # ---- Matrices ----
        def mwrap(func, name):
            def inner(a, hist):
                r = guarded(func, a); h = push_history(name, a, hist, r); return r, h, render_history(h)
            # Only the name is copied, deliberately -- not functools.wraps.
            # wraps also sets __wrapped__, which inspect.signature follows, so
            # Gradio would read the core function's signature
            # (matrix_determinant(matrix_string)) instead of this closure's
            # real (a, hist): startup arity warnings, and an API that rejects
            # its own arguments. The name alone is what makes the generated
            # endpoint readable.
            inner.__name__ = func.__name__
            return inner
        def op_mmult(a, b, hist):
            r = guarded(matrix_multiply, a, b); h = push_history("multiply", "A × B", hist, r); return r, h, render_history(h)

        MAT_OUT = [mat_output, history, history_display, mat_latex, main_tabs]
        sb_det.click(with_tab(mwrap(matrix_determinant, "det"), "mat"),             inputs=[mat_a, history], outputs=MAT_OUT)
        sb_inv.click(with_tab(mwrap(matrix_inverse, "inverse"), "mat"),             inputs=[mat_a, history], outputs=MAT_OUT)
        sb_transpose.click(with_tab(mwrap(matrix_transpose, "transpose"), "mat"),   inputs=[mat_a, history], outputs=MAT_OUT)
        sb_eigenval.click(with_tab(mwrap(matrix_eigenvalues, "eigenvalues"), "mat"), inputs=[mat_a, history], outputs=MAT_OUT)
        sb_eigenvec.click(with_tab(mwrap(matrix_eigenvectors, "eigenvectors"), "mat"), inputs=[mat_a, history], outputs=MAT_OUT)
        sb_rank.click(with_tab(mwrap(matrix_rank, "rank"), "mat"),                  inputs=[mat_a, history], outputs=MAT_OUT)
        sb_rref.click(with_tab(mwrap(matrix_rref, "rref"), "mat"),                  inputs=[mat_a, history], outputs=MAT_OUT)
        sb_multiply.click(with_tab(op_mmult, "mat"),                                inputs=[mat_a, mat_b, history], outputs=MAT_OUT)

        # ---- Graphs ----
        def op_plot2d(e1, e2, e3, xmin, xmax, hist):
            fig, status = guarded(plot_2d, [e for e in [e1, e2, e3] if e], xmin, xmax, returns_figure=True)
            h = push_history("plot 2d", e1 or "", hist, status); return fig, status, h, render_history(h)
        def op_plot3d(expr, xmin, xmax, ymin, ymax, xvar, yvar, hist):
            fig, status = guarded(plot_3d, expr, xmin, xmax, ymin, ymax, xvar, yvar, returns_figure=True)
            h = push_history("plot 3d", expr, hist, status); return fig, status, h, render_history(h)
        def op_plotparam(xe, ye, tmin, tmax, hist):
            fig, status = guarded(plot_parametric, xe, ye, tmin, tmax, returns_figure=True)
            h = push_history("parametric", f"({xe}, {ye})", hist, status); return fig, status, h, render_history(h)

        # Each graph has one input list, one output list, and one handler,
        # shared by three triggers: the sidebar button, the in-pane "Plot"
        # button, and Enter in any of that pane's fields.
        G2D_IN  = [g2d_e1, g2d_e2, g2d_e3, g2d_xmin, g2d_xmax, history]
        G2D_OUT = [g2d_plot, g2d_status, history, history_display, main_tabs]
        G3D_IN  = [g3d_expr, g3d_xmin, g3d_xmax, g3d_ymin, g3d_ymax, g3d_xvar, g3d_yvar, history]
        G3D_OUT = [g3d_plot, g3d_status, history, history_display, main_tabs]
        GPA_IN  = [gpa_xe, gpa_ye, gpa_tmin, gpa_tmax, history]
        GPA_OUT = [gpa_plot, gpa_status, history, history_display, main_tabs]

        # Every field in a graph pane submits on Enter, not just the first one.
        # Previously only Function 1 / Function / x(t) were wired, so editing a
        # range or a second function and pressing Enter did nothing at all --
        # and there was no Plot button near the inputs either, leaving the
        # sidebar button as the only working trigger.
        G2D_FIELDS = [g2d_e1, g2d_e2, g2d_e3, g2d_xmin, g2d_xmax]
        G3D_FIELDS = [g3d_expr, g3d_xvar, g3d_yvar, g3d_xmin, g3d_xmax, g3d_ymin, g3d_ymax]
        GPA_FIELDS = [gpa_xe, gpa_ye, gpa_tmin, gpa_tmax]

        for trigger in [sb_plot2d.click, g2d_go.click] + [f.submit for f in G2D_FIELDS]:
            trigger(with_graph_tab(op_plot2d, "g2d"), inputs=G2D_IN, outputs=G2D_OUT)
        for trigger in [sb_plot3d.click, g3d_go.click] + [f.submit for f in G3D_FIELDS]:
            trigger(with_graph_tab(op_plot3d, "g3d"), inputs=G3D_IN, outputs=G3D_OUT)
        for trigger in [sb_plotparam.click, gpa_go.click] + [f.submit for f in GPA_FIELDS]:
            trigger(with_graph_tab(op_plotparam, "gpa"), inputs=GPA_IN, outputs=GPA_OUT)

        # "📈 Graph result": send the computed expression to the 2D plotter.
        # The expression comes from the off-screen value buffer that the
        # operation's handler filled in; it is empty whenever the result is not
        # a single-variable curve (solve's root set, a limit, a substituted
        # number), and the click then reports that instead of plotting nothing.
        def graph_result(value, hist):
            expression = (value or "").strip()
            if not expression:
                return (
                    None,
                    "❌ Nothing to graph — run an operation whose result is a "
                    "single-variable expression first.",
                    hist, render_history(hist), "",
                    gr.update(),
                )
            figure, status = guarded(plot_2d, [expression], -10, 10, returns_figure=True)
            h = push_history("graph result", expression, hist, status)
            return (
                figure, status, h, render_history(h), expression,
                gr.update(selected="g2d"),
            )

        GRAPH_RESULT_OUT = [
            g2d_plot, g2d_status, history, history_display, g2d_e1, main_tabs,
        ]
        alg_graph.click(graph_result, inputs=[alg_value, history], outputs=GRAPH_RESULT_OUT)
        cal_graph.click(graph_result, inputs=[cal_value, history], outputs=GRAPH_RESULT_OUT)

        # ---- Copy LaTeX (clipboard write, no server round-trip) ----
        for copy_button, buffer_id in (
            (alg_copy, "alg-latex"), (cal_copy, "cal-latex"),
            (mat_copy, "mat-latex"), (sp_copy, "spc-latex"),
        ):
            copy_button.click(
                fn=None, inputs=None, outputs=None,
                js=f"() => {{ window.mathkunjiCopyLatex && window.mathkunjiCopyLatex('{buffer_id}'); }}",
            )

        # ---- Export session ----
        # Two steps: the server renders the transcript into the hidden buffer,
        # then the browser saves it. The save is client-side because the file
        # components that would do it natively are broken in this Gradio
        # version (see the note on export_buffer above).
        export_btn.click(
            lambda hist: build_transcript(hist),
            inputs=[history],
            outputs=[export_buffer],
        ).then(
            fn=None, inputs=None, outputs=None,
            js="() => { window.mathkunjiDownloadSession && window.mathkunjiDownloadSession(); }",
        )

        # ---- Special Functions ----
        # The trailing `numeric` flag reaches the evaluator as its show_numeric
        # argument, so the decimal is computed where the result already exists
        # rather than being recomputed here.
        # Name-only copying here too -- see the note in mwrap().
        def sp_wrap1(func, name):
            def inner(a, numeric, hist):
                r = guarded(func, a, bool(numeric)); h = push_history(name, a, hist, r); return r, h, render_history(h)
            inner.__name__ = func.__name__
            return inner
        def sp_wrap2(func, name):
            def inner(a, b, numeric, hist):
                r = guarded(func, a, b, bool(numeric)); h = push_history(name, a, hist, r); return r, h, render_history(h)
            inner.__name__ = func.__name__
            return inner
        def sp_wrap3(func, name):
            def inner(a, b, c, numeric, hist):
                r = guarded(func, a, b, c, bool(numeric)); h = push_history(name, a, hist, r); return r, h, render_history(h)
            inner.__name__ = func.__name__
            return inner

        SPC_OUT = [sp_output, history, history_display, sp_latex, main_tabs]
        SPC_IN1 = [sp_arg1, sp_numeric, history]
        SPC_IN2 = [sp_arg1, sp_arg2, sp_numeric, history]
        SPC_IN3 = [sp_arg1, sp_arg2, sp_arg3, sp_numeric, history]

        sb_gamma.click(with_tab(sp_wrap1(evaluate_gamma, "gamma"), "spc"),                       inputs=SPC_IN1, outputs=SPC_OUT)
        sb_zeta.click(with_tab(sp_wrap1(evaluate_zeta, "zeta"), "spc"),                          inputs=SPC_IN1, outputs=SPC_OUT)
        sb_factorial.click(with_tab(sp_wrap1(evaluate_factorial, "factorial"), "spc"),           inputs=SPC_IN1, outputs=SPC_OUT)
        sb_binomial.click(with_tab(sp_wrap2(evaluate_binomial, "binomial"), "spc"),              inputs=SPC_IN2, outputs=SPC_OUT)
        sb_erf.click(with_tab(sp_wrap1(evaluate_erf, "erf"), "spc"),                             inputs=SPC_IN1, outputs=SPC_OUT)
        sb_erfc.click(with_tab(sp_wrap1(evaluate_erfc, "erfc"), "spc"),                          inputs=SPC_IN1, outputs=SPC_OUT)
        sb_besselj.click(with_tab(sp_wrap2(evaluate_besselj, "Bessel J"), "spc"),                inputs=SPC_IN2, outputs=SPC_OUT)
        sb_bessely.click(with_tab(sp_wrap2(evaluate_bessely, "Bessel Y"), "spc"),                inputs=SPC_IN2, outputs=SPC_OUT)
        sb_besseli.click(with_tab(sp_wrap2(evaluate_besseli, "Bessel I"), "spc"),                inputs=SPC_IN2, outputs=SPC_OUT)
        sb_besselk.click(with_tab(sp_wrap2(evaluate_besselk, "Bessel K"), "spc"),                inputs=SPC_IN2, outputs=SPC_OUT)
        sb_hermite.click(with_tab(sp_wrap2(evaluate_hermite, "Hermite"), "spc"),                 inputs=SPC_IN2, outputs=SPC_OUT)
        sb_legendre.click(with_tab(sp_wrap2(evaluate_legendre, "Legendre"), "spc"),              inputs=SPC_IN2, outputs=SPC_OUT)
        sb_laguerre.click(with_tab(sp_wrap2(evaluate_laguerre, "Laguerre"), "spc"),              inputs=SPC_IN2, outputs=SPC_OUT)
        sb_chebyshevt.click(with_tab(sp_wrap2(evaluate_chebyshevt, "Chebyshev T"), "spc"),       inputs=SPC_IN2, outputs=SPC_OUT)
        sb_chebyshevu.click(with_tab(sp_wrap2(evaluate_chebyshevu, "Chebyshev U"), "spc"),       inputs=SPC_IN2, outputs=SPC_OUT)
        sb_asslegendre.click(with_tab(sp_wrap3(evaluate_assoc_legendre, "Assoc Legendre"), "spc"), inputs=SPC_IN3, outputs=SPC_OUT)
        sb_asslaguerre.click(with_tab(sp_wrap3(evaluate_assoc_laguerre, "Assoc Laguerre"), "spc"), inputs=SPC_IN3, outputs=SPC_OUT)

        # ---- Enter-to-submit per active panel (default primary action) ----
        # Bound through the same wrappers as the sidebar buttons so pressing
        # Enter behaves identically to clicking, including the tab switch and
        # the Copy/Graph buffers.
        alg_expr.submit(with_tab(op_simplify, "alg"), inputs=[alg_expr, history], outputs=ALG_OUT)
        cal_expr.submit(with_tab(op_deriv, "cal"),
                        inputs=[cal_expr, cal_var, cal_order, cal_steps, cal_numeric, history],
                        outputs=CAL_OUT)
        mat_a.submit(with_tab(mwrap(matrix_determinant, "det"), "mat"), inputs=[mat_a, history], outputs=MAT_OUT)
        # The graph panes are not listed here: every one of their fields is
        # already bound to submit in the per-pane loops above. Repeating them
        # would register the handler twice and plot twice per Enter.

        # ---- Fullscreen plot: enter, and (crucially) leave ----
        # Pure client-side, no server round-trip. The real work lives in the
        # mathkunjiToggleFullscreen / mathkunjiExitFullscreen helpers defined in the
        # inline script below, so the buttons and the Esc key share one
        # implementation rather than each poking at the body class.
        for btn in (g2d_fs, g3d_fs, gpa_fs):
            btn.click(fn=None, inputs=None, outputs=None,
                      js="() => { window.mathkunjiToggleFullscreen && window.mathkunjiToggleFullscreen(); }")
        for btn in (g2d_fs_exit, g3d_fs_exit, gpa_fs_exit):
            btn.click(fn=None, inputs=None, outputs=None,
                      js="() => { window.mathkunjiExitFullscreen && window.mathkunjiExitFullscreen(); }")

    return app


if __name__ == "__main__":
    app = create_app()

    # No share= argument, deliberately. Gradio's share option opens a public
    # tunnel through Gradio's relay infrastructure, which would put an app that
    # evaluates user-supplied expressions on the open internet. MathKunji is a
    # local desktop tool with no external API surface; reaching
    # it from anywhere other than the machine it runs on is not a feature.
    # Access is controlled by the host-side port binding in docker-compose.yml.
    #
    # quiet=True suppresses Gradio's own two startup lines, which are actively
    # misleading for this deployment:
    #
    #   "Running on local URL: http://0.0.0.0:7860"
    #       -- the CONTAINER-side socket, printed from inside the container's
    #          own network namespace. It reads like an exposed bind, but the
    #          host only ever publishes on 127.0.0.1 (docker-compose.yml).
    #          It has to stay 0.0.0.0 inside, or Docker cannot forward to it.
    #
    #   "To create a public link, set `share=True` in `launch()`."
    #       -- Gradio prints this precisely BECAUSE sharing is off; it is the
    #          else-branch of the share check in gradio/blocks.py. It reads
    #          like an offer, not a statement of the current state.
    #
    # prevent_thread_lock=True lets the banner below print once the server is
    # genuinely listening rather than before; block_thread() then restores the
    # normal blocking behaviour so the container stays in the foreground.
    app.launch(quiet=True, prevent_thread_lock=True)

    print("=" * 46, flush=True)
    print("  MathKunji is ready", flush=True)
    print("  Open http://localhost:7860 on this machine", flush=True)
    print("  Local only - no public share link", flush=True)
    print("=" * 46, flush=True)

    app.block_thread()
