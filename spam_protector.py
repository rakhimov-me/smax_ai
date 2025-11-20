import re

class SpamProtector:
    def __init__(self):
        self.gibberish_patterns = [
            r'[a-z]{10,}',  # длинные последовательности латиницы
            r'[0-9]{10,}',  # длинные последовательности цифр
            r'[!@#$%^&*()_+\-={}\[\]|:;"<>,.?/~`]{5,}',  # много спецсимволов
            r'(.)\1{5,}',  # повторяющиеся символы (aaaaaa)
            r'[а-яё]\s*[а-яё]\s*[а-яё]\s*[а-яё]\s*[а-яё]',  # одиночные буквы через пробелы
        ]
        
        # Минимальный набор русских слов для осмысленного запроса
        self.russian_common_words = [
            'не', 'на', 'в', 'с', 'по', 'за', 'к', 'у', 'о', 'из', 'от', 'до', 
            'для', 'при', 'под', 'над', 'перед', 'после', 'без', 'про', 'через',
            'работа', 'систем', 'ошибк', 'проблем', 'помощ', 'вопрос', 'служб',
            'техническ', 'поддержк', 'информац', 'данн', 'файл', 'программ',
            'компьютер', 'сервер', 'сеть', 'интернет', 'телефон', 'почт', 'документ',
            'устройств', 'настройк', 'установк', 'заявк', 'обращен', 'помощ'
        ]
    
    def is_spam(self, title, description):
        """Строгая проверка на бред с акцентом на русский язык"""
        full_text = f"{title}. {description}" if description else title
        full_text = full_text.strip()
        
        # 1. Проверка на слишком короткий текст
        if len(full_text) < 10:
            return True, "Слишком короткий запрос. Минимум 10 символов."
        
        # 2. Проверка на слишком длинный текст
        if len(full_text) > 1000:
            return True, "Слишком длинный запрос. Максимум 1000 символов."
        
        # 3. СТРОГАЯ проверка на русский язык
        russian_check = self._strict_russian_check(full_text)
        if not russian_check[0]:
            return True, russian_check[1]
        
        # 4. Проверка на бред
        if self._is_gibberish(full_text):
            return True, "Текст похож на бессмыслицу или автоматическую генерацию"
        
        # 5. Проверка на осмысленность (наличие обычных русских слов)
        if not self._has_meaningful_russian(full_text):
            return True, "Запрос не содержит осмысленных русских слов"
        
        return False, "OK"
    
    def _strict_russian_check(self, text):
        """Строгая проверка на русский язык"""
        text_lower = text.lower()
        
        # Подсчет символов
        cyrillic_chars = len(re.findall(r'[а-яё]', text_lower))
        latin_chars = len(re.findall(r'[a-z]', text_lower))
        digit_chars = len(re.findall(r'[0-9]', text_lower))
        special_chars = len(re.findall(r'[!@#$%^&*()_+\-={}\[\]|:;"<>,.?/~`]', text_lower))
        total_chars = len(text_lower)
        
        if total_chars == 0:
            return False, "Пустой запрос"
        
        # Должно быть не менее 60% кириллицы
        cyrillic_ratio = cyrillic_chars / total_chars
        if cyrillic_ratio < 0.6:
            return False, f"Слишком мало русского текста ({cyrillic_ratio*100:.0f}%). Минимум 60%."
        
        # Не более 20% латиницы
        latin_ratio = latin_chars / total_chars
        if latin_ratio > 0.2:
            return False, f"Слишком много латинских символов ({latin_ratio*100:.0f}%). Максимум 20%."
        
        # Не более 10% цифр
        digit_ratio = digit_chars / total_chars
        if digit_ratio > 0.1:
            return False, f"Слишком много цифр ({digit_ratio*100:.0f}%). Максимум 10%."
        
        # Не более 5% спецсимволов
        special_ratio = special_chars / total_chars
        if special_ratio > 0.05:
            return False, f"Слишком много специальных символов ({special_ratio*100:.0f}%). Максимум 5%."
        
        return True, "OK"
    
    def _is_gibberish(self, text):
        """Проверяем, является ли текст бредом"""
        text_lower = text.lower()
        
        # Проверяем паттерны бессмыслицы
        for pattern in self.gibberish_patterns:
            if re.search(pattern, text_lower):
                return True
        
        # Проверка на случайный набор букв (как в примере "щзфАФЬВЛЖАЖЙЬЫЖВ")
        if self._is_random_letters(text):
            return True
        
        return False
    
    def _is_random_letters(self, text):
        """Проверка на случайный набор букв без пробелов"""
        # Если текст длинный и нет пробелов - подозрительно
        if len(text) > 15 and ' ' not in text:
            # Проверяем, что это не одно слово, а случайный набор
            russian_letters = re.findall(r'[а-яё]', text.lower())
            if len(russian_letters) > 10:
                # Если много русских букв подряд без пробелов - вероятно бред
                return True
        return False
    
    def _has_meaningful_russian(self, text):
        """Проверяем наличие осмысленных русских слов"""
        text_lower = text.lower()
        meaningful_count = 0
        
        for word in self.russian_common_words:
            if word in text_lower:
                meaningful_count += 1
        
        # Должно быть хотя бы 2 осмысленных слова
        return meaningful_count >= 2