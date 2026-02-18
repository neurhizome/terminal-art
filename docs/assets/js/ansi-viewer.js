/**
 * ANSI Viewer - Render terminal captures in the browser
 * Uses xterm.js for authentic terminal rendering
 */

/**
 * Render an ANSI capture file in a terminal element
 * @param {string} captureFile - Path to .ans file
 * @param {string} elementId - ID of element to render into
 */
async function renderCapture(captureFile, elementId) {
    try {
        // Fetch the capture file
        const response = await fetch(`/terminal-art/assets/captures/${captureFile}`);
        const ansiContent = await response.text();

        // Create terminal instance
        const terminalElement = document.getElementById(elementId);
        if (!terminalElement) {
            console.error(`Element ${elementId} not found`);
            return;
        }

        const term = new Terminal({
            cols: 80,
            rows: 24,
            theme: {
                background: '#000000',
                foreground: '#d4d4d4',
                cursor: '#d4d4d4',
                black: '#0a0e14',
                red: '#ff3333',
                green: '#7fd962',
                yellow: '#ffcc66',
                blue: '#00d9ff',
                magenta: '#d4bfff',
                cyan: '#5ccfe6',
                white: '#d4d4d4',
                brightBlack: '#606060',
                brightRed: '#ff6666',
                brightGreen: '#9fef82',
                brightYellow: '#ffdd88',
                brightBlue: '#4de9ff',
                brightMagenta: '#e4cfff',
                brightCyan: '#7cdfee',
                brightWhite: '#ffffff'
            },
            cursorBlink: false,
            fontFamily: "'IBM Plex Mono', 'Courier New', monospace",
            fontSize: 13,
            lineHeight: 1.2,
            letterSpacing: 0
        });

        // Open terminal in element
        term.open(terminalElement);

        // Strip metadata header (lines starting with #)
        const lines = ansiContent.split('\n');
        const contentStart = lines.findIndex(line => !line.startsWith('#'));
        const content = lines.slice(contentStart).join('\n');

        // Write content to terminal
        term.write(content);

        // Disable input
        term.setOption('disableStdin', true);

    } catch (error) {
        console.error(`Error loading capture ${captureFile}:`, error);
        document.getElementById(elementId).innerHTML =
            `<p style="color: #ff3333; padding: 1rem;">Error loading capture: ${error.message}</p>`;
    }
}

/**
 * Auto-detect and render all terminal displays on page load
 */
document.addEventListener('DOMContentLoaded', () => {
    // This will be called by inline scripts in post layout
    console.log('ANSI viewer initialized');
});
