# Билд-процесс для фронтенда

## Проблема

С добавлением скриптов для графиков работать с ними без поддержки модулей (импортов/экспортов, пакетов с npm) стало
неудобно. Без поддержки модулей и полноценной сборки фронтенд тяжело расширять.

## Решение

Использовать билд-процесс, в рамках которого собирать Яваскрипт в один файл, и подключить этот файл в корневой шаблон,
который сервит Джанго. Выбрали [Parcel](http://parceljs.org), потому что поддержка наших текущих запросов из коробки и
не нужно писать файлы конфигов.

## Рассмотренные альтернативы

- [Snowpack](https://www.snowpack.dev) - Для полноценной поддержки нужно делать миддлвару для Джанги, которая будет
  слушать каждый реквест и билдить файлы. Хорошо заточен под чистый фронтенд, но для серверного рендеринга не слишком
  лучше альтернатив, а настраивать сложнее.
- [Skypack](https://www.skypack.dev) - использует модули из npm, обрабатывая их бандлером на серверах их и выдавая по
  ссылке. Хороший подход, когда бандлер не нужен совсем. Есть ограничения (нет Тайпскрипта, JSX), и они рекомендуют
  Сноупак.
- [Rollup](https://rollupjs.org) - минимальный бандлер, который заточен под библиотеки и оптимизацию итогового бандла,
  которые в нашем случае не нужны, и замедлят процесс ребилда.
- [Webpack](https://webpack.js.org) - слишком большой и сложный для текущих задач, одна настройка и установка будет
  сложнее чем весь фронтенд.