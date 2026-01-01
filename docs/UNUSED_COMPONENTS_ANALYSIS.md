# Анализ неиспользуемых компонентов

## Проверка использования компонентов

### ✅ Используемые компоненты

1. **RoutinePlayer.svelte** - используется в `routes/workout/+page.svelte`
2. **QuickExerciseModal.svelte** - используется в `routes/+page.svelte`
3. **AvatarPicker.svelte** - используется в `routes/profile/+page.svelte`
4. **UserProfileModal.svelte** - используется в `routes/leaderboard/+page.svelte`
5. **FilterModal.svelte** - используется в `routes/workout/+page.svelte`
6. **ExerciseInfoModal.svelte** - используется в:
   - `lib/components/CustomRoutineEditor.svelte`
   - НЕ используется в `routes/workout/+page.svelte` (там используется встроенный модальный код)
7. **CustomRoutineEditor.svelte** - используется в `routes/workout/+page.svelte`
8. **ExerciseCard.svelte** - используется в `routes/workout/+page.svelte`
9. **CustomRoutineList.svelte** - используется в `routes/workout/+page.svelte`
10. **OnboardingScreen.svelte** - используется в `routes/+layout.svelte`
11. **OnboardingSlides.svelte** - используется в `lib/components/OnboardingScreen.svelte`
12. **PixelIcon.svelte** - используется везде
13. **PixelModal.svelte** - используется в:
    - `lib/components/QuickExerciseModal.svelte`
    - `lib/components/ui/AvatarPicker.svelte`
    - `lib/components/FilterModal.svelte`
    - `lib/components/ExerciseInfoModal.svelte`
14. **PixelNav.svelte** - используется в `routes/+layout.svelte`
15. **PixelAvatar.svelte** - используется в:
    - `routes/profile/+page.svelte`
    - `routes/leaderboard/+page.svelte`
    - `routes/friends/+page.svelte`
    - `lib/components/ui/AvatarPicker.svelte`
    - `lib/components/UserProfileModal.svelte`
    - `lib/components/OnboardingScreen.svelte`
16. **PixelCard.svelte** - используется везде
17. **PixelButton.svelte** - используется везде
18. **PixelProgress.svelte** - используется в `routes/+page.svelte` и `routes/profile/+page.svelte`

### ❌ Неиспользуемые компоненты

**НЕ НАЙДЕНО** - все компоненты используются!

## Вывод

Все компоненты в проекте используются. Неиспользуемых компонентов не обнаружено.

## Рекомендации

1. ✅ Все компоненты актуальны и используются
2. ✅ Структура компонентов хорошо организована
3. ✅ Нет "мертвого кода" среди компонентов

## Примечания

- `ExerciseInfoModal` используется косвенно через `ExerciseCard` (пропс `onInfoClick`)
- Все UI компоненты (`Pixel*`) активно используются в различных частях приложения
- Компоненты модальных окон используются в соответствующих местах

