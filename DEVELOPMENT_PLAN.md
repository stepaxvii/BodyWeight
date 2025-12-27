# BodyWeight - Technical Development Plan

## Project Overview

**BodyWeight** - Telegram Mini App for bodyweight workouts with 8-bit pixel art style gamification.

**URL:** https://stepaproject.ru/bodyweight/

---

## 1. Architecture Overview

```
                    +------------------+
                    |   Telegram Bot   |
                    |   (aiogram 3.4)  |
                    +--------+---------+
                             |
                             | WebApp Launch + Notifications
                             v
+------------------+    +------------------+    +------------------+
|   Frontend       |<-->|   Backend API    |<-->|   PostgreSQL     |
|   SvelteKit 2.0  |    |   FastAPI        |    |   (SQLite dev)   |
|   Svelte 5       |    |   SQLAlchemy 2.0 |    |                  |
+------------------+    +------------------+    +------------------+
        |                       |
        v                       v
+------------------+    +------------------+
|   Static Assets  |    |   JSON Data      |
|   /static/       |    |   exercises.json |
|   sprites, gifs  |    |   achievements   |
+------------------+    +------------------+
```

---

## 2. Project Structure

```
BodyWeight/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app entry
│   │   ├── config.py               # Settings from .env
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── database.py         # Async SQLAlchemy setup
│   │   │   └── models.py           # ORM models
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── deps.py             # Dependencies (auth, db session)
│   │   │   └── routes/
│   │   │       ├── __init__.py
│   │   │       ├── auth.py         # Telegram auth validation
│   │   │       ├── users.py        # User profile
│   │   │       ├── exercises.py    # Exercise catalog
│   │   │       ├── workouts.py     # Workout sessions
│   │   │       ├── achievements.py # Achievements
│   │   │       ├── leaderboard.py  # Rankings
│   │   │       ├── friends.py      # Social features
│   │   │       └── goals.py        # User goals
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── xp_calculator.py    # XP formula logic
│   │   │   ├── achievement_checker.py
│   │   │   └── notification_service.py
│   │   ├── bot/
│   │   │   ├── __init__.py
│   │   │   ├── main.py             # Bot setup
│   │   │   ├── handlers/
│   │   │   │   ├── __init__.py
│   │   │   │   └── start.py        # /start command
│   │   │   └── keyboards/
│   │   │       ├── __init__.py
│   │   │       └── inline.py       # WebApp button
│   │   └── data/
│   │       ├── exercises.json      # Exercise catalog
│   │       ├── achievements.json   # Achievement definitions
│   │       └── messages.json       # Bot messages
│   ├── alembic/
│   │   ├── versions/
│   │   ├── env.py
│   │   └── script.py.mako
│   ├── alembic.ini
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   └── mini-app/
│       ├── src/
│       │   ├── lib/
│       │   │   ├── components/
│       │   │   │   ├── ui/         # Reusable pixel UI components
│       │   │   │   │   ├── PixelButton.svelte
│       │   │   │   │   ├── PixelCard.svelte
│       │   │   │   │   ├── PixelProgress.svelte
│       │   │   │   │   ├── PixelChart.svelte
│       │   │   │   │   └── PixelModal.svelte
│       │   │   │   ├── exercise/
│       │   │   │   │   ├── ExerciseCard.svelte
│       │   │   │   │   └── ExerciseDetail.svelte
│       │   │   │   ├── workout/
│       │   │   │   │   ├── WorkoutTimer.svelte
│       │   │   │   │   └── WorkoutSummary.svelte
│       │   │   │   └── profile/
│       │   │   │       ├── StatsDisplay.svelte
│       │   │   │       └── AchievementBadge.svelte
│       │   │   ├── stores/
│       │   │   │   ├── user.ts      # User state
│       │   │   │   ├── workout.ts   # Active workout
│       │   │   │   └── telegram.ts  # Telegram WebApp
│       │   │   ├── api/
│       │   │   │   └── client.ts    # API client
│       │   │   ├── utils/
│       │   │   │   ├── xp.ts        # XP calculations
│       │   │   │   └── format.ts    # Formatters
│       │   │   └── types/
│       │   │       └── index.ts     # TypeScript types
│       │   ├── routes/
│       │   │   ├── +layout.svelte   # Main layout with nav
│       │   │   ├── +page.svelte     # Home/Dashboard
│       │   │   ├── workout/
│       │   │   │   ├── +page.svelte         # Category selection
│       │   │   │   ├── [category]/
│       │   │   │   │   └── +page.svelte     # Exercise list
│       │   │   │   └── session/
│       │   │   │       └── +page.svelte     # Active workout
│       │   │   ├── profile/
│       │   │   │   └── +page.svelte
│       │   │   ├── achievements/
│       │   │   │   └── +page.svelte
│       │   │   ├── leaderboard/
│       │   │   │   └── +page.svelte
│       │   │   ├── friends/
│       │   │   │   └── +page.svelte
│       │   │   ├── shop/
│       │   │   │   └── +page.svelte
│       │   │   └── settings/
│       │   │       └── +page.svelte
│       │   ├── app.html
│       │   ├── app.css             # Global pixel styles
│       │   └── app.d.ts
│       ├── static/
│       │   ├── sprites/            # 16x16 pixel sprites
│       │   │   ├── icons/
│       │   │   ├── achievements/
│       │   │   └── ui/
│       │   ├── exercises/          # Exercise GIFs
│       │   └── fonts/
│       │       └── pixel.woff2     # Pixel font
│       ├── package.json
│       ├── svelte.config.js
│       ├── vite.config.ts
│       └── tsconfig.json
│
├── deploy/
│   ├── docker-compose.yml
│   ├── nginx.conf
│   └── systemd/
│       └── bodyweight.service
│
├── .env.example
├── .gitignore
└── README.md
```

