from flask import Flask, request, jsonify, render_template
import os
from datetime import datetime
from model_manager import ModelManager

app = Flask(__name__)
model_manager = ModelManager()

@app.route('/')
def home():
    return render_template('index.html')

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
    """Загрузка данных из Excel файлов (только новых)"""
    try:
        success = model_manager.load_and_train("Выгрузка")
        
        if success:
            model_manager.save_model()
            
            return jsonify({
                "status": "success",
                "message": "Данные успешно загружены и модель обучена",
                "records_loaded": model_manager.get_data_stats()["total_records"],
                "model_trained": model_manager.is_trained,
                "loaded_files_info": model_manager.data_loader.get_loaded_files_info()
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Не удалось загрузить данные из Excel файлов"
            }), 400
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/force_reload_excel', methods=['GET'])
def force_reload_excel():
    """Принудительная перезагрузка всех Excel файлов"""
    try:
        # Помечаем все файлы для перезагрузки
        model_manager.data_loader.force_reload_all("Выгрузка")
        
        success = model_manager.load_and_train("Выгрузка")
        
        if success:
            model_manager.save_model()
            
            return jsonify({
                "status": "success",
                "message": "Данные принудительно перезагружены и модель переобучена",
                "records_loaded": model_manager.get_data_stats()["total_records"],
                "model_trained": model_manager.is_trained,
                "loaded_files_info": model_manager.data_loader.get_loaded_files_info()
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Не удалось перезагрузить данные из Excel файлов"
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
    stats["loaded_files_info"] = model_manager.data_loader.get_loaded_files_info()
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
        "model_status": "trained" if model_manager.is_trained else "not_trained",
        "loaded_files_info": model_manager.data_loader.get_loaded_files_info()
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
    print("   GET /force_reload_excel - Принудительная перезагрузка всех Excel файлов")
    print("   GET /save_model - Сохранение модели")
    print("   GET /load_model - Загрузка модели")
    print("   GET /stats - Статистика")
    print("   GET /get_data - Списки групп и экспертов")
    
    app.run(host='0.0.0.0', port=port, debug=False)