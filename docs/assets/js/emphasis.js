/**
 * Inline emphasis processor for terminal-art blog
 *
 * Transforms  [[flags|text]]  patterns in post content into styled <span>s.
 * Walks real DOM text nodes — skips <code> and <pre> — so source examples
 * are never accidentally styled.
 *
 * ── Syntax ────────────────────────────────────────────────────────────────
 *
 *   [[flags|text to style]]
 *
 *   flags is a comma-separated list of any of:
 *
 *   Modifier   Effect
 *   ────────   ──────────────────────────────────────────
 *   b          bold (font-weight 700)
 *   i          italic
 *   m          monospace (IBM Plex Mono, 0.9em)
 *
 *   Palette name  Color           Hex
 *   ────────────  ──────────────  ────────
 *   gr            green           #98c379
 *   cy            cyan            #56b6c2
 *   bl            blue            #61afef
 *   pu            purple          #c678dd
 *   re            red             #e06c75
 *   ye            yellow          #e5c07b
 *   or            orange          #d19a66
 *   dim           subdued grey    #828997
 *
 *   Hex / RGB     Effect
 *   ───────────   ──────────────────────────────
 *   #rrggbb       foreground color (hex)
 *   bg#rrggbb     background color (hex)
 *   fg(r,g,b)     foreground color (24-bit RGB, 0-255)
 *   bg(r,g,b)     background color (24-bit RGB, 0-255)
 *
 *   Background flags also add a subtle border-radius and padding so the
 *   highlight feels like a terminal selection rather than a paint bucket.
 *
 * ── Examples ──────────────────────────────────────────────────────────────
 *
 *   [[b,gr|important discovery]]
 *   [[i,pu|Walker]]
 *   [[b,i,ye|critical insight]]
 *   [[b,cy,bg#1e2127|cyan on terminal dark]]
 *   [[b,fg(152,195,121)|precise RGB green]]
 *   [[i,bg(40,44,52)|subtle panel highlight]]
 *
 * ── Notes ─────────────────────────────────────────────────────────────────
 *
 *   • Nesting [[…]] is not supported.
 *   • Text inside <code> and <pre> is intentionally left alone.
 *   • Applied to .post-content and .content on DOMContentLoaded.
 */

'use strict';

// ── One Dark palette shortcuts ─────────────────────────────────────────────

const PALETTE = {
    gr:  '#98c379',   // green
    cy:  '#56b6c2',   // cyan
    bl:  '#61afef',   // blue
    pu:  '#c678dd',   // purple
    re:  '#e06c75',   // red
    ye:  '#e5c07b',   // yellow
    or:  '#d19a66',   // orange
    dim: '#828997',   // subdued
};

// ── Flag tokenizer ─────────────────────────────────────────────────────────
// Splits "b,fg(152,195,121),bg#1e2127" respecting parentheses so that
// the r,g,b commas inside fg()/bg() are not treated as flag separators.

function tokenize(flagStr) {
    const tokens = [];
    let buf = '';
    let depth = 0;
    for (const ch of flagStr) {
        if      (ch === '(') { depth++; buf += ch; }
        else if (ch === ')') { depth--; buf += ch; }
        else if (ch === ',' && depth === 0) {
            const t = buf.trim();
            if (t) tokens.push(t);
            buf = '';
        } else {
            buf += ch;
        }
    }
    const t = buf.trim();
    if (t) tokens.push(t);
    return tokens;
}

// ── Flag → CSS style string ────────────────────────────────────────────────

function flagsToStyle(flagStr) {
    const css = [];
    let hasBg = false;

    for (const token of tokenize(flagStr)) {
        // Modifiers
        if (token === 'b')   { css.push('font-weight:700');                      continue; }
        if (token === 'i')   { css.push('font-style:italic');                    continue; }
        if (token === 'm')   { css.push('font-family:monospace;font-size:0.9em'); continue; }

        // Named palette → foreground
        if (PALETTE[token])  { css.push(`color:${PALETTE[token]}`);              continue; }

        // #rrggbb or #rgb → foreground
        if (/^#[0-9a-fA-F]{3,6}$/.test(token)) {
            css.push(`color:${token}`);
            continue;
        }

        // bg#rrggbb or bg#rgb → background
        if (/^bg#[0-9a-fA-F]{3,6}$/.test(token)) {
            css.push(`background:${token.slice(2)}`);
            hasBg = true;
            continue;
        }

        // fg(r,g,b) → 24-bit RGB foreground
        const fgMatch = token.match(/^fg\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)$/);
        if (fgMatch) {
            css.push(`color:rgb(${fgMatch[1]},${fgMatch[2]},${fgMatch[3]})`);
            continue;
        }

        // bg(r,g,b) → 24-bit RGB background
        const bgMatch = token.match(/^bg\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)$/);
        if (bgMatch) {
            css.push(`background:rgb(${bgMatch[1]},${bgMatch[2]},${bgMatch[3]})`);
            hasBg = true;
            continue;
        }
    }

    // Background highlights get a terminal-selection feel
    if (hasBg) {
        css.push('border-radius:3px', 'padding:0.05em 0.35em');
    }

    return css.join(';');
}

// ── DOM text-node walker ───────────────────────────────────────────────────
// Operates on raw DOM text nodes rather than innerHTML so we never
// accidentally mutate HTML structure or double-process encoded entities.

const SKIP_TAGS = new Set(['code', 'pre', 'script', 'style', 'textarea']);
const EMPHASIS_RE = /\[\[([^\]|]+)\|([^\]]+)\]\]/g;

function processNode(el) {
    // Collect text nodes that (a) contain '[[' and (b) are not inside a skip-tag
    const candidates = [];
    const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, {
        acceptNode(node) {
            if (!node.textContent.includes('[[')) return NodeFilter.FILTER_SKIP;
            let p = node.parentElement;
            while (p && p !== el) {
                if (SKIP_TAGS.has(p.tagName.toLowerCase())) return NodeFilter.FILTER_REJECT;
                p = p.parentElement;
            }
            return NodeFilter.FILTER_ACCEPT;
        },
    });
    while (walker.nextNode()) candidates.push(walker.currentNode);

    for (const textNode of candidates) {
        const raw = textNode.textContent;
        EMPHASIS_RE.lastIndex = 0;

        // Quick check — avoid building a fragment when nothing matches
        if (!EMPHASIS_RE.test(raw)) continue;
        EMPHASIS_RE.lastIndex = 0;

        const frag = document.createDocumentFragment();
        let cursor = 0;
        let m;

        while ((m = EMPHASIS_RE.exec(raw)) !== null) {
            // Plain text before this match
            if (m.index > cursor) {
                frag.appendChild(document.createTextNode(raw.slice(cursor, m.index)));
            }

            // Styled span
            const styleStr = flagsToStyle(m[1]);
            if (styleStr) {
                const span = document.createElement('span');
                span.setAttribute('style', styleStr);
                span.textContent = m[2];
                frag.appendChild(span);
            } else {
                // No valid flags — emit text unchanged
                frag.appendChild(document.createTextNode(m[2]));
            }

            cursor = m.index + m[0].length;
        }

        // Trailing plain text
        if (cursor < raw.length) {
            frag.appendChild(document.createTextNode(raw.slice(cursor)));
        }

        textNode.parentNode.replaceChild(frag, textNode);
    }
}

// ── Entry point ────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.post-content, .content').forEach(processNode);
});