---

## 3. Database Schema

```sql
-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    photo_url TEXT,

    -- Gamification
    level INTEGER DEFAULT 1,
    total_xp INTEGER DEFAULT 0,
    coins INTEGER DEFAULT 0,

    -- Streaks
    current_streak INTEGER DEFAULT 0,
    max_streak INTEGER DEFAULT 0,
    last_workout_date DATE,

    -- Settings
    notification_time TIME,
    notifications_enabled BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Exercise categories
CREATE TABLE exercise_categories (
    id SERIAL PRIMARY KEY,
    slug VARCHAR(50) UNIQUE NOT NULL,  -- push, pull, legs, etc.
    name VARCHAR(100) NOT NULL,
    name_ru VARCHAR(100) NOT NULL,
    icon VARCHAR(50),                   -- sprite name
    color VARCHAR(7),                   -- hex color
    sort_order INTEGER DEFAULT 0
);

-- Exercises
CREATE TABLE exercises (
    id SERIAL PRIMARY KEY,
    category_id INTEGER REFERENCES exercise_categories(id),
    slug VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    name_ru VARCHAR(255) NOT NULL,
    description TEXT,
    description_ru TEXT,

    -- Difficulty & progression
    difficulty INTEGER CHECK (difficulty BETWEEN 1 AND 5),
    base_xp INTEGER DEFAULT 10,
    required_level INTEGER DEFAULT 1,

    -- Media
    gif_url VARCHAR(255),
    thumbnail_url VARCHAR(255),

    -- Progression chain
    easier_exercise_id INTEGER REFERENCES exercises(id),
    harder_exercise_id INTEGER REFERENCES exercises(id),

    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Workout sessions
CREATE TABLE workout_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,

    started_at TIMESTAMP NOT NULL,
    finished_at TIMESTAMP,
    duration_seconds INTEGER,

    -- Totals
    total_xp_earned INTEGER DEFAULT 0,
    total_coins_earned INTEGER DEFAULT 0,
    total_reps INTEGER DEFAULT 0,

    -- Streak bonus applied
    streak_multiplier DECIMAL(3,2) DEFAULT 1.00,

    status VARCHAR(20) DEFAULT 'active'  -- active, completed, cancelled
);

-- Workout exercises (sets within a workout)
CREATE TABLE workout_exercises (
    id SERIAL PRIMARY KEY,
    workout_session_id INTEGER REFERENCES workout_sessions(id) ON DELETE CASCADE,
    exercise_id INTEGER REFERENCES exercises(id),

    sets_completed INTEGER DEFAULT 0,
    total_reps INTEGER DEFAULT 0,

    xp_earned INTEGER DEFAULT 0,
    coins_earned INTEGER DEFAULT 0,

    completed_at TIMESTAMP DEFAULT NOW()
);

-- User achievements
CREATE TABLE user_achievements (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    achievement_slug VARCHAR(100) NOT NULL,

    unlocked_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(user_id, achievement_slug)
);

-- User goals
CREATE TABLE user_goals (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,

    goal_type VARCHAR(50) NOT NULL,  -- weekly_workouts, daily_xp, specific_exercise
    target_value INTEGER NOT NULL,
    current_value INTEGER DEFAULT 0,

    start_date DATE NOT NULL,
    end_date DATE NOT NULL,

    completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT NOW()
);

-- Friends
CREATE TABLE friendships (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    friend_id INTEGER REFERENCES users(id) ON DELETE CASCADE,

    status VARCHAR(20) DEFAULT 'pending',  -- pending, accepted, blocked

    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(user_id, friend_id)
);

-- Shop items (cosmetics)
CREATE TABLE shop_items (
    id SERIAL PRIMARY KEY,
    slug VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    name_ru VARCHAR(255) NOT NULL,

    item_type VARCHAR(50) NOT NULL,  -- title, badge, theme

    price_coins INTEGER NOT NULL,
    required_level INTEGER DEFAULT 1,

    sprite_url VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE
);

-- User purchases
CREATE TABLE user_purchases (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    shop_item_id INTEGER REFERENCES shop_items(id),

    purchased_at TIMESTAMP DEFAULT NOW(),
    is_equipped BOOLEAN DEFAULT FALSE,

    UNIQUE(user_id, shop_item_id)
);

-- Exercise progress tracking (for recommendations)
CREATE TABLE user_exercise_progress (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    exercise_id INTEGER REFERENCES exercises(id),

    total_reps_ever INTEGER DEFAULT 0,
    best_single_set INTEGER DEFAULT 0,
    times_performed INTEGER DEFAULT 0,
    last_performed_at TIMESTAMP,

    -- For progression recommendations
    recommended_upgrade BOOLEAN DEFAULT FALSE,

    UNIQUE(user_id, exercise_id)
);

-- Indexes
CREATE INDEX idx_users_telegram_id ON users(telegram_id);
CREATE INDEX idx_workout_sessions_user ON workout_sessions(user_id);
CREATE INDEX idx_workout_sessions_date ON workout_sessions(started_at);
CREATE INDEX idx_workout_exercises_session ON workout_exercises(workout_session_id);
CREATE INDEX idx_friendships_user ON friendships(user_id, status);
CREATE INDEX idx_user_achievements_user ON user_achievements(user_id);
```

