import pandas as pd
import os
import glob
from datetime import datetime
import re

class DataLoader:
    def __init__(self):
        self.historical_data = []
        self.groups = set()
        self.experts = set()
        self.labels = set()
    
    def load_from_excel(self, folder_path="Выгрузка"):
        """Загрузка данных из всех xlsx файлов в папке"""
        try:
            excel_files = glob.glob(os.path.join(folder_path, "*.xlsx"))
            
            if not excel_files:
                print(f"❌ В папке '{folder_path}' не найдено xlsx файлов")
                return False
            
            all_data = []
            
            for file_path in excel_files:
                print(f"📖 Чтение файла: {os.path.basename(file_path)}")
                
                try:
                    # Читаем Excel, пропускаем пустые строки
                    df = pd.read_excel(file_path).dropna(how='all')
                    
                    if df.empty:
                        print(f"⚠️ Файл {os.path.basename(file_path)} пустой")
                        continue
                    
                    # Проверяем наличие нужных столбцов
                    required_columns = ['Заголовок', 'Назначенный эксперт Имя', 'Группа экспертов Имя']
                    missing_columns = [col for col in required_columns if col not in df.columns]
                    
                    if missing_columns:
                        print(f"⚠️ В файле {os.path.basename(file_path)} отсутствуют столбцы: {missing_columns}")
                        print(f"   Найдены столбцы: {list(df.columns)}")
                        continue
                    
                    for _, row in df.iterrows():
                        record = self._parse_excel_row(row, file_path)
                        if record:
                            all_data.append(record)
                            self.groups.add(record['group'])
                            self.experts.add(record['expert'])
                            self.labels.add(record['label'])
                            
                except Exception as e:
                    print(f"⚠️ Ошибка чтения {file_path}: {e}")
                    continue
            
            if all_data:
                self.historical_data.extend(all_data)
                print(f"✅ Загружено {len(all_data)} записей из {len(excel_files)} файлов")
                print(f"📊 Обнаружено: {len(self.groups)} групп, {len(self.experts)} экспертов, {len(self.labels)} меток")
                
                # Выводим примеры данных для проверки
                self.print_sample_data(5)
                
                return True
            else:
                print("❌ Не удалось загрузить данные из файлов")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка загрузки данных: {e}")
            return False
    
    def _parse_excel_row(self, row, file_path):
        """Парсинг строки Excel по фиксированным именам столбцов"""
        try:
            # Извлекаем данные по точным именам столбцов
            code = row['Код'] if 'Код' in row and pd.notna(row['Код']) else None
            close_time = row['Время закрытия'] if 'Время закрытия' in row and pd.notna(row['Время закрытия']) else None
            
            # Заголовок - обязательное поле
            if pd.isna(row['Заголовок']):
                return None
            title = str(row['Заголовок']).strip()
            
            # Эксперт - обязательное поле
            if pd.isna(row['Назначенный эксперт Имя']):
                return None
            expert = str(row['Назначенный эксперт Имя']).strip()
            
            # Проверяем что эксперт - это ФИО (содержит пробелы и кириллицу)
            if not self._is_valid_expert_name(expert):
                print(f"⚠️ Пропуск записи: некорректное имя эксперта '{expert}'")
                return None
            
            # Описание
            description = ""
            if 'Описание' in row and pd.notna(row['Описание']):
                description = str(row['Описание']).strip()
            
            # Группа - обязательное поле
            if pd.isna(row['Группа экспертов Имя']):
                return None
            group = str(row['Группа экспертов Имя']).strip()
            
            # Метка
            label = ""
            if 'Предложение Отображаемая метка' in row and pd.notna(row['Предложение Отображаемая метка']):
                label = str(row['Предложение Отображаемая метка']).strip()
            
            # URL
            url = ""
            if 'URL' in row and pd.notna(row['URL']):
                url = str(row['URL']).strip()
            
            # Пропускаем пустые заголовки
            if not title:
                return None
            
            # Объединяем заголовок и описание для обучения
            full_text = title
            if description:
                full_text = f"{title}. {description}"
            
            return {
                'code': code,
                'close_time': close_time,
                'title': title,
                'expert': expert,
                'description': description,
                'group': group,
                'label': label,
                'url': url,
                'full_text': full_text,
                'source_file': os.path.basename(file_path)
            }
            
        except Exception as e:
            print(f"⚠️ Ошибка парсинга строки: {e}")
            return None
    
    def _is_valid_expert_name(self, name):
        """Проверяем что имя эксперта похоже на ФИО"""
        # Должно содержать кириллические символы
        if not re.search(r'[а-яА-Я]', name):
            return False
        
        # Должно содержать пробелы (ФИО обычно имеет минимум 2 слова)
        if len(name.split()) < 2:
            return False
            
        return True
    
    def get_groups(self):
        """Получить список всех групп"""
        return sorted(list(self.groups))
    
    def get_experts(self):
        """Получить список всех экспертов"""
        return sorted(list(self.experts))
    
    def get_labels(self):
        """Получить список всех меток"""
        return sorted(list(self.labels))
    
    def get_stats(self):
        """Получить статистику данных"""
        return {
            "total_records": len(self.historical_data),
            "groups_count": len(self.groups),
            "experts_count": len(self.experts),
            "labels_count": len(self.labels)
        }
    
    def print_sample_data(self, count=5):
        """Вывести примеры данных для проверки"""
        if not self.historical_data:
            print("📭 Нет данных для отображения")
            return
        
        print(f"\n📋 Примеры первых {min(count, len(self.historical_data))} записей:")
        for i, record in enumerate(self.historical_data[:count]):
            print(f"\n{i+1}. Файл: {record['source_file']}")
            print(f"   📝 Заголовок: {record['title'][:80]}...")
            print(f"   👨‍💻 Эксперт: {record['expert']}")
            print(f"   👥 Группа: {record['group']}")
            print(f"   🏷️ Метка: {record['label'] if record['label'] else 'Не указана'}")
            if record['description']:
                print(f"   📄 Описание: {record['description'][:100]}...")