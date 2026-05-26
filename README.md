# ASGARD Alliance Dashboard

A modern, production-ready dashboard system for processing and analyzing alliance performance data from Excel spreadsheets.

## Features

✨ **Comprehensive Analytics**
- Unified member data consolidation from multiple Excel sheets
- Dynamic week-wise data processing
- Combined performance metrics (Duel, Tech, CP Growth)
- Bottom 20 performers analysis
- Top performers ranking by metric

📊 **Interactive Dashboard**
- Modern, responsive web interface
- File upload and automatic processing
- Real-time data visualization with Chart.js
- Advanced filtering and search
- Member-wise detailed analytics
- Export to Excel

⚙️ **Backend Processing**
- Modular data processor with robust error handling
- Automatic detection of week sections
- Intelligent column mapping
- Data normalization and aggregation
- RESTful API endpoints

## Project Structure

```
d:\yosker\ASGARD\
├── data_processor.py       # Core data processing engine
├── flask_app.py            # Flask backend application
├── templates/
│   └── dashboard.html      # Interactive dashboard UI
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Installation

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Setup

1. **Clone or download the project**
   ```powershell
   cd d:\yosker\ASGARD
   ```

2. **Create a virtual environment (recommended)**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate
   ```

3. **Install dependencies**
   ```powershell
   pip install -r requirements.txt
   ```

## Usage

### Running the Dashboard

1. **Start the Flask application**
   ```powershell
   python flask_app.py
   ```

2. **Open your browser and navigate to**
   ```
   http://localhost:5000
   ```

3. **Upload your Excel file**
   - Click on the file input field
   - Select your `.xlsx` or `.xls` file
   - Click "Upload & Process"
   - Wait for processing to complete

4. **Explore the data**
   - View unified member data in "Common Sheet"
   - Analyze bottom 20 performers
   - Compare top performers across metrics
   - Export processed data to Excel

### Excel File Format Requirements

Your Excel file should contain these sheets:

1. **Alliance duel**
   - Repeated member data for each week
   - Pattern: Members, Duel Score, Daily Avg, Tiers (repeated for each week)
   - Example: Members, Duel Week 1, daily average, Tiers, Members 2, Duel Week 2, ...

2. **Tech**
   - Similar structure to Alliance duel
   - Contains tech contribution values
   - Pattern: Members, Tech Week 1, daily average, Tiers (repeated for each week)

3. **CP check**
   - Member names and CP growth values
   - Columns: Members, CP dates, 23 days growth, Tier

4. **Kicking list**
   - Member status information
   - Not processed by default (reserved for future analysis)

## API Endpoints

### File Upload
- **POST** `/api/upload` - Upload and process Excel file

### Data Retrieval
- **GET** `/api/data/common-sheet` - Get unified member data
- **GET** `/api/data/bottom-20` - Get bottom 20 performers
- **GET** `/api/data/analytics` - Get summary analytics
- **GET** `/api/data/top-performers?metric=duel` - Get top performers (duel/tech/cp)
- **GET** `/api/data/lowest-performers?metric=duel` - Get lowest performers

### Export
- **GET** `/api/data/export-common-sheet` - Download common sheet as Excel
- **GET** `/api/data/export-bottom-20` - Download bottom 20 as Excel

### Status
- **GET** `/api/status` - Get dashboard status

## Data Processing Flow

```
Excel File
    ↓
[Read Raw Sheets]
    ↓
┌─────────────────────────────────┐
│ Process Each Sheet:             │
├─────────────────────────────────┤
│ 1. Alliance Duel                │
│    - Detect week sections       │
│    - Extract member data        │
│    - Calculate totals           │
│                                 │
│ 2. Tech                         │
│    - Detect week sections       │
│    - Extract tech values        │
│    - Calculate totals           │
│                                 │
│ 3. CP Check                     │
│    - Extract CP growth values   │
│    - Extract tier information   │
└─────────────────────────────────┘
    ↓
[Merge All Sheets]
    - One row per member
    - Combine all metrics
    ↓
[Generate Analytics]
    - Calculate totals
    - Identify bottom 20
    - Rank by metric
    ↓
[Common Sheet + Analytics]
```

## Data Processor Features

### Dynamic Week Detection
The processor automatically detects the number of weeks in each sheet by looking for patterns like:
- "Members", "Members 2", "Members 3", "Members 4"
- "Duel Week 1", "Duel Week 2", etc.
- Date patterns like "May 04th - May 10"

### Intelligent Column Mapping
- Automatically identifies member columns
- Finds score columns (Duel, Tech, CP)
- Extracts daily averages
- Captures tier information

### Data Normalization
- Handles missing values
- Converts numeric strings to floats
- Processes percentages and formatted numbers
- Aggregates duplicate member entries

## Configuration

### File Upload Limits
- Default: 50MB max file size
- Configurable in `flask_app.py` via `MAX_CONTENT_LENGTH`

### Performance Tuning
- Pagination: 50 members per page (configurable)
- Default sorting: By combined score (Duel×1000 + Tech×1 + CP×100)

## Troubleshooting

### File Not Processing
**Issue**: "No week sections detected"
- **Solution**: Verify your Excel file has the correct sheet names: "Alliance duel", "Tech", "CP check"

### Column Not Detected
**Issue**: Data appears as NaN or missing
- **Solution**: Check that column names contain expected keywords (Members, Duel, Tech, etc.)

### Port Already in Use
**Issue**: `Address already in use`
- **Solution**: Change port in `flask_app.py`: 
  ```python
  app.run(debug=True, host='127.0.0.1', port=5001)
  ```

### Import Errors
**Issue**: `ModuleNotFoundError`
- **Solution**: Ensure virtual environment is activated and requirements are installed
  ```powershell
  pip install -r requirements.txt
  ```

## Development

### Adding New Metrics
1. Add calculation in `data_processor.py` → `generate_analytics()`
2. Add API endpoint in `flask_app.py`
3. Add visualization in `dashboard.html`

### Modifying Sheet Processing
Edit `data_processor.py`:
- `process_alliance_duel_sheet()` - Duel processing logic
- `process_tech_sheet()` - Tech processing logic
- `process_cp_sheet()` - CP processing logic
- `_detect_week_sections()` - Week detection logic

## Performance Considerations

- **Large Files**: For files with >1000 members, processing may take 10-15 seconds
- **Browser**: Recommended: Chrome/Edge/Firefox (latest versions)
- **Memory**: Minimum 2GB RAM recommended

## Future Enhancements

- [ ] Kicking List analysis and integration
- [ ] Member activity timeline
- [ ] Automated alerts for underperformers
- [ ] Historical trend analysis
- [ ] Custom scoring weights
- [ ] Role-based access control
- [ ] Data caching and persistence
- [ ] Mobile app version

## License

Internal Use Only - ASGARD Alliance

## Support

For issues or questions, contact the development team.

---

**Version**: 1.0  
**Last Updated**: May 2026
