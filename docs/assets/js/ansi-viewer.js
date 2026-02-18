/**
 * ANSI Viewer — render terminal captures in the browser via xterm.js v5
 *
 * One Dark terminal theme to match site palette.
 */

// Jekyll injects window.SITE_BASEURL from the post layout
const _baseUrl = (typeof window !== 'undefined' && window.SITE_BASEURL) ? window.SITE_BASEURL : '';

// One Dark terminal theme — matches joshdick/onedark.vim
const ONE_DARK_THEME = {
    background:    '#1e2127',
    foreground:    '#abb2bf',
    cursor:        '#528bff',
    cursorAccent:  '#1e2127',
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
 * Render an ANSI capture file inside a terminal element.
 *
 * @param {string} captureFile  Filename inside assets/captures/ (e.g. "first-run.ans")
 * @param {string} elementId    ID of the <div> to render into
 * @param {object} [opts]       Optional overrides: { cols, rows, fontSize }
 */
async function renderCapture(captureFile, elementId, opts = {}) {
    const terminalElement = document.getElementById(elementId);
    if (!terminalElement) {
        console.error(`[ansi-viewer] element #${elementId} not found`);
        return;
    }

    const cols     = opts.cols     || 80;
    const rows     = opts.rows     || 24;
    const fontSize = opts.fontSize || 13;

    // Create xterm.js v5 Terminal — all options go in the constructor;
    // setOption() was removed in v5.
    const term = new Terminal({
        cols,
        rows,
        disableStdin:  true,
        cursorBlink:   false,
        scrollback:    0,
        fontFamily:    "'IBM Plex Mono', 'Courier New', monospace",
        fontSize,
        lineHeight:    1.25,
        letterSpacing: 0,
        theme:         ONE_DARK_THEME,
    });

    term.open(terminalElement);

    try {
        const url = `${_baseUrl}/assets/captures/${captureFile}`;
        const response = await fetch(url);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status} fetching ${url}`);
        }

        const ansiContent = await response.text();

        // Strip comment/metadata header lines (lines starting with #)
        const lines = ansiContent.split('\n');
        const firstContent = lines.findIndex(l => !l.startsWith('#'));
        const content = lines.slice(firstContent >= 0 ? firstContent : 0).join('\n');

        term.write(content);

    } catch (err) {
        console.error(`[ansi-viewer] failed to load ${captureFile}:`, err);
        terminalElement.innerHTML =
            `<p style="color:#e06c75;padding:1.5rem;font-family:monospace;">` +
            `Error loading capture: ${err.message}</p>`;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    // Inline scripts in post.html call renderCapture() directly.
});
