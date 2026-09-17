"""
Strip Gradio's hardcoded external requests from its frontend template.

Gradio ships an index.html that preconnects to Google's two font hosts and
pulls iframe-resizer from cdnjs. MathKunji promises it makes no network
requests, and none of the three is needed to keep that promise:

  * The two preconnect hints exist to warm a connection for the font stylesheet
    Gradio's theme would otherwise request. app.py passes plain font names to
    gr.themes.Base rather than gr.themes.GoogleFont, so no stylesheet is ever
    requested -- leaving the hints to perform DNS, TCP and TLS against Google
    for a resource that is never fetched.

  * iframeResizer.contentWindow.js is the child half of iframe-resizer: it lets
    an embedded page report its height to the parent frame around it. This app
    is opened as a direct browser tab and publishes to loopback only, so it is
    never inside an iframe and the script has nothing to do.

Runs at image build time, after pip install.

Gradio is pinned to an exact version, so the template cannot change underneath
a build and these patterns cannot silently stop matching. The loud failure
below matters on the day someone raises that pin: rather than quietly leaving
the requests in place, the build stops and says which block it could not find.

Can also be run by hand against a local, non-Docker install:

    python scripts/strip_external_requests.py
"""

import pathlib
import re
import sys

import gradio

TEMPLATE = pathlib.Path(gradio.__file__).parent / "templates" / "frontend" / "index.html"

# Indentation is deliberately loose (`[ \t]*`, `\s+`) so that a whitespace or
# line-wrapping change between Gradio releases does not defeat the patch. The
# hostnames themselves are exact -- matching those loosely would risk removing
# something this patch was never meant to touch.
TARGETS = (
    (
        "preconnect to fonts.googleapis.com",
        re.compile(r'[ \t]*<link[^>]*?href="https://fonts\.googleapis\.com"[^>]*?/>\n'),
    ),
    (
        "preconnect to fonts.gstatic.com",
        re.compile(r'[ \t]*<link\s[^>]*?href="https://fonts\.gstatic\.com"[^>]*?/>\n'),
    ),
    (
        "iframe-resizer script from cdnjs.cloudflare.com",
        re.compile(r'[ \t]*<script\s[^>]*?src="https://cdnjs\.cloudflare\.com/[^"]*"[^>]*?>\s*</script>\n'),
    ),
)

FORBIDDEN_HOSTS = ("fonts.googleapis.com", "fonts.gstatic.com", "cdnjs.cloudflare.com")


def main():
    if not TEMPLATE.is_file():
        sys.exit(f"Gradio template not found at {TEMPLATE}")

    html = TEMPLATE.read_text(encoding="utf-8")

    for label, pattern in TARGETS:
        html, count = pattern.subn("", html)
        if count == 0:
            sys.exit(
                f"Could not find: {label}\n\n"
                f"Gradio's template no longer matches what this patch expects, so "
                f"the external requests were NOT removed. Read\n  {TEMPLATE}\n"
                f"and update the pattern in scripts/strip_external_requests.py."
            )
        print(f"removed {count}x {label}")

    # Belt and braces: a pattern could in principle match a rewritten block
    # while leaving another copy of the same host elsewhere in the file.
    remaining = [host for host in FORBIDDEN_HOSTS if host in html]
    if remaining:
        sys.exit(f"Still referenced after patching: {', '.join(remaining)}")

    TEMPLATE.write_text(html, encoding="utf-8")
    print(f"Patched {TEMPLATE}")


if __name__ == "__main__":
    main()
