#!/bin/bash
#
# ArXiv Weekly Digest Setup Script
#
# This script helps you set up the digest for first use.
#

echo "=========================================="
echo "ArXiv Weekly Digest - Setup"
echo "=========================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed!"
    echo "Please install Python 3.7 or later."
    exit 1
fi

echo "✓ Python found: $(python3 --version)"
echo ""

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "Error: pip3 is not installed!"
    echo "Please install pip."
    exit 1
fi

echo "✓ pip found"
echo ""

# Install dependencies
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo ""
    echo "Error: Failed to install dependencies!"
    exit 1
fi

echo ""
echo "✓ Dependencies installed"
echo ""

# Check if config exists
if [ ! -f "config.yaml" ]; then
    echo "Creating config.yaml from template..."
    cp config.yaml.example config.yaml
    echo "✓ config.yaml created"
    echo ""
    echo "⚠️  IMPORTANT: Edit config.yaml with your settings!"
    echo ""
    echo "You need to configure:"
    echo "  1. Email SMTP settings (see docs/GMAIL_SETUP.md)"
    echo "  2. Anthropic (Claude) API key"
    echo "  3. ArXiv categories and keywords"
    echo "  4. Your research interests"
    echo "  5. Zotero library path (see docs/ZOTERO_EXPORT.md)"
    echo ""
else
    echo "✓ config.yaml already exists"
    echo ""
fi

echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Edit config.yaml with your settings:"
echo "   nano config.yaml"
echo ""
echo "2. Read the documentation:"
echo "   - docs/GMAIL_SETUP.md - Set up email"
echo "   - docs/ZOTERO_EXPORT.md - Export your library"
echo "   - docs/CRON_SETUP.md - Automate weekly runs"
echo ""
echo "3. Test the digest:"
echo "   python src/main.py"
echo "   # or"
echo "   ./run_digest.sh"
echo ""
echo "4. Set up weekly automation (optional):"
echo "   crontab -e"
echo "   # Add: 0 8 * * * /path/to/whatsup/run_digest.sh"
echo ""
echo "For help, see: README.md"
echo ""