---

## 4. API Specification

### Authentication
All endpoints require Telegram WebApp initData validation.

```
Header: Authorization: tma <initData>
```

### Endpoints

#### Auth
```
POST /api/auth/validate
- Validates Telegram initData
- Creates or updates user
- Returns: { user, token }
```

#### Users
```
GET  /api/users/me              - Current user profile
PUT  /api/users/me              - Update profile/settings
GET  /api/users/:id             - Get user by ID (public profile)
GET  /api/users/me/stats        - Detailed statistics
```

#### Exercises
```
GET  /api/exercises             - All exercises (with filters)
GET  /api/exercises/categories  - All categories
GET  /api/exercises/:slug       - Single exercise details
GET  /api/exercises/:slug/progress - User progress for exercise
```

#### Workouts
```
POST /api/workouts              - Start new workout session
GET  /api/workouts/:id          - Get workout details
PUT  /api/workouts/:id          - Update workout (add exercises)
POST /api/workouts/:id/complete - Complete workout
GET  /api/workouts/history      - User workout history
GET  /api/workouts/today        - Today's workout summary
```

#### Achievements
```
GET  /api/achievements          - All achievements (with unlock status)
GET  /api/achievements/recent   - Recently unlocked
```

#### Leaderboard
```
GET  /api/leaderboard           - Global leaderboard
GET  /api/leaderboard/friends   - Friends leaderboard
GET  /api/leaderboard/weekly    - Weekly rankings
```

