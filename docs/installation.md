# Установка

## Требования

Проверенная V1 закрепляет следующие версии:

- Python 3.12.11;
- uv 0.12.x;
- Pandoc 3.11;
- TeX Live 2026 с LuaLaTeX;
- Times New Roman для нормативного PDF.

Версии Pandoc и TeX Live проверяются при каждом запуске рендера. Несовместимая
версия останавливает сборку с кодом 2.

## macOS

Установите uv, Pandoc и TeX Live удобным для системы способом. Homebrew можно
использовать как источник внешних программ:

```sh
brew install uv pandoc
brew install --cask mactex-no-gui
```

После установки убедитесь, что `pandoc --version` показывает 3.11, а
`tlmgr --version` — TeX Live 2026. Если менеджер пакетов уже предлагает другую
основную версию, используйте Docker либо установите закреплённую версию вручную.

Разверните Python-окружение из корня репозитория:

```sh
uv sync
uv run tex2sto --version
```

Для одной только сборки DOCX LuaLaTeX не запускается, но Pandoc обязателен.

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
  build examples/master-thesis/main.tex -o build/example --pdf
```

Свободный шрифт Liberation Serif с кириллицей и Times-совместимой метрикой
используется в контейнере только как запасной вариант, когда Times New Roman
недоступен. Для нормативного PDF добавьте лицензированный Times New Roman в
окружение сборки. DOCX запрашивает Times New Roman стилями документа и не
встраивает шрифт.

## Проверка установки

```sh
uv run tex2sto check examples/master-thesis/main.tex --strict
uv run tex2sto build examples/master-thesis/main.tex -o build/example --pdf
```

Успешная команда печатает абсолютные пути созданных файлов. Полный пример
должен дать `main.docx` и `main.pdf`.
