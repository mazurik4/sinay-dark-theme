/**
 * Sinay.ua — переключатель тёмной темы.
 *
 * Как работает:
 *  - Тема хранится в localStorage под ключом "sinay-theme" ("dark" или нет записи = светлая).
 *  - Нажатие на любую кнопку с атрибутом data-theme-toggle переключает тему:
 *    светлая -> тёмная, тёмная -> снова стандартная светлая.
 *  - Тёмная тема = атрибут data-theme="dark" на <html>; все стили в theme-dark.css.
 *  - Синхронизация вкладок: браузер присылает событие "storage" во ВСЕ другие открытые
 *    вкладки этого сайта, когда меняется localStorage. Мы ловим его и применяем ту же тему,
 *    поэтому тема меняется сразу везде без перезагрузки.
 *
 * Подключается как ES-модуль: <script type="module" src="...">.
 * Модуль сам работает в строгом режиме, выполняется после загрузки страницы
 * и не создаёт глобальных переменных — обёртка (function(){...})() не нужна.
 *
 * Зависимостей нет (jQuery не нужен).
 */

const STORAGE_KEY = 'sinay-theme';
const DARK = 'dark';
const LIGHT = 'light';
const root = document.documentElement;

// Подписи кнопки (подсказка и текст для экранных чтецов) на языке страницы — по <html lang="...">.
// Тема одна на весь сайт: при смене языка RU/UA выбранная тема сохраняется.
const TEXTS = {
  ru: { toDark: 'Включить тёмную тему', toLight: 'Включить светлую тему', dark: 'Тёмная тема', light: 'Светлая тема' },
  uk: { toDark: 'Увімкнути темну тему', toLight: 'Увімкнути світлу тему', dark: 'Темна тема', light: 'Світла тема' },
};
const lang = (root.lang || 'ru').slice(0, 2).toLowerCase();
const t = TEXTS[lang] ?? TEXTS.ru;

const isDark = () => root.dataset.theme === DARK;

// Сохранённый выбор. Если браузер запретил сайту localStorage — считаем, что выбора нет.
const readSaved = () => {
  try {
    return localStorage.getItem(STORAGE_KEY) === DARK ? DARK : LIGHT;
  } catch {
    return LIGHT;
  }
};

// Применяет тему к странице и обновляет подписи кнопок (для экранных чтецов и подсказки).
const apply = (theme) => {
  const dark = theme === DARK;
  if (dark) {
    root.dataset.theme = DARK;
  } else {
    delete root.dataset.theme;
  }
  for (const button of document.querySelectorAll('[data-theme-toggle]')) {
    button.setAttribute('aria-pressed', String(dark));
    button.setAttribute('aria-label', dark ? t.toLight : t.toDark);
    button.title = dark ? t.light : t.dark;
  }
};

// Сохраняет выбор. Светлая тема — стандартная, поэтому для неё запись просто удаляем.
const save = (theme) => {
  try {
    if (theme === DARK) {
      localStorage.setItem(STORAGE_KEY, DARK);
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  } catch {
    // localStorage заблокирован браузером: тема переключится только в этой вкладке.
  }
};

const toggle = () => {
  const next = isDark() ? LIGHT : DARK;
  apply(next);
  save(next);
};

// Делегирование клика: работает и для кнопок, добавленных позже (например, в мобильном меню).
document.addEventListener('click', (e) => {
  const button = e.target.closest?.('[data-theme-toggle]');
  if (!button) return;
  e.preventDefault();
  toggle();
});

// Другая вкладка сменила тему -> применяем здесь тоже.
window.addEventListener('storage', (e) => {
  if (e.key === STORAGE_KEY || e.key === null) { // null — localStorage очищен целиком
    apply(e.newValue === DARK ? DARK : LIGHT);
  }
});

// Вкладку вернули из кэша кнопкой «Назад» — сверяемся с сохранённым выбором.
window.addEventListener('pageshow', () => apply(readSaved()));

// Начальное состояние (сама тема уже включена скриптом в <head>, тут — подписи кнопок).
apply(isDark() ? DARK : LIGHT);