#### Friends
```
GET    /api/friends             - List friends
POST   /api/friends/add         - Send friend request
POST   /api/friends/accept/:id  - Accept request
DELETE /api/friends/:id         - Remove friend
GET    /api/friends/search      - Search by username
```

#### Goals
```
GET  /api/goals                 - Active goals
POST /api/goals                 - Create goal
PUT  /api/goals/:id             - Update goal progress
```

#### Shop
```
GET  /api/shop                  - All shop items
POST /api/shop/purchase/:id     - Purchase item
GET  /api/shop/inventory        - User's purchased items
POST /api/shop/equip/:id        - Equip item
```

---

## 5. XP & Coins Formula

### XP Calculation
```python
def calculate_xp(
    base_xp: int,           # From exercise definition
    difficulty: int,        # 1-5
    reps: int,              # Reps performed
    streak_days: int,       # Current streak
    is_first_today: bool    # First workout of the day
) -> int:
    # Difficulty multiplier
    difficulty_mult = 1 + (difficulty - 1) * 0.25  # 1.0, 1.25, 1.5, 1.75, 2.0

    # Streak bonus (max 50% at 30+ days)
    streak_mult = 1 + min(streak_days, 30) * 0.0167  # ~1.5 max

    # Volume bonus (diminishing returns after 20 reps)
    if reps <= 20:
        volume_mult = 1 + reps * 0.02  # 1.0 to 1.4
    else:
        volume_mult = 1.4 + (reps - 20) * 0.01  # slower growth

    # First workout bonus
    first_bonus = 1.2 if is_first_today else 1.0

    xp = base_xp * difficulty_mult * streak_mult * volume_mult * first_bonus
    return int(xp)
```

### Coins Calculation
```python
def calculate_coins(xp_earned: int, has_achievement: bool) -> int:
    # Base: 1 coin per 10 XP
    coins = xp_earned // 10

    # Achievement bonus
    if has_achievement:
        coins += 50

    return coins
```

### Level Formula
```python
def xp_for_level(level: int) -> int:
    return 100 * level * level  # 100, 400, 900, 1600...

def get_level_from_xp(total_xp: int) -> int:
    level = 1
    while xp_for_level(level + 1) <= total_xp:
        level += 1
    return level
```

---

## 6. Screen Flow & Navigation

### Screens (7 main)

1. **Home/Dashboard** (`/`)
   - Today's stats (XP, streak, level progress)
   - Quick workout button
   - Recent achievements
   - Friend activity preview

2. **Workout** (`/workout`)
   - Category grid (8 categories)
   - Exercise list per category
   - Active workout session

3. **Profile** (`/profile`)
   - Level, XP, streaks
   - Statistics charts
   - Equipped cosmetics

4. **Achievements** (`/achievements`)
   - All achievements grid
   - Locked/unlocked status
   - Progress for incomplete

5. **Leaderboard** (`/leaderboard`)
   - Tabs: Global, Friends, Weekly
   - User rankings

6. **Friends** (`/friends`)
   - Friend list
   - Search/add friends
   - View friend profiles

7. **Shop** (`/shop`)
   - Purchasable items
   - Coin balance
   - Equipped items

### Navigation
- Bottom tab bar: Home, Workout, Profile, Leaderboard
- Profile -> Settings, Achievements, Friends, Shop

---

## 7. Pixel Art Assets Required

### Sprites (16x16)

#### UI Elements
- [ ] nav_home.png
- [ ] nav_workout.png
- [ ] nav_profile.png
- [ ] nav_leaderboard.png
- [ ] icon_xp.png
- [ ] icon_coin.png
- [ ] icon_streak.png
- [ ] icon_level.png
- [ ] icon_timer.png
- [ ] icon_reps.png
- [ ] icon_check.png
- [ ] icon_lock.png
- [ ] icon_star.png (1-5 for difficulty)
- [ ] icon_friend.png
- [ ] icon_settings.png
- [ ] icon_back.png

