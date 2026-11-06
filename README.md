# Практическая работа №2. Вариант 30

Инструмент анализа зависимостей пакетов Ubuntu APT. Этап 1: загрузка
плоской YAML-конфигурации, проверка пяти параметров и вывод ключ=значение.

Требуется Python 3.10+. Сборка и дополнительные модули не требуются.
Запуск: `run.bat` (Windows) или `sh run.sh` (Linux/macOS).
Параметр `--config PATH` выбирает YAML вместо `config.yaml`.

`package` задаёт имя, `repository` - URL или путь к тестовому файлу,
`test_mode` - режим тестирования, `version` - версию в кавычках,
`max_depth` - глубину 0..256. Ошибка параметра выводится в stderr.

Проверки в PowerShell:

```powershell
$env:PYTHONPATH = 'src'
py -3 -m unittest discover -s tests -v
```

В Linux/macOS: `PYTHONPATH=src python3 -m unittest discover -s tests -v`.

Этап 2: `run.bat --config examples/ubuntu/hello.yaml` загружает
официальный индекс Ubuntu 24.04 noble, main, amd64 и печатает прямые
обязательные связи именно версии 2.10-3build1. `--mode config` показывает
параметры первого этапа. Можно указать прямой URL Packages, .xz, .gz, .bz2.

Этап 3: `--mode graph` показывает граф, построенный рекурсивным DFS.
`run.bat` показывает ромб A/B/C/D; `--config examples/cycle.yaml` - цикл;
`--config examples/shallow.yaml` ограничивает глубину одной связью;
`--config examples/isolated.yaml` оставляет одну вершину. Тестовый JSON
содержит объект «пакет → версия → список зависимостей»; имена A..Z.
