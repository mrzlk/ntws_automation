# Roadmap

## Milestone 1: Foundation ✅
**Статус:** Завершён

- [x] Структура проекта
- [x] Базовые классы и интерфейсы
- [x] ARCHITECTURE.md
- [x] Git репозиторий

---

## Milestone 2: Core Implementation
**Статус:** Следующий

### 2.1 Window Connection
- [ ] Реализовать `TWSWindow.connect()` с реальным поиском окна
- [ ] Тесты подключения к запущенному TWS
- [ ] Обработка случаев: TWS не запущен, несколько окон

### 2.2 Element Finding
- [ ] Реализовать UIA стратегию поиска элементов
- [ ] Добавить OCR fallback для кастомных QML элементов
- [ ] Калибровка регионов под реальный терминал

### 2.3 Input
- [ ] Протестировать keyboard/mouse на реальном терминале
- [ ] Проверить работу hotkeys (Alt+B, Alt+S, etc.)
- [ ] Настроить timing (задержки между действиями)

---

## Milestone 3: Order Actions
**Статус:** Приоритет после Core

- [ ] `search_symbol` — поиск и выбор тикера
- [ ] `create_order` — создание ордера (BUY/SELL, LMT/MKT)
- [ ] `transmit_order` — отправка ордера
- [ ] `cancel_order` — отмена ордера
- [ ] Интеграционные тесты на paper trading

---

## Milestone 4: Screen Reading
- [ ] OCR для цен, символов, P&L
- [ ] Парсинг таблицы портфолио
- [ ] Парсинг списка ордеров
- [ ] Определение статуса ордера

---

## Milestone 5: MCP Server
- [ ] Запуск MCP сервера
- [ ] Тестирование всех tools
- [ ] Интеграция с Claude Desktop
- [ ] Документация для пользователя

---

## Milestone 6: Polish & Docs
- [ ] README.md с инструкциями
- [ ] Примеры использования
- [ ] Обработка edge cases
- [ ] CI/CD (опционально)
