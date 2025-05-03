# Request2Ffuf
The tool for transfer request file (from BurpSuite 4 exmple) to Ffuf comandline. Created with ChatGPT help.

# 🦊 http-to-ffuf

Утилита на Python для генерации команд `ffuf` из сырых HTTP-запросов (например, экспортированных из Burp Suite).  
Позволяет удобно фаззить параметры, заголовки, использовать множественные словари и настраивать фильтры.

---

## 🚀 Возможности

- ✅ Поддержка **GET и POST** запросов
- ✅ Поддержка автоматической пометки параметров для фаззинга путем добавления символов $ в запросе (как в интрудере) 
- ✅ Парсинг сырых запросов из BurpSuite
- ✅ Фаззинг **любых параметров или заголовков**
- ✅ **Множественные слоты** (`FUZZ`, `FUZZ1`, `FUZZ2`, ...)
- ✅ **Несколько словарей** (`-w`, `-w1`, `-w2`, ...)
- ✅ Автоматическая генерация флагов `-H`, `-d`, `-X POST`, и т.д.
- ✅ Поддержка фильтров: `--mc`, `--fs`, `--fc`

---

## 🛠 Установка

```bash
git clone https://github.com/yourusername/http-to-ffuf.git
cd http-to-ffuf
python3 -m venv venv
source venv/bin/activate
```

Никаких зависимостей не требуется — используется стандартная библиотека Python.

---

## 📄 Пример использования

### 1. Сохраните HTTP-запрос из Burp в файл:

Пример файла `login.txt`:

```
POST /login HTTP/1.1
Host: example.com
User-Agent: Mozilla/5.0
Content-Type: application/x-www-form-urlencoded

username=admin&password=admin
```

---

### 2. Запуск генерации команды `ffuf`

```bash
python http_to_ffuf.py login.txt \
  -f param:username=FUZZ1,param:password=FUZZ2 \
  -w1 users.txt -w2 passwords.txt \
  --mc 200 --fs 0
```

**Результат:**

```bash
ffuf -X POST -u "http://example.com/login" -d 'username=FUZZ1&password=FUZZ2' \
-w users.txt:FUZZ1 -w passwords.txt:FUZZ2 \
-H "User-Agent: Mozilla/5.0" -mc 200 -fs 0
```

---

## 🔧 Аргументы

| Аргумент               | Описание |
|------------------------|----------|
| `file`                 | Путь к файлу с HTTP-запросом |
| `-f / --fuzz`          | Что фаззить: `param:name=FUZZ`, `header:Header=FUZZ1` |
| `-w`                   | Словарь по умолчанию (для `FUZZ`) |
| `-w1`, `-w2`, ...      | Словари для `FUZZ1`, `FUZZ2`, и т.д. |
| `--mc`, `--fc`, `--fs` | Фильтрация/поиск по статусам и размеру ответа |

---

## 💡 Примеры

### Фаззинг параметров GET-запроса

```bash
-f param:search=FUZZ
```

### Фаззинг заголовков (например, Authorization)

```bash
-f header:Authorization=FUZZ
```

### Смешанный фаззинг

```bash
-f param:user=FUZZ1,param:pass=FUZZ2,header:X-Api-Key=FUZZ3
```


---

## ⚠️ Примечания

- Скрипт не выполняет фаззинг сам — он **только генерирует** удобную команду `ffuf`.
- Убедитесь, что `ffuf` установлен на вашей системе: https://github.com/ffuf/ffuf

---

## 🧪 Совместимость

- Python 3.6+
- Кроссплатформенный (Linux, macOS, Windows)

---

## 📜 Лицензия

MIT — свободное использование, модификация и распространение.

---

## 🧠 Автор

Разработано с целью автоматизации фаззинга на основе Burp-запросов.

Pull requests и предложения приветствуются!