#### Category Icons
- [ ] cat_push.png
- [ ] cat_pull.png
- [ ] cat_legs.png
- [ ] cat_core.png
- [ ] cat_static.png
- [ ] cat_cardio.png
- [ ] cat_warmup.png
- [ ] cat_stretch.png

#### Achievement Badges (24 icons)
- [ ] ach_first_workout.png
- [ ] ach_streak_7.png
- [ ] ach_streak_30.png
- [ ] ach_level_10.png
- [ ] ach_100_pushups.png
- [ ] ach_early_bird.png
- [ ] ach_night_owl.png
- [ ] ... (more achievements)

#### Shop Items
- [ ] Various badge/title sprites
- [ ] Theme color palettes

### Exercise GIFs (35+ exercises)
Simple 2-4 frame pixel animations showing:
- Starting position
- Movement
- End position
- Return

Resolution: 128x128 or 96x96 scaled from 16x16 base

### Color Palette (NES-inspired, 16 colors)
```css
:root {
    --pixel-black: #0f0f0f;
    --pixel-dark: #2d2d2d;
    --pixel-gray: #5a5a5a;
    --pixel-light: #9a9a9a;
    --pixel-white: #fcfcfc;

    --pixel-red: #d82800;
    --pixel-orange: #fc7400;
    --pixel-yellow: #fcc800;
    --pixel-green: #00a800;
    --pixel-cyan: #00a8a8;
    --pixel-blue: #0058f8;
    --pixel-purple: #6800a8;
    --pixel-pink: #f878f8;

    --pixel-bg: #1a1a2e;
    --pixel-card: #16213e;
    --pixel-accent: #e94560;
}
```

---

## 8. Exercise Data Structure

```json
{
  "categories": [
    {
      "slug": "push",
      "name": "Push",
      "name_ru": "Толкающие",
      "icon": "cat_push",
      "color": "#d82800"
    }
  ],
  "exercises": [
    {
      "slug": "pushup-regular",
      "category": "push",
      "name": "Push-up",
      "name_ru": "Отжимания",
      "description": "Classic push-up with hands shoulder-width apart",
      "description_ru": "Классические отжимания, руки на ширине плеч",
      "difficulty": 2,
      "base_xp": 10,
      "required_level": 1,
      "gif": "pushup-regular.gif",
      "easier": "pushup-knee",
      "harder": "pushup-diamond"
    },
    {
      "slug": "pushup-knee",
      "category": "push",
      "name": "Knee Push-up",
      "name_ru": "Отжимания с колен",
      "difficulty": 1,
      "base_xp": 8,
      "required_level": 1,
      "harder": "pushup-regular"
    },
    {
      "slug": "pushup-diamond",
      "category": "push",
      "name": "Diamond Push-up",
      "name_ru": "Алмазные отжимания",
      "difficulty": 4,
      "base_xp": 15,
      "required_level": 5,
      "easier": "pushup-regular",
      "harder": "pushup-archer"
    }
  ]
}
```

---

## 9. Achievements Definition

```json
{
  "achievements": [
    {
      "slug": "first_workout",
      "name": "First Step",
      "name_ru": "Первый шаг",
      "description": "Complete your first workout",
      "description_ru": "Завершите первую тренировку",
      "icon": "ach_first_workout",
      "xp_reward": 50,
      "coin_reward": 100,
      "condition": { "type": "total_workouts", "value": 1 }
    },
    {
      "slug": "streak_7",
      "name": "Week Warrior",
      "name_ru": "Недельный воин",
      "description": "Maintain a 7-day streak",
      "description_ru": "Поддержите серию 7 дней",
      "icon": "ach_streak_7",
      "xp_reward": 200,
      "coin_reward": 300,
      "condition": { "type": "streak", "value": 7 }
    },
    {
      "slug": "streak_30",
      "name": "Month Master",
      "name_ru": "Месячный мастер",
      "description": "Maintain a 30-day streak",
      "description_ru": "Поддержите серию 30 дней",
      "icon": "ach_streak_30",
      "xp_reward": 1000,
      "coin_reward": 1000,
      "condition": { "type": "streak", "value": 30 }
    },
    {
      "slug": "pushup_100",
      "name": "Push-up Centurion",
      "name_ru": "Сотня отжиманий",
      "description": "Do 100 push-ups total",
      "description_ru": "Сделайте 100 отжиманий всего",
      "icon": "ach_100_pushups",
      "xp_reward": 150,
      "coin_reward": 200,
      "condition": { "type": "exercise_reps", "exercise": "pushup-*", "value": 100 }
    },
    {
      "slug": "early_bird",
      "name": "Early Bird",
      "name_ru": "Ранняя пташка",
      "description": "Complete a workout before 7 AM",
      "description_ru": "Завершите тренировку до 7 утра",
      "icon": "ach_early_bird",
      "xp_reward": 100,
      "coin_reward": 150,
      "condition": { "type": "time_of_day", "before": "07:00" }
    },
    {
      "slug": "level_10",
      "name": "Double Digits",
      "name_ru": "Двузначный",
      "description": "Reach level 10",
      "description_ru": "Достигните 10 уровня",
      "icon": "ach_level_10",
      "xp_reward": 500,
      "coin_reward": 500,
      "condition": { "type": "level", "value": 10 }
    }
  ]
}
```

