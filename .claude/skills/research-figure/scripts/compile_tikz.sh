#!/bin/bash
# compile_tikz.sh - Compile a TikZ .tex file to PDF and PNG
# Usage: ./compile_tikz.sh <input.tex> [dpi]
# Output: <input>.pdf and <input>.png in the same directory

set -euo pipefail

# --- Arguments ---
TEX_FILE="${1:?Usage: compile_tikz.sh <input.tex> [dpi]}"
DPI="${2:-300}"

# --- Validate input ---
if [[ ! -f "$TEX_FILE" ]]; then
    echo "ERROR: File not found: $TEX_FILE"
    exit 1
fi

if [[ "${TEX_FILE##*.}" != "tex" ]]; then
    echo "ERROR: Input must be a .tex file"
    exit 1
fi

# --- Resolve paths ---
TEX_DIR="$(cd "$(dirname "$TEX_FILE")" && pwd)"
TEX_BASE="$(basename "$TEX_FILE" .tex)"
PDF_FILE="$TEX_DIR/$TEX_BASE.pdf"
PNG_FILE="$TEX_DIR/$TEX_BASE.png"

# --- Check for pdflatex ---
if ! command -v pdflatex &>/dev/null; then
    echo "ERROR: pdflatex not found."
    echo "Please install a TeX distribution:"
    echo "  macOS:  brew install --cask mactex-no-gui"
    echo "  Ubuntu: sudo apt-get install texlive-full"
    echo "  Arch:   sudo pacman -S texlive-most"
    exit 1
fi

# --- Compile (two passes for references) ---
echo "Compiling $TEX_FILE ..."
COMPILE_LOG="$TEX_DIR/$TEX_BASE.compile.log"

compile_once() {
    pdflatex -interaction=nonstopmode -halt-on-error \
        -output-directory="$TEX_DIR" \
        "$TEX_FILE" > "$COMPILE_LOG" 2>&1
}

if ! compile_once; then
    echo "ERROR: pdflatex compilation failed."
    echo "--- Key errors from log ---"
    # Extract error lines (lines starting with !) and a few lines of context
    grep -A 3 '^!' "$COMPILE_LOG" 2>/dev/null || tail -20 "$COMPILE_LOG"
    echo "--- Full log at: $COMPILE_LOG ---"
    exit 1
fi

# Second pass (for any cross-references)
compile_once 2>/dev/null || true

if [[ ! -f "$PDF_FILE" ]]; then
    echo "ERROR: PDF not generated. Check $COMPILE_LOG"
    exit 1
fi

echo "PDF generated: $PDF_FILE"

# --- Convert PDF to PNG ---
convert_success=false

# Method 1: pdftoppm (from poppler, best quality)
if command -v pdftoppm &>/dev/null; then
    echo "Converting PDF to PNG using pdftoppm (dpi=$DPI) ..."
    pdftoppm -png -r "$DPI" -singlefile "$PDF_FILE" "$TEX_DIR/$TEX_BASE"
    if [[ -f "$PNG_FILE" ]]; then
        convert_success=true
    fi
fi

# Method 2: sips (macOS built-in) - need to handle DPI scaling manually
if [[ "$convert_success" == false ]] && command -v sips &>/dev/null; then
    echo "Converting PDF to PNG using sips (dpi=$DPI) ..."
    # sips converts PDF at 72dpi by default, need to scale up
    sips -s format png "$PDF_FILE" --out "$PNG_FILE" &>/dev/null
    if [[ -f "$PNG_FILE" ]]; then
        # Scale up to match requested DPI (sips default is 72dpi)
        SCALE_FACTOR=$(echo "scale=2; $DPI / 72" | bc)
        ORIG_W=$(sips -g pixelWidth "$PNG_FILE" | tail -1 | awk '{print $2}')
        ORIG_H=$(sips -g pixelHeight "$PNG_FILE" | tail -1 | awk '{print $2}')
        NEW_W=$(echo "$ORIG_W * $SCALE_FACTOR / 1" | bc)
        NEW_H=$(echo "$ORIG_H * $SCALE_FACTOR / 1" | bc)
        sips -z "$NEW_H" "$NEW_W" "$PNG_FILE" &>/dev/null
        convert_success=true
    fi
fi

# Method 3: ImageMagick convert
if [[ "$convert_success" == false ]] && command -v convert &>/dev/null; then
    echo "Converting PDF to PNG using ImageMagick ..."
    convert -density "$DPI" "$PDF_FILE" "$PNG_FILE" 2>/dev/null
    if [[ -f "$PNG_FILE" ]]; then
        convert_success=true
    fi
fi

if [[ "$convert_success" == false ]]; then
    echo "WARNING: Could not convert PDF to PNG."
    echo "Install one of: poppler (pdftoppm), ImageMagick (convert)"
    echo "  macOS:  brew install poppler"
    echo "  Ubuntu: sudo apt-get install poppler-utils"
    echo "PDF is still available at: $PDF_FILE"
    exit 0
fi

echo "PNG generated: $PNG_FILE"

# --- Cleanup temporary files ---
for ext in aux log out toc nav snm vrb fls fdb_latexmk synctex.gz compile.log; do
    rm -f "$TEX_DIR/$TEX_BASE.$ext"
done

echo "Done. Output files:"
echo "  PDF: $PDF_FILE"
echo "  PNG: $PNG_FILE"
