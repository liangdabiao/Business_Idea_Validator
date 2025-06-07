from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import csv
import json
from functions import  generate_doc_description, do_review,get_json_content
from test_xhs import csv_analysis

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB限制

@app.route('/')
def index():
    return render_template('index_reddit.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': '未选择文件'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '空文件名'}), 400

    if not file.filename.endswith('.csv'):
        return jsonify({'error': '仅支持CSV文件'}), 400
        
    # 检查CSV行数不超过100条
    file.seek(0)
    line_count = sum(1 for _ in csv.reader(file.read().decode('utf-8').splitlines()))
    if line_count > 400:
        return jsonify({'error': 'CSV文件数据不能超过30条'}), 200
    file.seek(0)

    # 保存原始文件
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(input_path)

    final_report, pain_points_word_frequency, excitement_signals_word_frequency, notable_quotes_word_frequency, red_flags_word_frequency = csv_analysis(input_path)
    

    return jsonify({ 
        'final_report': final_report,
        'pain_points_word_frequency': pain_points_word_frequency,
        'excitement_signals_word_frequency': excitement_signals_word_frequency,
        'notable_quotes_word_frequency': notable_quotes_word_frequency,
        'red_flags_word_frequency': red_flags_word_frequency, 
    })

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)