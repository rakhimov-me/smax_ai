from flask import Flask, request, jsonify, render_template_string
import os
from datetime import datetime
from model_manager import ModelManager

app = Flask(__name__)
model_manager = ModelManager()

# HTML интерфейс
HTML_INTERFACE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SMAP AI - Классификация заявок</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            min-height: 100vh; 
            padding: 20px;
            color: #333;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: #2c3e50;
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .content {
            padding: 30px;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
        }
        @media (max-width: 768px) {
            .content {
                grid-template-columns: 1fr;
            }
        }
        .form-section, .data-section {
            background: #f8f9fa;
            padding: 25px;
            border-radius: 10px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: bold;
            color: #2c3e50;
        }
        input, textarea {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 16px;
            font-family: inherit;
        }
        textarea {
            height: 120px;
            resize: vertical;
        }
        input:focus, textarea:focus {
            outline: none;
            border-color: #3498db;
        }
        button {
            background: #3498db;
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
            transition: background 0.3s ease;
            margin: 5px;
        }
        button:hover {
            background: #2980b9;
        }
        .btn-danger {
            background: #e74c3c;
        }
        .btn-danger:hover {
            background: #c0392b;
        }
        .btn-success {
            background: #27ae60;
        }
        .btn-success:hover {
            background: #219a52;
        }
        .results {
            margin-top: 20px;
            padding: 20px;
            background: white;
            border-radius: 8px;
            border-left: 5px solid #3498db;
        }
        .result-item {
            margin: 10px 0;
            padding: 10px;
            background: #ecf0f1;
            border-radius: 5px;
        }
        .confidence {
            display: inline-block;
            padding: 3px 8px;
            background: #e74c3c;
            color: white;
            border-radius: 12px;
            font-size: 12px;
            margin-left: 10px;
        }
        .confidence.high { background: #27ae60; }
        .confidence.medium { background: #f39c12; }
        .data-list {
            max-height: 200px;
            overflow-y: auto;
            background: white;
            padding: 10px;
            border-radius: 5px;
            margin-top: 10px;
        }
        .data-item {
            padding: 5px;
            border-bottom: 1px solid #eee;
        }
        .admin-panel {
            grid-column: 1 / -1;
            background: #34495e;
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-top: 20px;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-bottom: 20px;
        }
        .stat-item {
            background: #2c3e50;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }
        .admin-buttons {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 SMAP AI</h1>
            <p>Автоматическая классификация заявок</p>
        </div>
        
        <div class="content">
            <!-- Левая колонка - форма -->
            <div class="form-section">
                <h3>🎯 Классификация заявки</h3>
                <div class="form-group">
                    <label for="title">Заголовок заявки:</label>
                    <input type="text" id="title" placeholder="Введите заголовок заявки...">
                </div>
                
                <div class="form-group">
                    <label for="description">Описание проблемы:</label>
                    <textarea id="description" placeholder="Подробно опишите проблему..."></textarea>
                </div>
                
                <button onclick="predict()">🎯 Классифицировать заявку</button>
                
                <div class="results" id="results" style="display: none;">
                    <h4>📊 Результаты:</h4>
                    <div id="predictionResults"></div>
                </div>
            </div>
            
            <!-- Правая колонка - данные -->
            <div class="data-section">
                <h3>📋 Загруженные данные</h3>
                
                <div class="form-group">
                    <label>Группы экспертов:</label>
                    <div class="data-list" id="groupsList">
                        <div class="data-item">Данные не загружены</div>
                    </div>
                </div>
                
                <div class="form-group">
                    <label>Эксперты (ФИО):</label>
                    <div class="data-list" id="expertsList">
                        <div class="data-item">Данные не загружены</div>
                    </div>
                </div>
                
                <div class="form-group">
                    <label>Метки заявок:</label>
                    <div class="data-list" id="labelsList">
                        <div class="data-item">Данные не загружены</div>
                    </div>
                </div>
                
                <button onclick="refreshData()">🔄 Обновить данные</button>
            </div>
            
            <!-- Админ панель -->
            <div class="admin-panel">
                <h3>⚙️ Управление моделью</h3>
                
                <div class="stats" id="stats">
                    <div class="stat-item">
                        <strong>Записей:</strong><br>
                        <span id="recordsCount">0</span>
                    </div>
                    <div class="stat-item">
                        <strong>Групп:</strong><br>
                        <span id="groupsCount">0</span>
                    </div>
                    <div class="stat-item">
                        <strong>Экспертов:</strong><br>
                        <span id="expertsCount">0</span>
                    </div>
                    <div class="stat-item">
                        <strong>Меток:</strong><br>
                        <span id="labelsCount">0</span>
                    </div>
                </div>
                
                <div class="admin-buttons">
                    <button class="btn-success" onclick="loadExcel()">📥 Загрузить данные из Excel</button>
                    <button onclick="getStats()">📊 Обновить статистику</button>
                    <button class="btn-danger" onclick="clearModel()">🧹 Очистить модель</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        async function predict() {
            const title = document.getElementById('title').value;
            const description = document.getElementById('description').value;
            
            if (!title) {
                alert('Введите заголовок заявки');
                return;
            }
            
            const response = await fetch('/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    title: title,
                    description: description
                })
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                const prediction = data.prediction;
                const resultsDiv = document.getElementById('predictionResults');
                
                // Проверка на спам
                if (prediction.is_spam) {
                    resultsDiv.innerHTML = `
                        <div style="color: #e74c3c; text-align: center; padding: 20px;">
                            <h3>🚫 ЗАПРОС ЗАБЛОКИРОВАН</h3>
                            <p><strong>Причина:</strong> ${prediction.spam_message || prediction.message}</p>
                            <p>Пожалуйста, опишите вашу проблему более конкретно.</p>
                        </div>
                    `;
                } else if (prediction.fallback) {
                    // Модель не обучена
                    resultsDiv.innerHTML = `
                        <div style="color: #f39c12; text-align: center; padding: 20px;">
                            <h3>⚠️ МОДЕЛЬ НЕ ОБУЧЕНА</h3>
                            <p>${prediction.message}</p>
                        </div>
                    `;
                } else {
                    // Нормальный результат
                    let confidenceClass = 'low';
                    if (prediction.confidence > 0.7) confidenceClass = 'high';
                    else if (prediction.confidence > 0.4) confidenceClass = 'medium';
                    
                    resultsDiv.innerHTML = `
                        <div class="result-item">
                            <strong>👥 Группа:</strong> ${prediction.group}
                            <span class="confidence ${confidenceClass}">${Math.round(prediction.confidence * 100)}%</span>
                        </div>
                        <div class="result-item">
                            <strong>👨‍💻 Эксперт:</strong> ${prediction.expert}
                            <span class="confidence ${confidenceClass}">${Math.round(prediction.expert_confidence * 100)}%</span>
                        </div>
                        <div class="result-item">
                            <strong>🏷️ Метка:</strong> ${prediction.label}
                            <span class="confidence ${confidenceClass}">${Math.round(prediction.label_confidence * 100)}%</span>
                        </div>
                    `;
                }
                
                document.getElementById('results').style.display = 'block';
            } else {
                alert('Ошибка: ' + data.error);
            }
        }
        
        async function loadExcel() {
            const response = await fetch('/load_excel');
            const data = await response.json();
            alert(data.message);
            refreshData();
            getStats();
        }
        
        async function saveModel() {
            const response = await fetch('/save_model');
            const data = await response.json();
            alert(data.message);
        }
        
        async function loadModel() {
            const response = await fetch('/load_model');
            const data = await response.json();
            alert(data.message);
            refreshData();
            getStats();
        }
        
        async function getStats() {
            const response = await fetch('/stats');
            const data = await response.json();
            
            document.getElementById('recordsCount').textContent = data.total_records;
            document.getElementById('groupsCount').textContent = data.groups_count;
            document.getElementById('expertsCount').textContent = data.experts_count;
            document.getElementById('labelsCount').textContent = data.labels_count;
        }
        
        async function refreshData() {
            const response = await fetch('/get_data');
            const data = await response.json();
            
            // Обновляем списки групп
            const groupsList = document.getElementById('groupsList');
            groupsList.innerHTML = data.groups.map(group => 
                `<div class="data-item">${group}</div>`
            ).join('') || '<div class="data-item">Нет данных</div>';
            
            // Обновляем списки экспертов
            const expertsList = document.getElementById('expertsList');
            expertsList.innerHTML = data.experts.map(expert => 
                `<div class="data-item">${expert}</div>`
            ).join('') || '<div class="data-item">Нет данных</div>';
            
            // Обновляем списки меток
            const labelsList = document.getElementById('labelsList');
            labelsList.innerHTML = data.labels.map(label => 
                `<div class="data-item">${label}</div>`
            ).join('') || '<div class="data-item">Нет данных</div>';
        }

        async function clearModel() {
            if (!confirm('⚠️ ВНИМАНИЕ! Это удалит все данные модели. Продолжить?')) {
                return;
            }
            
            const response = await fetch('/clear_model');
            const data = await response.json();
            alert(data.message);
            
            // Обновляем интерфейс после очистки
            refreshData();
            getStats();
            
            // Очищаем результаты предсказания
            document.getElementById('results').style.display = 'none';
            document.getElementById('title').value = '';
            document.getElementById('description').value = '';
        }
        
        // Загружаем данные при старте
        refreshData();
        getStats();
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return HTML_INTERFACE

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()
        
        if not data or 'title' not in data:
            return jsonify({"error": "Missing 'title' field"}), 400
            
        title = data['title']
        description = data.get('description', '')
        
        prediction = model_manager.predict(title, description)
        
        return jsonify({
            "prediction": prediction,
            "status": "success",
            "model_trained": model_manager.is_trained,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/load_excel', methods=['GET'])
def load_excel():
    """Загрузка данных из Excel файлов"""
    try:
        success = model_manager.load_and_train("Выгрузка")
        
        if success:
            model_manager.save_model()
            
            return jsonify({
                "status": "success",
                "message": "Данные успешно загружены и модель обучена",
                "records_loaded": model_manager.get_data_stats()["total_records"],
                "model_trained": model_manager.is_trained
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Не удалось загрузить данные из Excel файлов"
            }), 400
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/save_model', methods=['GET'])
def save_model():
    """Сохранение модели"""
    try:
        success = model_manager.save_model()
        return jsonify({
            "status": "success" if success else "error",
            "message": "Модель успешно сохранена" if success else "Ошибка сохранения модели"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/load_model', methods=['GET'])
def load_model():
    """Загрузка модели"""
    try:
        success = model_manager.load_model()
        return jsonify({
            "status": "success" if success else "error",
            "message": "Модель успешно загружена" if success else "Ошибка загрузки модели"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/stats', methods=['GET'])
def stats():
    """Статистика модели"""
    stats = model_manager.get_data_stats()
    return jsonify(stats)

@app.route('/get_data', methods=['GET'])
def get_data():
    """Получить списки групп, экспертов и меток"""
    return jsonify({
        "groups": model_manager.get_groups(),
        "experts": model_manager.get_experts(),
        "labels": model_manager.get_labels()
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "model_status": "trained" if model_manager.is_trained else "not_trained"
    })

@app.route('/clear_model', methods=['GET'])
def clear_model():
    """Очистка модели - удаление всех файлов"""
    try:
        success = model_manager.clear_model()
        return jsonify({
            "status": "success" if success else "error",
            "message": "Модель успешно очищена" if success else "Ошибка очистки модели"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    
    # Пытаемся загрузить сохраненную модель при старте
    if os.path.exists("model"):
        print("📂 Попытка загрузить сохраненную модель...")
        model_manager.load_model()
    
    print(f"🚀 Starting AI Server on port {port}...")
    print("📡 Endpoints:")
    print("   GET / - Веб-интерфейс")
    print("   POST /predict - Предсказание для заявки")
    print("   GET /load_excel - Загрузка данных из Excel")
    print("   GET /save_model - Сохранение модели")
    print("   GET /load_model - Загрузка модели")
    print("   GET /stats - Статистика")
    print("   GET /get_data - Списки групп и экспертов")
    
    app.run(host='0.0.0.0', port=port, debug=False)