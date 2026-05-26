"""
ASGARD Alliance Dashboard - Flask Backend
Handles file uploads, data processing, and provides analytics API
"""

from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import os
import tempfile
from datetime import datetime
import pandas as pd
import json
from data_processor import DataProcessor
import traceback

app = Flask(__name__)
CORS(app)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
UPLOAD_FOLDER = tempfile.gettempdir()
ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}

# Global state for the current processed data
current_data = {
    'common_sheet': None,
    'week_sheets': {},
    'analytics': {},
    'raw_sheets': {},
    'errors': [],
    'upload_time': None
}

def allowed_file(filename):
    """Check if file has allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """Serve the dashboard HTML"""
    return render_template('dashboard.html')


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file upload and process data"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed. Use .xlsx, .xls, or .csv'}), 400
        
        # Save file temporarily
        temp_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(temp_path)
        
        # Process the file
        processor = DataProcessor()
        result = processor.process_excel_file(temp_path)
        
        # Store in global state
        current_data['common_sheet'] = result.common_sheet
        current_data['week_sheets'] = result.week_sheets
        current_data['analytics'] = result.analytics
        current_data['raw_sheets'] = result.raw_sheets
        current_data['errors'] = result.errors
        current_data['upload_time'] = datetime.now().isoformat()
        
        # Clean up temp file
        try:
            os.remove(temp_path)
        except:
            pass
        
        # Return success with basic info
        return jsonify({
            'success': True,
            'message': 'File processed successfully',
            'data_summary': {
                'total_members': len(result.common_sheet),
                'total_sheets': len(result.raw_sheets),
                'errors': result.errors,
                'upload_time': current_data['upload_time']
            }
        }), 200
    
    except Exception as e:
        return jsonify({'error': f'Processing error: {str(e)}'}), 500


@app.route('/api/data/common-sheet', methods=['GET'])
def get_common_sheet():
    """Get the unified common sheet"""
    try:
        if current_data['common_sheet'] is None or len(current_data['common_sheet']) == 0:
            return jsonify({'error': 'No data loaded'}), 404
        
        # Apply filters if provided
        df = current_data['common_sheet'].copy()
        
        # Member search filter
        member = request.args.get('member', '').lower()
        if member:
            df = df[df['Member'].astype(str).str.lower().str.contains(member)]
        
        # Pagination
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        start = (page - 1) * per_page
        end = start + per_page
        
        # Convert to JSON-friendly format
        df_page = df.iloc[start:end].fillna(0)
        
        return jsonify({
            'success': True,
            'data': df_page.to_dict('records'),
            'total': len(df),
            'page': page,
            'per_page': per_page,
            'total_pages': (len(df) + per_page - 1) // per_page
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/data/bottom-20', methods=['GET'])
def get_bottom_20():
    """Get bottom 20 performers"""
    try:
        if not current_data['analytics'] or 'bottom_20' not in current_data['analytics']:
            return jsonify({'error': 'Analytics not available'}), 404
        
        bottom_20 = current_data['analytics']['bottom_20']
        
        return jsonify({
            'success': True,
            'data': bottom_20,
            'count': len(bottom_20)
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/data/analytics', methods=['GET'])
def get_analytics():
    """Get all analytics"""
    try:
        if not current_data['analytics']:
            return jsonify({'error': 'Analytics not available'}), 404
        
        analytics = current_data['analytics'].copy()
        
        # Remove list data for summary endpoint
        summary = {
            'total_members': analytics.get('total_members', 0),
            'total_duel': analytics.get('total_duel', 0),
            'total_tech': analytics.get('total_tech', 0),
            'total_cp_growth': analytics.get('total_cp_growth', 0)
        }
        
        return jsonify({
            'success': True,
            'summary': summary,
            'bottom_20_count': len(analytics.get('bottom_20', [])),
            'top_performers': {
                'duel_count': len(analytics.get('top_duel', [])),
                'tech_count': len(analytics.get('top_tech', [])),
                'cp_count': len(analytics.get('top_cp_growth', []))
            },
            'lowest_performers': {
                'duel_count': len(analytics.get('lowest_duel', [])),
                'tech_count': len(analytics.get('lowest_tech', [])),
                'cp_count': len(analytics.get('least_active_cp', []))
            }
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/data/top-performers', methods=['GET'])
def get_top_performers():
    """Get top performers"""
    try:
        metric = request.args.get('metric', 'duel').lower()
        
        if not current_data['analytics']:
            return jsonify({'error': 'Analytics not available'}), 404
        
        analytics = current_data['analytics']
        
        metric_map = {
            'duel': 'top_duel',
            'tech': 'top_tech',
            'cp': 'top_cp_growth'
        }
        
        key = metric_map.get(metric, 'top_duel')
        data = analytics.get(key, [])
        
        return jsonify({
            'success': True,
            'metric': metric,
            'data': data
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/data/lowest-performers', methods=['GET'])
def get_lowest_performers():
    """Get lowest performers"""
    try:
        metric = request.args.get('metric', 'duel').lower()
        
        if not current_data['analytics']:
            return jsonify({'error': 'Analytics not available'}), 404
        
        analytics = current_data['analytics']
        
        metric_map = {
            'duel': 'lowest_duel',
            'tech': 'lowest_tech',
            'cp': 'least_active_cp'
        }
        
        key = metric_map.get(metric, 'lowest_duel')
        data = analytics.get(key, [])
        
        return jsonify({
            'success': True,
            'metric': metric,
            'data': data
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/data/export-common-sheet', methods=['GET'])
def export_common_sheet():
    """Export common sheet as Excel"""
    try:
        if current_data['common_sheet'] is None or len(current_data['common_sheet']) == 0:
            return jsonify({'error': 'No data to export'}), 404
        
        # Create Excel file
        output = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        with pd.ExcelWriter(output.name, engine='openpyxl') as writer:
            current_data['common_sheet'].to_excel(writer, sheet_name='Common Sheet', index=False)
        
        output.seek(0)
        return send_file(
            output.name,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='common_sheet.xlsx'
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/data/export-bottom-20', methods=['GET'])
def export_bottom_20():
    """Export bottom 20 as Excel"""
    try:
        if not current_data['analytics'] or 'bottom_20' not in current_data['analytics']:
            return jsonify({'error': 'No data to export'}), 404
        
        bottom_20 = current_data['analytics']['bottom_20']
        df = pd.DataFrame(bottom_20)
        
        # Create Excel file
        output = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        with pd.ExcelWriter(output.name, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Bottom 20', index=False)
        
        output.seek(0)
        return send_file(
            output.name,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='bottom_20.xlsx'
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/status', methods=['GET'])
def get_status():
    """Get current dashboard status"""
    return jsonify({
        'data_loaded': current_data['common_sheet'] is not None and len(current_data['common_sheet']) > 0,
        'upload_time': current_data['upload_time'],
        'total_members': len(current_data['common_sheet']) if current_data['common_sheet'] is not None else 0,
        'errors': current_data['errors']
    }), 200


@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    # Create templates folder if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)

    # Run the Flask app using environment variables for deployment platforms
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() in ('1', 'true', 'yes')
    app.run(debug=debug, host='0.0.0.0', port=port)