---

## 10. Development Phases

### Phase 1: Foundation
**Focus:** Core infrastructure and basic functionality

**Backend:**
- [ ] Project setup (FastAPI, SQLAlchemy 2.0 async)
- [ ] Database models and migrations
- [ ] Telegram auth validation
- [ ] Basic user CRUD
- [ ] Exercise catalog API
- [ ] Basic workout CRUD

**Frontend:**
- [ ] SvelteKit project setup
- [ ] Telegram WebApp SDK integration
- [ ] Pixel CSS design system
- [ ] Basic routing
- [ ] API client
- [ ] Auth flow

**Bot:**
- [ ] aiogram 3.4 setup
- [ ] /start command with WebApp button
- [ ] Basic inline keyboard

---

### Phase 2: Core Features
**Focus:** Workout tracking and gamification

**Backend:**
- [ ] Complete workout flow (start, add exercises, complete)
- [ ] XP calculation service
- [ ] Level progression
- [ ] Streak tracking
- [ ] Basic achievement checking

**Frontend:**
- [ ] Home dashboard
- [ ] Exercise category browser
- [ ] Exercise detail view
- [ ] Active workout session UI
- [ ] Workout timer
- [ ] Rep counter
- [ ] Workout summary

---

### Phase 3: Gamification
**Focus:** Full gamification system

**Backend:**
- [ ] Complete achievement system
- [ ] Coins earning logic
- [ ] Goal system
- [ ] Leaderboard queries

**Frontend:**
- [ ] Profile page with stats
- [ ] Achievement gallery
- [ ] Leaderboard views (global, weekly)
- [ ] Progress charts (pixel style)
- [ ] Goal management UI

---

### Phase 4: Social & Shop
**Focus:** Social features and monetization

**Backend:**
- [ ] Friend system (add, accept, list)
- [ ] Shop items management
- [ ] Purchase/equip logic
- [ ] Friend leaderboard

**Frontend:**
- [ ] Friends list and search
- [ ] Friend profiles
- [ ] Shop UI
- [ ] Inventory management
- [ ] Equipped items display

---

### Phase 5: Notifications & Polish
**Focus:** Bot notifications and UX polish

**Backend:**
- [ ] Scheduled notifications (workout reminders)
- [ ] Achievement notifications
- [ ] Streak warning notifications
- [ ] Weekly summary messages

**Frontend:**
- [ ] Settings page
- [ ] Notification preferences
- [ ] Onboarding flow
- [ ] Loading states and animations
- [ ] Error handling

---

### Phase 6: Testing & Launch
**Focus:** Quality assurance and deployment

- [ ] Unit tests (pytest for backend)
- [ ] API integration tests
- [ ] E2E tests (Playwright)
- [ ] Performance optimization
- [ ] Security review
- [ ] Production deployment
- [ ] Monitoring setup

---

## 11. Deployment Strategy

### Server Requirements
- VPS with 1GB+ RAM
- Ubuntu 22.04+
- Docker & Docker Compose
- Nginx as reverse proxy
- Let's Encrypt SSL (via certbot)

