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
 * Зависимостей нет (jQuery не нужен).
 */
(function () {
  'use strict';

  let STORAGE_KEY = 'sinay-theme';
  let DARK = 'dark';
  let root = document.documentElement;

  // Подписи кнопки (подсказка и текст для экранных чтецов) на языке страницы — по <html lang="...">.
  // Тема одна на весь сайт: при смене языка RU/UA выбранная тема сохраняется.
  let TEXTS = {
    ru: { toDark: 'Включить тёмную тему', toLight: 'Включить светлую тему', dark: 'Тёмная тема', light: 'Светлая тема' },
    uk: { toDark: 'Увімкнути темну тему', toLight: 'Увімкнути світлу тему', dark: 'Темна тема', light: 'Світла тема' }
  };
  let lang = (root.getAttribute('lang') || 'ru').slice(0, 2).toLowerCase();
  let t = TEXTS[lang] || TEXTS.ru;

  function isDark() {
    return root.getAttribute('data-theme') === DARK;
  }

  // Применяет тему к странице и обновляет подписи кнопок (для экранных чтецов и подсказки).
  function apply(theme) {
    let dark = theme === DARK;
    if (dark) {
      root.setAttribute('data-theme', DARK);
    } else {
      root.removeAttribute('data-theme');
    }
    let buttons = document.querySelectorAll('[data-theme-toggle]');
    for (let i = 0; i < buttons.length; i++) {
      buttons[i].setAttribute('aria-pressed', dark ? 'true' : 'false');
      buttons[i].setAttribute('aria-label', dark ? t.toLight : t.toDark);
      buttons[i].setAttribute('title', dark ? t.light : t.dark);
    }
  }

  // Сохраняет выбор. Светлая тема — стандартная, поэтому для неё запись просто удаляем.
  function save(theme) {
    try {
      if (theme === DARK) {
        localStorage.setItem(STORAGE_KEY, DARK);
      } else {
        localStorage.removeItem(STORAGE_KEY);
      }
    } catch (e) { /* приватный режим: тема сработает только в этой вкладке */ }
  }

  function toggle() {
    let next = isDark() ? 'light' : DARK;
    apply(next);
    save(next);
  }

  // Делегирование клика: работает и для кнопок, добавленных позже (например, в мобильном меню).
  document.addEventListener('click', function (e) {
    let btn = e.target.closest && e.target.closest('[data-theme-toggle]');
    if (!btn) return;
    e.preventDefault();
    toggle();
  });

  // Другая вкладка сменила тему -> применяем здесь тоже.
  window.addEventListener('storage', function (e) {
    if (e.key === STORAGE_KEY || e.key === null) { // null — localStorage очищен целиком
      apply(e.newValue === DARK ? DARK : 'light');
    }
  });

  // Вкладку вернули из кэша кнопкой «Назад» — сверяемся с сохранённым выбором.
  window.addEventListener('pageshow', function () {
    let saved = null;
    try { saved = localStorage.getItem(STORAGE_KEY); } catch (e) {}
    apply(saved === DARK ? DARK : 'light');
  });

  // Начальное состояние (сама тема уже включена скриптом в <head>, тут — подписи кнопок).
  apply(isDark() ? DARK : 'light');
})();
