import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
import joblib
import os
import glob
from data_loader import DataLoader
from spam_protector import SpamProtector  # Добавляем импорт

class ModelManager:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=1500, stop_words=['и', 'в', 'на', 'с', 'по', 'для', 'за', 'к'])
        self.group_encoder = LabelEncoder()
        self.expert_encoder = LabelEncoder()
        self.label_encoder = LabelEncoder()
        
        self.group_classifier = None
        self.expert_classifier = None
        self.label_classifier = None
        
        self.data_loader = DataLoader()
        self.spam_protector = SpamProtector()  # Добавляем спам-защиту
        self.is_trained = False
        
    def load_and_train(self, folder_path="Выгрузка"):
        """Загрузка данных и обучение модели"""
        # Загружаем данные
        success = self.data_loader.load_from_excel(folder_path)
        if not success:
            return False
        
        # Обучаем модель
        return self._train_model()
    
    def _train_model(self):
        """Обучение модели на загруженных данных"""
        if len(self.data_loader.historical_data) < 10:
            print("⚠️ Недостаточно данных для обучения")
            return False
            
        try:
            df = pd.DataFrame(self.data_loader.historical_data)
            
            # Векторизуем объединенный текст
            X = self.vectorizer.fit_transform(df['full_text'])
            
            # Обучаем кодировщики и классификаторы для групп
            groups_encoded = self.group_encoder.fit_transform(df['group'])
            self.group_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
            self.group_classifier.fit(X, groups_encoded)
            
            # Обучаем кодировщики и классификаторы для экспертов
            experts_encoded = self.expert_encoder.fit_transform(df['expert'])
            self.expert_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
            self.expert_classifier.fit(X, experts_encoded)
            
            # Обучаем кодировщики и классификаторы для меток
            labels_encoded = self.label_encoder.fit_transform(df['label'])
            self.label_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
            self.label_classifier.fit(X, labels_encoded)
            
            self.is_trained = True
            print(f"✅ Модель обучена на {len(df)} заявках")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка обучения модели: {e}")
            return False
    
    def predict(self, title, description):
        """Предсказание группы, эксперта и метки с проверкой на спам"""
        
        # 1. Проверка на спам перед предсказанием
        is_spam, spam_message = self.spam_protector.is_spam(title, description)
        if is_spam:
            return {
                "group": "СПАМ-ФИЛЬТР",
                "expert": "Система защиты",
                "label": "Заблокировано",
                "confidence": 0.0,
                "group_confidence": 0.0,
                "expert_confidence": 0.0,
                "label_confidence": 0.0,
                "is_spam": True,
                "spam_message": spam_message,
                "message": "Запрос заблокирован спам-фильтром"
            }
        
        # 2. Проверка, обучена ли модель
        if not self.is_trained:
            return self._fallback_prediction(title, description)
            
        try:
            full_text = f"{title}. {description}" if description else title
            X = self.vectorizer.transform([full_text])
            
            # Предсказываем группу
            group_encoded = self.group_classifier.predict(X)[0]
            group = self.group_encoder.inverse_transform([group_encoded])[0]
            group_confidence = np.max(self.group_classifier.predict_proba(X))
            
            # Предсказываем эксперта
            expert_encoded = self.expert_classifier.predict(X)[0]
            expert = self.expert_encoder.inverse_transform([expert_encoded])[0]
            expert_confidence = np.max(self.expert_classifier.predict_proba(X))
            
            # Предсказываем метку
            label_encoded = self.label_classifier.predict(X)[0]
            label = self.label_encoder.inverse_transform([label_encoded])[0]
            label_confidence = np.max(self.label_classifier.predict_proba(X))
            
            confidence = min(group_confidence, expert_confidence, label_confidence)
            
            return {
                "group": group,
                "expert": expert,
                "label": label,
                "confidence": round(confidence, 3),
                "group_confidence": round(group_confidence, 3),
                "expert_confidence": round(expert_confidence, 3),
                "label_confidence": round(label_confidence, 3),
                "is_spam": False
            }
        except Exception as e:
            print(f"❌ Ошибка предсказания: {e}")
            return self._fallback_prediction(title, description)
    
    def _fallback_prediction(self, title, description):
        """Резервное предсказание когда модель не обучена"""
        return {
            "group": "Общая группа поддержки",
            "expert": "Специалист первой линии",
            "label": "Стандартная заявка",
            "confidence": 0.1,
            "group_confidence": 0.1,
            "expert_confidence": 0.1,
            "label_confidence": 0.1,
            "fallback": True,
            "is_spam": False,
            "message": "Модель не обучена. Загрузите данные через /load_excel"
        }
    
    def save_model(self, folder_path="model"):
        """Сохранение модели и данных"""
        try:
            os.makedirs(folder_path, exist_ok=True)
            
            joblib.dump(self.vectorizer, os.path.join(folder_path, "vectorizer.joblib"))
            joblib.dump(self.group_encoder, os.path.join(folder_path, "group_encoder.joblib"))
            joblib.dump(self.expert_encoder, os.path.join(folder_path, "expert_encoder.joblib"))
            joblib.dump(self.label_encoder, os.path.join(folder_path, "label_encoder.joblib"))
            joblib.dump(self.group_classifier, os.path.join(folder_path, "group_classifier.joblib"))
            joblib.dump(self.expert_classifier, os.path.join(folder_path, "expert_classifier.joblib"))
            joblib.dump(self.label_classifier, os.path.join(folder_path, "label_classifier.joblib"))
            
            print(f"💾 Модель сохранена в папку {folder_path}")
            return True
        except Exception as e:
            print(f"❌ Ошибка сохранения модели: {e}")
            return False
    
    def load_model(self, folder_path="model"):
        """Загрузка модели"""
        try:
            self.vectorizer = joblib.load(os.path.join(folder_path, "vectorizer.joblib"))
            self.group_encoder = joblib.load(os.path.join(folder_path, "group_encoder.joblib"))
            self.expert_encoder = joblib.load(os.path.join(folder_path, "expert_encoder.joblib"))
            self.label_encoder = joblib.load(os.path.join(folder_path, "label_encoder.joblib"))
            self.group_classifier = joblib.load(os.path.join(folder_path, "group_classifier.joblib"))
            self.expert_classifier = joblib.load(os.path.join(folder_path, "expert_classifier.joblib"))
            self.label_classifier = joblib.load(os.path.join(folder_path, "label_classifier.joblib"))
            
            self.is_trained = True
            print(f"📂 Модель загружена из папки {folder_path}")
            return True
        except Exception as e:
            print(f"❌ Ошибка загрузки модели: {e}")
            return False

    def clear_model(self, folder_path="model"):
        """Очистка модели - удаление всех файлов"""
        try:
            if not os.path.exists(folder_path):
                print(f"📭 Папка {folder_path} не существует")
                return True
                
            # Удаляем все файлы в папке модели
            files = glob.glob(os.path.join(folder_path, "*"))
            for file in files:
                try:
                    os.remove(file)
                    print(f"🗑️ Удален файл: {os.path.basename(file)}")
                except Exception as e:
                    print(f"⚠️ Не удалось удалить файл {file}: {e}")
            
            # Сбрасываем состояние модели
            self.vectorizer = TfidfVectorizer(max_features=1500, stop_words=['и', 'в', 'на', 'с', 'по', 'для', 'за', 'к'])
            self.group_encoder = LabelEncoder()
            self.expert_encoder = LabelEncoder()
            self.label_encoder = LabelEncoder()
            
            self.group_classifier = None
            self.expert_classifier = None
            self.label_classifier = None
            
            # Очищаем данные
            self.data_loader.historical_data = []
            self.data_loader.groups = set()
            self.data_loader.experts = set()
            self.data_loader.labels = set()
            
            self.is_trained = False
            
            print(f"🧹 Модель полностью очищена. Удалено {len(files)} файлов.")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка очистки модели: {e}")
            return False
    
    def get_data_stats(self):
        """Получить статистику данных"""
        return self.data_loader.get_stats()
    
    def get_groups(self):
        """Получить список всех групп"""
        return self.data_loader.get_groups()
    
    def get_experts(self):
        """Получить список всех экспертов"""
        return self.data_loader.get_experts()
    
    def get_labels(self):
        """Получить список всех меток"""
        return self.data_loader.get_labels()
    
    def get_model_info(self):
        """Получить информацию о модели"""
        if not self.is_trained:
            return {
                "is_trained": False,
                "message": "Модель не обучена"
            }
        
        return {
            "is_trained": True,
            "groups_count": len(self.group_encoder.classes_),
            "experts_count": len(self.expert_encoder.classes_),
            "labels_count": len(self.label_encoder.classes_),
            "groups": self.group_encoder.classes_.tolist(),
            "experts": self.expert_encoder.classes_.tolist(),
            "labels": self.label_encoder.classes_.tolist()
        }