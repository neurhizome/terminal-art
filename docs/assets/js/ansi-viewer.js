/**
 * ANSI Viewer — render terminal captures in the browser via xterm.js v5
 *
 * Reads cols/rows from the capture file's metadata header so the terminal
 * frame is bounded to the exact dimensions of the recorded artifact.
 *
 * One Dark terminal theme to match site palette.
 */

// Jekyll injects window.SITE_BASEURL before this script loads (set in <head>).
const _baseUrl = (typeof window !== 'undefined' && window.SITE_BASEURL != null)
    ? window.SITE_BASEURL
    : '';

// One Dark terminal theme — joshdick/onedark.vim
const ONE_DARK_THEME = {
    background:          '#1e2127',
    foreground:          '#abb2bf',
    cursor:              '#528bff',
    cursorAccent:        '#1e2127',
    selectionBackground: 'rgba(97,175,239,0.25)',
    black:         '#282c34',
    red:           '#e06c75',
    green:         '#98c379',
    yellow:        '#e5c07b',
    blue:          '#61afef',
    magenta:       '#c678dd',
    cyan:          '#56b6c2',
    white:         '#abb2bf',
    brightBlack:   '#5c6370',
    brightRed:     '#e06c75',
    brightGreen:   '#98c379',
    brightYellow:  '#e5c07b',
    brightBlue:    '#61afef',
    brightMagenta: '#c678dd',
    brightCyan:    '#56b6c2',
    brightWhite:   '#ffffff',
};

/**
 * Parse the comment-header of a capture file.
 *
 * Header lines look like:  # key: value
 * Content begins at the first non-# line.
 *
 * Returns { meta: { key: value, ... }, content: "the rest of the file" }
 */
function parseCaptureFile(raw) {
    const lines = raw.split('\n');
    const meta = {};
    let i = 0;
    for (; i < lines.length; i++) {
        if (!lines[i].startsWith('#')) break;
        const m = lines[i].match(/^#\s*(\w+)\s*:\s*(.+)/);
        if (m) meta[m[1].toLowerCase()] = m[2].trim();
    }
    // Skip a single blank separator line between header and content, if present
    if (i < lines.length && lines[i].trim() === '') i++;
    return { meta, content: lines.slice(i).join('\n') };
}

/**
 * Render an ANSI capture file inside a terminal element.
 *
 * The terminal is sized to exactly the cols×rows declared in the capture's
 * metadata header (with sensible defaults if the keys are absent).
 *
 * @param {string} captureFile  Filename inside assets/captures/
 * @param {string} elementId    ID of the container <div>
 * @param {object} [opts]       Fallback overrides: { cols, rows, fontSize }
 */
async function renderCapture(captureFile, elementId, opts = {}) {
    const el = document.getElementById(elementId);
    if (!el) {
        console.error(`[ansi-viewer] #${elementId} not found`);
        return;
    }

    // ── 1. Fetch the capture file ────────────────────────────────────────
    let raw;
    try {
        const url = `${_baseUrl}/assets/captures/${captureFile}`;
        const res = await fetch(url);
        if (!res.ok) throw new Error(`HTTP ${res.status} — ${url}`);
        raw = await res.text();
    } catch (err) {
        console.error(`[ansi-viewer] fetch failed:`, err);
        el.innerHTML =
            `<p style="color:#e06c75;padding:1rem;font-family:monospace;font-size:0.9rem">` +
            `Could not load capture: ${err.message}</p>`;
        return;
    }

    // ── 2. Parse metadata so we know the artifact dimensions ─────────────
    const { meta, content } = parseCaptureFile(raw);

    const cols     = parseInt(meta.cols)     || opts.cols     || 80;
    const rows     = parseInt(meta.rows)     || opts.rows     || 24;
    const fontSize = parseInt(meta.fontsize) || opts.fontSize || 13;

    // ── 3. Wait for fonts so xterm measures character cells correctly ─────
    if (document.fonts && document.fonts.ready) {
        await document.fonts.ready;
    }

    // ── 4. Build xterm.js terminal at exact artifact dimensions ──────────
    const term = new Terminal({
        cols,
        rows,
        disableStdin:  true,
        cursorBlink:   false,
        scrollback:    0,
        fontFamily:    "'IBM Plex Mono', 'Courier New', monospace",
        fontSize,
        lineHeight:    1.0,
        letterSpacing: 0,
        theme:         ONE_DARK_THEME,
    });

    term.open(el);
    term.write(content);
}
