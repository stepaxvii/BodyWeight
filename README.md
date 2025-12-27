# 🎮 BodyWeight

Telegram Mini App для отслеживания тренировок с собственным весом в игровом пиксельном стиле.

## ✨ Особенности

- 💪 **Упражнения с собственным весом** — более 35 упражнений в 8 категориях
- 🎮 **Геймификация** — уровни, опыт, достижения и серии
- 🏆 **Достижения** — разблокируй награды за прогресс
- 📊 **Рейтинг** — соревнуйся с друзьями и глобально
- 🎯 **Цели** — ставь цели и отслеживай прогресс
- 👥 **Социальные функции** — друзья и группы
- 🎨 **Пиксельный стиль** — ретро-эстетика 8-bit

## 🛠 Технологии

### Backend
- Python 3.11+
- FastAPI
- SQLAlchemy 2.0 (async)
- aiogram 3.4.0
- SQLite / PostgreSQL

### Frontend
- SvelteKit 2.0
- Svelte 5
- TypeScript
- Telegram WebApp API

## 📦 Структура проекта

```
BodyWeight/
├── backend/
│   ├── app/
│   │   ├── api/           # REST API endpoints
│   │   ├── bot/           # Telegram bot
│   │   ├── data/          # JSON data files
│   │   ├── db/            # Database models
│   │   ├── config.py
│   │   └── main.py
│   └── requirements.txt
├── frontend/
│   └── mini-app/          # SvelteKit Mini App
└── deploy/                # Deployment configs
```

## 🚀 Запуск

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Создай .env файл
cp .env.example .env
# Заполни BOT_TOKEN и SECRET_KEY

# Запуск API
uvicorn app.main:app --reload --port 8002

# Запуск бота
python -m app.bot.main
```

### Frontend

```bash
cd frontend/mini-app
npm install
npm run dev
```

## 📱 Категории упражнений

| Категория | Описание | Примеры |
|-----------|----------|---------|
| 💪 Push | Жимовые | Отжимания, отжимания на брусьях |
| 🏋️ Pull | Тяговые | Подтягивания, австралийские подтягивания |
| 🦵 Legs | Ноги | Приседания, выпады |
| 🎯 Core | Кор/Пресс | Скручивания, подъёмы ног |
| 🧘 Static | Статика | Планка, стойка на руках |
| ❤️ Cardio | Кардио | Берпи, прыжки |
| 🔥 Warmup | Разминка | Махи руками, вращения |
| 🌊 Stretch | Растяжка | Наклоны, шпагат |

## 🏆 Система прогресса

- **XP (опыт)** — зарабатывай за каждое упражнение
- **Уровни** — требуемый XP = 100 × уровень²
- **Серии** — дни тренировок подряд
- **Достижения** — особые награды за достижения

## 📄 License

MIT
