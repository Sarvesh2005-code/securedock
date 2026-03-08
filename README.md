# SecureDock: Digital Forensic Chat Recovery Tool

SecureDock is a professional desktop-based Digital Forensic Recovery Software designed for cybersecurity and forensic investigation purposes. It focuses on the recovery and analysis of deleted chat messages and SMS records from extracted mobile device backups (Android and iOS).

## Disclaimer
This tool is strictly for forensic, academic, and authorized investigation use only. It does not bypass encryption, hack accounts, or perform unauthorized access. The system analyzes legally acquired SQLite database files, backup files, or disk images.

## Features
*   **Android Analysis:** Parse `mmssms.db` and Google Messages `bugle_db`.
*   **iOS Analysis:** Parse `sms.db`.
*   **Data Carving:** Detect and recover deleted text message artifacts directly from SQLite free pages, WAL files, and unallocated blocks.
*   **Forensic Hash Tracking:** Deterministic SHA-256 evidence hashing and chain-of-custody log generation.
*   **Report Generation:** Export cases to professional PDF summaries or CSV dumps.
*   **Cross Platform Evidence:** Handles timestamp normalization for Unix Epoch, iOS Mac Absolute Time, and Android Java Time automatically.
*   **GUI:** Professional, modern desktop interface with message details viewer, forensic filtering, and statistics dashboards.

## Installation

### Method 1: Download Standalone Executable (Windows)
1. Navigate to the **[Releases](https://github.com/Sarvesh2005-code/securedock/releases)** page on this GitHub repository.
2. Under the **Latest Release**, download the `SecureDock.exe` file attached in the Assets section.
3. Once downloaded, double-click the `.exe` file to launch the application. No installation or Python environment is required!

### Method 2: Run from Source
1. Clone this repository.
2. Install Python 3.9+.
3. Create a virtual environment: `python -m venv venv`
4. Activate the virtual environment:
   * Windows: `venv\Scripts\activate`
   * Mac/Linux: `source venv/bin/activate`
5. Install dependencies: `pip install -r requirements.txt` (Note: requires `PyQt6` and `reportlab`).
6. Run the application: `python main.py`

## Usage
1. Click **"Load Database File"**.
2. Select an extracted SQLite database (e.g., `sms.db`, `mmssms.db`, or `bugle_db`).
3. The system will automatically compute its SHA-256 hash, parse allocated records, and carve deleted blocks.
4. Use the keyword search box and date filters to narrow down the artifacts.
5. Click a row to view the full message body, timestamps, and deep metadata in the Viewer pane.
6. Export the selected dataset to PDF or CSV for formal case documentation.

## Development & Compiling
To compile the application yourself into a standalone executable:
```bash
pip install pyinstaller
pyinstaller --name "SecureDock" --windowed --onefile main.py
```
The executable will be located in the `dist/` folder.
