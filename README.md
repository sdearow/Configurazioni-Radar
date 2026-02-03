# Radar Project Management - Roma

A dashboard tool for managing the installation and configuration of 800 radars across ~200 road intersections in Rome.

## Quick Start

### Option 1: Open directly in browser
Simply double-click `index.html` to open the dashboard in your default browser.

### Option 2: Run with a local server (recommended for full functionality)
```bash
# Using Python (if installed)
python -m http.server 8000

# Then open http://localhost:8000 in your browser
```

## Features

- **Map View**: Interactive map of Rome showing all intersection locations
  - Color-coded by stage, lotto, system, or status
  - Filter by multiple criteria
  - Click markers to see details

- **Progress Dashboard**: Visual overview of project progress
  - Progress bars for each stage
  - Charts by Lotto, System, and Stage
  - Stage status breakdown

- **Intersection List**: Searchable/filterable table of all intersections
  - Quick access to details
  - Jump to map location

- **Inconsistencies**: Track data discrepancies between sources
  - Radar count mismatches
  - Missing from main file
  - Missing from Lotto files

- **Tasks**: Kanban-style task management
  - Link tasks to intersections
  - Assign to team members or companies
  - Track status (Pending, In Progress, Completed)

- **Export**:
  - Export to Excel (full data)
  - Export to JSON
  - Generate Site Visit PDFs
  - Backup/Restore functionality

## Project Structure

```
radar-dashboard/
├── index.html              # Main dashboard
├── css/
│   └── styles.css          # Styling
├── js/
│   ├── app.js              # Main application logic
│   ├── data.js             # Data management
│   ├── map.js              # Leaflet map integration
│   ├── charts.js           # Chart.js visualizations
│   ├── tasks.js            # Task management
│   └── export.js           # Export functionality
├── data/
│   ├── intersections.json  # Merged intersection data
│   └── summary.json        # Summary statistics
├── data-import/            # Original Excel files
└── scripts/
    └── merge_data.py       # Data merge script
```

## Data Model

### Stages
1. **Installation**: Planimetry sent → Installed → Issues resolved
2. **Configuration**: Config done → Config installed on centralino
3. **Connection**: UTC table → Interface installed → Data received
4. **Validation**: Data correctness verified

### Systems
- **Omnia** (Swarco): Uses SPOT devices
- **Tmacs** (Semaforica): Uses AUT devices

### Lotti
- **M9.1**: Engin (ENG) + Sonet
- **M9.2**: Installation company TBD

## Updating Data

### Manual Updates
Changes made in the dashboard are saved to browser localStorage. Use the Export feature to create backups.

### Re-importing from Excel
1. Place updated Excel files in `data-import/`
2. Run the merge script:
   ```bash
   python scripts/merge_data.py
   ```
3. Refresh the dashboard (may need to clear localStorage for fresh data)

## Team Members
- GT - Giacomo Tuffanelli
- AV - Alessandro Vangi
- MC - Marisdea Castiglione
- FM - Francesco Masucci

## Companies
- ENG (Engin/Edison Next) - Lotto M9.1 installation
- Sonet - Lotto M9.1 installation
- Swarco - Omnia/SPOT system management
- Semaforica - Tmacs/AUT system management

## Technical Notes

- Data is stored in browser localStorage for persistence
- Map uses OpenStreetMap via Leaflet.js
- Charts powered by Chart.js
- Excel export via SheetJS
- PDF export via jsPDF

## Portability

To transfer to another computer:
1. Zip the entire `radar-dashboard` folder
2. Send via email/WeTransfer
3. Unzip and open `index.html`

Note: Data stored in localStorage is browser-specific. Use the Backup feature to transfer data state.
