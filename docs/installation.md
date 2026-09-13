# Установка

## Требования

Проверенная V1 закрепляет следующие версии:

- Python 3.12.11;
- uv 0.12.x;
- Pandoc 3.11.

Версия Pandoc проверяется при каждой сборке DOCX. Несовместимая версия
останавливает сборку с кодом 2.

## macOS

Установите uv и Pandoc удобным для системы способом. Homebrew можно использовать
как источник внешних программ:

```sh
brew install uv pandoc
```

После установки убедитесь, что `pandoc --version` показывает 3.11. Если менеджер
пакетов уже предлагает другую основную версию, используйте Docker либо
установите закреплённую версию вручную.

Разверните Python-окружение из корня репозитория:

```sh
uv sync
uv run tex2sto --version
```

Для сборки DOCX Pandoc обязателен.

Экспериментальный предварительный PDF по флагу `--pdf` требует TeX Live 2026 с
LuaLaTeX. Для корректного шрифта ему также нужен лицензированный Times New Roman;
этот формат не входит в гарантии совместимости версии 1.0.

## Docker

Образ содержит закреплённые Python, Pandoc и TeX Live:

```sh
docker build -t tex2sto:0.1.0 .
```

Рабочий каталог монтируется в `/work`, поэтому результаты остаются на машине:

```sh
docker run --rm -v "$PWD:/work" tex2sto:0.1.0 \
  check examples/master-thesis/main.tex --strict

docker run --rm -v "$PWD:/work" tex2sto:0.1.0 \
  build examples/master-thesis/main.tex -o build/example
```

DOCX запрашивает Times New Roman стилями документа и не встраивает шрифт. Для
экспериментального PDF контейнер использует Liberation Serif как запасной
вариант, когда Times New Roman недоступен.

## Проверка установки

```sh
uv run tex2sto check examples/master-thesis/main.tex --strict
uv run tex2sto build examples/master-thesis/main.tex -o build/example
```

Успешная команда печатает абсолютный путь созданного `main.docx`.
