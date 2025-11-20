import re

class SpamProtector:
    def __init__(self):
        self.gibberish_patterns = [
            r'[a-z]{20,}',  # ОЧЕНЬ длинные последовательности латиницы
            r'[0-9]{20,}',  # ОЧЕНЬ длинные последовательности цифр
            r'[!@#$%^&*()_+\-={}\[\]|:;"<>,.?/~`]{10,}',  # Много спецсимволов
            r'(.)\1{10,}',  # Повторяющиеся символы (aaaaaaaaaaa)
        ]
    
    def is_spam(self, title, description):
        """Упрощенная проверка на бред"""
        full_text = f"{title}. {description}" if description else title
        full_text = full_text.strip()
        
        # 1. Проверка на слишком короткий текст
        if len(full_text) < 5:
            return True, "Слишком короткий запрос. Минимум 5 символов."
        
        # 2. Проверка на слишком длинный текст
        if len(full_text) > 2000:
            return True, "Слишком длинный запрос. Максимум 2000 символов."
        
        # 3. Проверка на явный бред
        if self._is_gibberish(full_text):
            return True, "Текст похож на бессмыслицу"
        
        return False, "OK"
    
    def _is_gibberish(self, text):
        """Проверяем, является ли текст явным бредом"""
        text_lower = text.lower()
        
        # Проверяем только самые явные паттерны бессмыслицы
        for pattern in self.gibberish_patterns:
            if re.search(pattern, text_lower):
                return True
        
        return False