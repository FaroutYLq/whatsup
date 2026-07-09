# Zotero Library Export Guide

This guide explains how to export your Zotero library so the 
ArXiv Weekly Digest can understand your research interests.

## Why Export Your Zotero Library?

The system analyzes your existing research papers (titles, 
abstracts, keywords) to build a profile of your interests. 
This helps the LLM make better recommendations.

## Export Methods

You can export your library in two formats:
- **BibTeX (.bib)** - Recommended
- **JSON (.json)** - Alternative

---

## Method 1: BibTeX Export (Recommended)

### Step 1: Open Zotero

Launch the Zotero desktop application.

### Step 2: Select Library or Collection

- To export your **entire library**: 
  Click on "My Library" in the left sidebar
- To export a **specific collection**: 
  Click on the collection you want to export

### Step 3: Export

1. Go to **File → Export Library...** 
   (or "Export Collection..." if you selected a collection)

2. In the export dialog:
   - **Format**: Select "BibTeX"
   - **Character Encoding**: UTF-8 (default)
   - Optionally check "Include Notes" and "Include Files" 
     if you want more context

3. Click **OK**

4. Choose a location to save the file 
   (e.g., `~/Documents/zotero_library.bib`)

5. Click **Save**

### Step 4: Update Configuration

Open your `config.yaml` and update the path:

```yaml
zotero:
  library_file: /Users/yourusername/Documents/zotero_library.bib
```

---

## Method 2: JSON Export (Alternative)

### Using Better BibTeX Plugin (Recommended for JSON)

1. **Install Better BibTeX plugin** (if not already installed):
   - Download from: 
     https://github.com/retorquere/zotero-better-bibtex
   - In Zotero: Tools → Add-ons → Install Add-on From File

2. **Export**:
   - Select your library or collection
   - Go to **File → Export Library...**
   - **Format**: Select "Better CSL JSON"
   - Click **OK** and save

3. **Update Configuration**:
   ```yaml
   zotero:
     library_file: /path/to/your/export.json
   ```

### Using Standard JSON Export

1. Select your library or collection
2. Go to **File → Export Library...**
3. **Format**: Select "Zotero RDF"
4. Click **OK** and save

Note: Standard JSON export may have limited metadata. 
BibTeX is recommended.

---

## What Information is Extracted?

The system extracts:
- **Titles**: Paper titles
- **Abstracts**: Paper abstracts (if available)
- **Authors**: Author names
- **Keywords/Tags**: Research topics
- **Year**: Publication year

## Tips

1. **Keep it updated**: Re-export your library periodically 
   (monthly) to keep recommendations fresh

2. **Quality over quantity**: The system samples up to 20 
   recent papers. Having a focused collection in your 
   library helps

3. **Add abstracts**: Papers with abstracts provide better 
   context. Import papers with full metadata when possible

4. **Use tags**: Zotero tags/keywords help the system 
   understand topics

---

## Troubleshooting

### "Library file not found" error

- Check the file path in `config.yaml` is correct
- Use absolute paths (e.g., `/Users/name/file.bib`)
- Ensure the file exists at that location

### "Unsupported file format" error

- Verify the file extension is `.bib` or `.json`
- Re-export using one of the methods above

### Limited recommendations

- Ensure your exported library has papers with abstracts
- Add more specific keywords/tags to your Zotero papers
- Update your `interests.description` in config.yaml

---

## Alternative: No Zotero Library

If you don't use Zotero or prefer not to export:

1. Leave the library_file path as-is (or point to 
   a non-existent file)
2. Write detailed interests in `config.yaml`:

```yaml
interests:
  description: |
    My research focuses on:
    - Superconducting quantum devices
    - Quasiparticle dynamics and tunneling
    - THz detection technologies
    - Applications in cosmology and particle physics
    [Add specific topics, methods, materials, etc.]
```

The system will rely entirely on your written description.