### Docker Compose
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    environment:
      - DATABASE_URL=postgresql+asyncpg://user:pass@db/bodyweight
      - BOT_TOKEN=${BOT_TOKEN}
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      - db
    restart: unless-stopped

  frontend:
    build: ./frontend/mini-app
    restart: unless-stopped

  bot:
    build:
      context: ./backend
      dockerfile: Dockerfile.bot
    environment:
      - BOT_TOKEN=${BOT_TOKEN}
      - MINI_APP_URL=${MINI_APP_URL}
    depends_on:
      - backend
    restart: unless-stopped

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=bodyweight
    volumes:
      - pgdata:/var/lib/postgresql/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./deploy/nginx.conf:/etc/nginx/nginx.conf
      - /etc/letsencrypt:/etc/letsencrypt
    depends_on:
      - backend
      - frontend
    restart: unless-stopped

volumes:
  pgdata:
```

### Nginx Config
```nginx
server {
    listen 443 ssl http2;
    server_name stepaproject.ru;

    ssl_certificate /etc/letsencrypt/live/stepaproject.ru/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/stepaproject.ru/privkey.pem;

    # Frontend (Mini App)
    location /bodyweight {
        proxy_pass http://frontend:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /bodyweight/api {
        proxy_pass http://backend:8000/api;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Static files (exercise GIFs, sprites)
    location /bodyweight/static {
        alias /app/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

---

## 12. Testing Strategy

### Backend Tests (pytest)

```python
# tests/test_xp.py
def test_xp_calculation_basic():
    xp = calculate_xp(base_xp=10, difficulty=2, reps=10, streak_days=0, is_first_today=True)
    assert xp > 10  # Should have bonuses

def test_xp_streak_bonus():
    xp_no_streak = calculate_xp(10, 2, 10, 0, False)
    xp_with_streak = calculate_xp(10, 2, 10, 7, False)
    assert xp_with_streak > xp_no_streak

# tests/test_auth.py
async def test_telegram_auth_valid():
    response = await client.post("/api/auth/validate", ...)
    assert response.status_code == 200

# tests/test_workouts.py
async def test_create_workout():
    response = await client.post("/api/workouts", ...)
    assert response.status_code == 201
```

### Frontend Tests (Vitest + Playwright)

```typescript
// Component tests
test('PixelProgress renders correctly', () => {
  render(PixelProgress, { props: { value: 50, max: 100 } });
  expect(screen.getByRole('progressbar')).toBeInTheDocument();
});

// E2E tests
test('complete workout flow', async ({ page }) => {
  await page.goto('/workout');
  await page.click('[data-category="push"]');
  await page.click('[data-exercise="pushup-regular"]');
  await page.click('[data-action="add-set"]');
  // ...
});
```

---

## 13. File Dependencies

### requirements.txt
```
fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy[asyncio]==2.0.25
asyncpg==0.29.0
aiosqlite==0.19.0
aiogram==3.4.0
python-jose[cryptography]==3.3.0
pydantic==2.5.3
pydantic-settings==2.1.0
alembic==1.13.1
httpx==0.26.0
python-multipart==0.0.6
```

### package.json (frontend)
```json
{
  "name": "bodyweight-mini-app",
  "version": "1.0.0",
  "scripts": {
    "dev": "vite dev",
    "build": "vite build",
    "preview": "vite preview"
  },
  "devDependencies": {
    "@sveltejs/adapter-node": "^5.0.0",
    "@sveltejs/kit": "^2.0.0",
    "@sveltejs/vite-plugin-svelte": "^3.0.0",
    "svelte": "^5.0.0",
    "typescript": "^5.3.0",
    "vite": "^5.0.0",
    "vitest": "^1.2.0",
    "@playwright/test": "^1.41.0"
  },
  "dependencies": {
    "@anthropic-ai/telegram-sdk": "latest"
  }
}
```

---

## Summary

This document provides a complete technical specification for BodyWeight Telegram Mini App including:

- Full project architecture and folder structure
- Complete database schema with all tables
- REST API specification
- XP/Coins/Level formulas
- UI/UX screen flow
- Pixel art asset requirements
- Achievement system
- 6-phase development plan
- Deployment configuration
- Testing strategy

Ready to begin implementation!
