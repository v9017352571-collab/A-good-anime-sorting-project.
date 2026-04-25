import sys
import os
import webbrowser
import sqlite3
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QLineEdit, QLabel, QPushButton, QRadioButton,
                             QTableWidget, QTableWidgetItem, QMessageBox, QDialog,
                             QComboBox, QMenuBar, QMenu, QCheckBox, QFileDialog)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QPixmap, QImage


class DatabaseManager:
    """Класс для управления базой данных аниме.АНИМЕ МЕНЕДЖЕР - ТЕСТОВАЯ ВЕРСИЯ

ИНСТРУКЦИЯ ПО УСТАНОВКЕ:
1. Распакуйте этот архив в любую папку на вашем компьютере
2. Дважды кликните на файл anime_manager.exe
3. При появлении предупреждения безопасности Windows:
   - Нажмите "Подробнее"
   - Нажмите "Выполнить в любом случае"
4. В первом окне выберите "Я согласен с политикой компании"
5. Наслаждайтесь приложением!

ВАЖНО: Все ваши данные будут храниться только на вашем компьютере в файле best_anime.sqlite

Для обратной связи: ваш_email@example.com

    Этот класс отвечает за все операции с базой данных:
    - Создание таблиц при первом запуске
    - Добавление, удаление и получение данных
    - Обновление информации об аниме
    - Управление жанрами
    """

    def __init__(self, db_name="best_anime.sqlite"):
        """Инициализация с поддержкой cx_Freeze"""

        self.db_name = db_name
        self.init_database()

    def get_connection(self):
        """Создание соединения с базой данных.

        Этот метод возвращает новое соединение с SQLite базой данных.
        Соединение нужно закрывать после использования (обычно в блоке finally).
        """
        return sqlite3.connect(self.db_name)  # Создаем и возвращаем соединение

    def init_database(self):
        """Инициализация базы данных - создает таблицы если они не существуют.

        Этот метод создает две таблицы:
        1. genres - для хранения жанров аниме
        2. animes - для хранения информации об аниме

        Важно: в этой версии кода таблица genres НЕ заполняется стандартными жанрами,
        что предотвращает дублирование жанров при последующих запусках приложения.
        """
        conn = self.get_connection()  # Получаем соединение с базой данных
        cursor = conn.cursor()  # Создаем курсор для выполнения SQL запросов

        try:
            # Создаем таблицу жанров если она не существует
            # id - уникальный идентификатор (автоинкремент)
            # title - название жанра (уникальное, не может быть пустым)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS genres (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL UNIQUE
                )
            ''')

            # Создаем таблицу аниме если она не существует
            # id - уникальный идентификатор (автоинкремент)
            # title - название (обязательное поле)
            # year - год выпуска
            # genre - внешний ключ на таблицу жанров
            # duration - количество эпизодов
            # prosmotrs - счетчик просмотров (по умолчанию '0')
            # poster - изображение постера в формате BLOB (бинарные данные)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS animes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    year INTEGER,
                    genre INTEGER,
                    duration INTEGER,
                    prosmotrs TEXT DEFAULT '0',
                    poster BLOB,
                    FOREIGN KEY (genre) REFERENCES genres(id)
                )
            ''')

            # Сохраняем изменения в базе данных
            conn.commit()

        except Exception as e:
            # В случае ошибки печатаем сообщение и откатываем транзакцию
            print(f"Ошибка при инициализации базы данных: {e}")
            conn.rollback()
        finally:
            # В любом случае закрываем соединение с базой данных
            conn.close()

    def get_all_films(self):
        """Получение всех аниме из базы данных.

        Выполняет SQL запрос с JOIN к таблице жанров,
        чтобы вместо ID жанра получить его название.
        COALESCE используется для замены NULL на '0' в поле просмотров.
        Результат сортируется по ID для сохранения порядка добавления.
        """
        conn = self.get_connection()  # Получаем соединение
        cursor = conn.cursor()  # Создаем курсор
        try:
            # Выполняем сложный SQL запрос с объединением таблиц
            cursor.execute('''
                SELECT 
                    f.id,
                    f.title,
                    f.year,
                    g.title as genre_title,          -- Получаем название жанра вместо ID
                    f.duration,
                    COALESCE(f.prosmotrs, '0') as prosmotrs,  -- Заменяем NULL на '0'
                    f.poster
                FROM animes f
                LEFT JOIN genres g ON f.genre = g.id  -- Объединяем с таблицей жанров
                ORDER BY f.id  -- Сортируем по ID
            ''')
            return cursor.fetchall()  # Возвращаем все результаты запроса
        except Exception as e:
            # В случае ошибки печатаем сообщение и возвращаем пустой список
            print(f"Ошибка при получении аниме: {e}")
            return []
        finally:
            # Закрываем соединение в любом случае
            conn.close()

    def add_film(self, title, year, genre_id, duration):
        """Добавление нового аниме в базу данных.

        Принимает:
        title - название аниме
        year - год выпуска
        genre_id - ID жанра из таблицы genres
        duration - количество эпизодов

        Устанавливает счетчик просмотров в '0' по умолчанию.
        Возвращает True при успехе, False при ошибке.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # SQL запрос для вставки новой записи
            cursor.execute('''
                INSERT INTO animes (title, year, genre, duration, prosmotrs)
                VALUES (?, ?, ?, ?, '0')  -- prosmotrs устанавливается в '0' по умолчанию
            ''', (title, year, genre_id, duration))
            conn.commit()  # Сохраняем изменения
            return True  # Возвращаем True при успехе
        except Exception as e:
            # При ошибке печатаем сообщение, откатываем транзакцию и возвращаем False
            print(f"Ошибка при добавлении аниме: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def delete_film(self, film_id):
        """Удаление аниме по ID.

        film_id - идентификатор аниме для удаления
        cursor.rowcount > 0 проверяет, была ли удалена хотя бы одна запись,
        что означает, что запись существовала и была успешно удалена.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('DELETE FROM animes WHERE id = ?', (film_id,))  # Удаляем запись по ID
            conn.commit()  # Сохраняем изменения
            return cursor.rowcount > 0  # Возвращаем True если запись была удалена
        except Exception as e:
            print(f"Ошибка при удалении аниме: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def get_film_title(self, film_id):
        """Получение названия аниме по ID.

        Используется для отображения названия при подтверждении удаления.
        Возвращает None если аниме с таким ID не найдено.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT title FROM animes WHERE id = ?', (film_id,))  # Запрашиваем только название
            result = cursor.fetchone()  # Получаем одну запись
            return result if result else None  # Возвращаем название или None
        except Exception:
            return None  # Возвращаем None при любой ошибке
        finally:
            conn.close()

    def get_all_genres(self):
        """Получение всех жанров из базы.

        Возвращает список кортежей вида [(id1, 'Жанр1'), (id2, 'Жанр2'), ...]
        Сортировка по названию (ORDER BY title) улучшает удобство выбора в интерфейсе.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                'SELECT id, title FROM genres ORDER BY title')  # Запрашиваем ID и названия, сортируем по алфавиту
            return cursor.fetchall()  # Возвращаем все результаты
        except Exception:
            return []  # Возвращаем пустой список при ошибке
        finally:
            conn.close()

    def increment_views(self, film_id):
        """Увеличение счетчика просмотров на 1.

        1. Сначала получаем текущее значение просмотров
        2. Преобразуем в число и увеличиваем на 1
        3. Сохраняем новое значение обратно в базу
        COALESCE нужен для обработки случая, когда поле prosmotrs равно NULL
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # Получаем текущее значение просмотров
            cursor.execute('SELECT COALESCE(prosmotrs, "0") FROM animes WHERE id = ?', (film_id,))
            result = cursor.fetchone()  # Получаем одну запись

            if result:
                current_views = int(result[0])  # Преобразуем строку в число
                new_views = str(current_views + 1)  # Увеличиваем на 1 и преобразуем обратно в строку

                # Обновляем значение в базе данных
                cursor.execute('UPDATE animes SET prosmotrs = ? WHERE id = ?', (new_views, film_id))
                conn.commit()  # Сохраняем изменения
                return True  # Возвращаем True при успехе
            return False  # Если запись не найдена, возвращаем False

        except Exception as e:
            print(f"Ошибка при увеличении просмотров: {e}")
            conn.rollback()  # Откатываем изменения при ошибке
            return False
        finally:
            conn.close()

    def update_film_poster(self, film_id, image_path):
        """Обновление постера аниме.

        1. Читает файл изображения в бинарном режиме
        2. Сохраняет бинарные данные в поле poster таблицы animes
        3. Обрабатывает ошибки чтения файла и обновления базы
        """

        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # Открываем файл изображения в бинарном режиме
            with open(image_path, 'rb') as file:
                image_data = file.read()  # Читаем все содержимое файла

            # Обновляем поле poster для указанного аниме
            cursor.execute('UPDATE animes SET poster = ? WHERE id = ?', (image_data, film_id))
            conn.commit()  # Сохраняем изменения
            return True  # Возвращаем True при успехе

        except Exception as e:
            print(f"Ошибка при обновлении постера: {e}")
            conn.rollback()  # Откатываем изменения при ошибке
            return False
        finally:
            conn.close()

    def get_film_poster(self, film_id):
        """Получение постера аниме по ID.

        Возвращает бинарные данные изображения (BLOB) или None если постера нет.
        Эти данные затем используются для отображения в интерфейсе.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT poster FROM animes WHERE id = ?', (film_id,))  # Запрашиваем только поле poster
            result = cursor.fetchone()  # Получаем одну запись
            return result[0] if result else None  # Возвращаем данные или None
        except Exception:
            return None  # Возвращаем None при любой ошибке
        finally:
            conn.close()

    def update_film_field(self, film_id, field, value):
        """Обновление информации об аниме в базе данных.

        film_id - ID аниме для обновления
        field - имя поля для обновления (title, year, duration, prosmotrs)
        value - новое значение для поля
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # Формируем SQL запрос с динамическим именем поля
            cursor.execute(f'UPDATE animes SET {field} = ? WHERE id = ?', (value, film_id))
            conn.commit()  # Сохраняем изменения
            return cursor.rowcount > 0  # True если обновление прошло успешно

        except Exception as e:
            print(f"Ошибка при обновлении поля {field}: {e}")
            conn.rollback()  # Откатываем изменения при ошибке
            return False
        finally:
            conn.close()

    def update_film_genre(self, film_id, genre_name):
        """Обновление жанра аниме по названию.

        1. Сначала находим ID жанра по его названию
        2. Затем обновляем запись аниме с этим ID
        3. Проверяем существование жанра перед обновлением
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # Ищем ID жанра по названию
            cursor.execute('SELECT id FROM genres WHERE title = ?', (genre_name,))
            result = cursor.fetchone()  # Получаем одну запись
            """Ой, а тут можно скорее всего меня и на ошибке поймать."""

            if not result:
                print(f"Жанр '{genre_name}' не найден")
                return False  # Возвращаем False если жанр не найден

            genre_id = result[0]  # Получаем ID жанра
            # Обновляем запись аниме
            cursor.execute('UPDATE animes SET genre = ? WHERE id = ?', (genre_id, film_id))
            conn.commit()  # Сохраняем изменения
            return cursor.rowcount > 0  # True если обновление прошло успешно

        except Exception as e:
            print(f"Ошибка при обновлении жанра: {e}")
            conn.rollback()  # Откатываем изменения при ошибке
            return False
        finally:
            conn.close()


class Ferst(QDialog):
    """Диалоговое окно приветствия с политикой компании.

    Это первое окно, которое видит пользователь при запуске приложения.
    Реализует нестандартную логику принятия решения:
    - "Я мудрый человек" немедленно закрывает приложение
    - Согласие с политикой разрешает вход в основное приложение
    - Отказ от выбора также приводит к закрытию приложения
    """

    def __init__(self):
        """Инициализация диалогового окна приветствия."""
        super().__init__()  # Вызываем конструктор родительского класса QDialog
        self.initUI()  # Вызываем метод инициализации интерфейса

    def initUI(self):
        """Инициализация пользовательского интерфейса диалога."""
        # Устанавливаем размер и позицию окна (x, y, ширина, высота)
        self.setGeometry(400, 400, 450, 200)
        self.setWindowTitle('Добро пожаловать!')  # Устанавливаем заголовок окна
        self.setModal(True)  # Делаем окно модальным (нельзя взаимодействовать с другими окнами пока это открыто)

        layout = QVBoxLayout()  # Создаем вертикальный компоновщик для размещения виджетов

        # Создаем два радио-кнопки для выбора пользователя
        self.radio_wise = QRadioButton("Я мудрый человек")  # Первая опция
        self.radio_agree = QRadioButton("Я согласен с политикой компании")  # Вторая опция

        # Добавляем радио-кнопки в компоновщик
        layout.addWidget(self.radio_wise)
        layout.addWidget(self.radio_agree)

        # Создаем метку с ссылкой на политику компании
        # HTML-тег <a> создает кликабельную ссылку
        policy_label = QLabel(
            'Ознакомится с политикой компании можно по <a href="https://rutube.ru/video/be9b5aece2911aecc68fa03942e25bac/?r=wd">ссылке</a>.')
        policy_label.setOpenExternalLinks(True)  # Разрешаем открытие ссылок во внешнем браузере
        # Разрешаем взаимодействие с текстом как с веб-браузером
        policy_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        layout.addWidget(policy_label)  # Добавляем метку в компоновщик

        # Создаем кнопку подтверждения
        self.ok_button = QPushButton("Окей")
        # Привязываем обработчик нажатия кнопки к методу process_choice
        self.ok_button.clicked.connect(self.process_choice)
        layout.addWidget(self.ok_button)  # Добавляем кнопку в компоновщик

        # Устанавливаем компоновщик для диалогового окна
        self.setLayout(layout)

    def process_choice(self):
        """Обработка выбора пользователя при нажатии кнопки "Окей".

        Логика обработки:
        1. Если ничего не выбрано - закрываем приложение
        2. Если выбрано "Я мудрый человек" - закрываем приложение
        3. Если согласен с политикой - закрываем диалог и открываем основное окно
        """
        # Проверяем, выбрана ли хотя бы одна опция
        if not self.radio_wise.isChecked() and not self.radio_agree.isChecked():
            sys.exit()  # Завершаем приложение если ничего не выбрано
        # Проверяем, выбрана ли опция "Я мудрый человек"
        elif self.radio_wise.isChecked():
            sys.exit()  # Завершаем приложение
        else:
            # Если согласен с политикой, закрываем диалог с кодом Accepted
            self.accept()


class IamRobot(QDialog):
    """Диалог проверки 'Я не робот' для просмотра аниме онлайн.

    Этот диалог открывается при попытке просмотра аниме.
    Эмулирует защиту от ботов, хотя технически проверяет только галочку.
    При подтверждении:
    1. Увеличивает счетчик просмотров в базе данных
    2. Формирует поисковый запрос для Google
    3. Открывает результаты поиска в веб-браузере
    """

    def __init__(self, parent=None, db_manager=None, film_id=None, film_title=None):
        """Инициализация диалога с параметрами аниме.

        parent - родительское окно (для модальности)
        db_manager - менеджер базы данных для обновления счетчика просмотров
        film_id - ID аниме для увеличения просмотров
        film_title - название аниме для формирования поискового запроса
        """
        super().__init__(parent)  # Вызываем конструктор родительского класса
        self.db_manager = db_manager  # Сохраняем ссылку на менеджер БД
        self.film_id = film_id  # Сохраняем ID аниме
        self.film_title = film_title  # Сохраняем название аниме
        self.initUI()  # Инициализируем интерфейс

    def initUI(self):
        """Инициализация пользовательского интерфейса диалога."""
        # Устанавливаем размер и позицию окна
        self.setGeometry(400, 400, 300, 150)
        self.setWindowTitle('Подтверждение')  # Заголовок окна

        layout = QVBoxLayout()  # Вертикальный компоновщик

        # Создаем чекбокс для подтверждения "Я не робот"
        self.robot_checkbox = QCheckBox("Я не робот.")
        layout.addWidget(self.robot_checkbox)  # Добавляем в компоновщик

        # Создаем кнопку подтверждения
        self.ok_button = QPushButton("Окей")
        # Привязываем обработчик нажатия к методу process_verification
        self.ok_button.clicked.connect(self.process_verification)
        layout.addWidget(self.ok_button)  # Добавляем в компоновщик

        # Устанавливаем компоновщик для диалога
        self.setLayout(layout)

    def process_verification(self):
        """Обработка подтверждения пользователя.

        Если галочка установлена:
        1. Увеличиваем счетчик просмотров в БД
        2. Формируем поисковый запрос и открываем его в браузере
        3. Закрываем диалог с кодом Accepted
        Если галочка не установлена - закрываем приложение
        """
        if self.robot_checkbox.isChecked():
            try:
                # Увеличиваем счетчик просмотров для выбранного аниме
                success = self.db_manager.increment_views(self.film_id)
                if success:
                    # Печатаем сообщение в консоль для отладки
                    print(f"Просмотры для аниме {self.film_id} увеличены на 1")

                # Формируем поисковый запрос для Google
                search_query = f"{self.film_title} аниме смотреть онлайн"
                # Открываем результаты поиска в веб-браузере
                # Внимание: в URL есть лишние пробелы (ошибка в коде)
                webbrowser.open(f"  https://www.google.com/search?q={search_query}")
                self.accept()  # Закрываем диалог с кодом Accepted

            except Exception as e:
                # При ошибке печатаем сообщение и показываем ошибку
                print(f"Ошибка при обработке просмотра: {e}")
                self.show_error()  # Показываем диалог ошибки
        else:
            # Если галочка не установлена, завершаем приложение
            sys.exit()

    def show_error(self):
        """Отображение диалога ошибки при неправильной проверке."""
        # Создаем диалоговое окно сообщения
        error_dialog = QMessageBox(self)  # Указываем родительское окно для модальности
        error_dialog.setWindowTitle("Ошибка")  # Заголовок диалога
        error_dialog.setText("Неправильно, давай еще раз.")  # Текст сообщения
        error_dialog.exec()  # Показываем диалог и ждем закрытия


class Addd(QDialog):
    """Диалог добавления нового аниме в базу данных.

    Содержит поля для ввода всех необходимых данных:
    - Название (обязательное поле)
    - Год выпуска (только цифры)
    - Жанр (выбор из существующих в базе данных)
    - Количество эпизодов (только цифры)

    Проводит валидацию на клиентской стороне перед сохранением в базу данных.
    """

    def __init__(self, parent=None, db_manager=None):
        """Инициализация диалога добавления аниме."""
        super().__init__(parent)  # Конструктор родительского класса
        self.db_manager = db_manager  # Сохраняем менеджер базы данных
        self.initUI()  # Инициализируем интерфейс

    def initUI(self):
        """Инициализация пользовательского интерфейса диалога."""
        # Устанавливаем размер и позицию
        self.setGeometry(400, 400, 400, 300)
        self.setWindowTitle('Добавить аниме')  # Заголовок

        layout = QVBoxLayout()  # Вертикальный компоновщик

        # Поле для ввода названия аниме
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Введите название аниме...")  # Подсказка в поле
        layout.addWidget(QLabel("Название аниме:"))  # Метка для поля
        layout.addWidget(self.title_input)  # Само поле ввода

        # Поле для ввода года выпуска
        self.year_input = QLineEdit()
        self.year_input.setPlaceholderText("Например: 2020")  # Пример ввода
        layout.addWidget(QLabel("Год выпуска:"))
        layout.addWidget(self.year_input)

        # Выпадающий список для выбора жанра
        self.genre_combo = QComboBox()
        # Получаем все жанры из базы данных
        genres = self.db_manager.get_all_genres()
        # Заполняем комбо-бокс данными из базы
        for genre_id, genre_name in genres:
            # addItem(text, userData) - userData будет хранить ID жанра
            self.genre_combo.addItem(genre_name, genre_id)
        layout.addWidget(QLabel("Жанр:"))
        layout.addWidget(self.genre_combo)

        # Поле для ввода количества эпизодов
        self.duration_input = QLineEdit()
        self.duration_input.setPlaceholderText("Например: 12 (эпизодов)")
        layout.addWidget(QLabel("Количество эпизодов:"))
        layout.addWidget(self.duration_input)

        # Кнопка подтверждения
        self.ok_button = QPushButton("Окей")
        # Привязываем обработчик к методу process_input
        self.ok_button.clicked.connect(self.process_input)
        layout.addWidget(self.ok_button)

        # Устанавливаем компоновщик
        self.setLayout(layout)

    def process_input(self):
        """Обработка введенных данных при нажатии кнопки "Окей".

        Проводит валидацию:
        1. Проверяет, что название не пустое
        2. Проверяет, что год состоит только из цифр
        3. Проверяет, что количество эпизодов состоит только из цифр
        4. Пытается добавить аниме в базу данных

        При ошибке вызывает метод show_error()
        """
        try:
            # Получаем и очищаем значения из полей ввода
            title = self.title_input.text().strip()
            year = self.year_input.text().strip()
            genre_id = self.genre_combo.currentData()  # Получаем ID жанра (userData)
            duration = self.duration_input.text().strip()

            # Валидация данных
            if not title:
                raise Exception("Название не может быть пустым")
            if not year.isdigit():  # Проверяем, что год состоит только из цифр
                raise Exception("Год должен быть числом")
            if not duration.isdigit():  # Проверяем, что количество эпизодов - число
                raise Exception("Количество эпизодов должно быть числом")

            # Пытаемся добавить аниме в базу данных
            if not self.db_manager.add_film(title, int(year), genre_id, int(duration)):
                raise Exception("Ошибка при добавлении")

            self.accept()  # Если все успешно, закрываем диалог с кодом Accepted

        except Exception:
            # При любой ошибке показываем диалог ошибки
            self.show_error()

    def show_error(self):
        """Отображение диалога ошибки при некорректных данных."""
        error_dialog = QMessageBox(self)
        error_dialog.setWindowTitle("Ошибка")
        error_dialog.setText("Неправильно, давай еще раз.")  # Стандартное сообщение об ошибке
        error_dialog.exec()


class Delit(QDialog):
    """Диалог удаления аниме из базы данных.

    Запрашивает ID аниме для удаления.
    Используется в двух сценариях:
    1. Когда пользователь не выбрал аниме в таблице
    2. Когда нужно удалить аниме по конкретному ID
    """

    def __init__(self, parent=None, db_manager=None):
        """Инициализация диалога удаления аниме."""
        super().__init__(parent)
        self.db_manager = db_manager  # Сохраняем менеджер базы данных
        self.initUI()

    def initUI(self):
        """Инициализация пользовательского интерфейса диалога."""
        self.setGeometry(400, 400, 300, 150)
        self.setWindowTitle('Удалить аниме')

        layout = QVBoxLayout()

        # Поле ввода для ID аниме
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("ID аниме...")  # Подсказка
        layout.addWidget(QLabel("Введите ID аниме для удаления:"))
        layout.addWidget(self.input_field)

        # Кнопка подтверждения
        self.ok_button = QPushButton("Окей")
        self.ok_button.clicked.connect(self.process_input)  # Привязываем обработчик
        layout.addWidget(self.ok_button)

        self.setLayout(layout)

    def process_input(self):
        """Обработка введенного ID при нажатии кнопки "Окей".

        Проводит валидацию:
        1. Проверяет, что ID состоит только из цифр
        2. Пытается удалить аниме с этим ID из базы данных

        При ошибке вызывает метод show_error()
        """
        try:
            film_id = self.input_field.text().strip()  # Получаем и очищаем ID

            # Валидация: ID должен быть числом
            if not film_id.isdigit():
                raise Exception("ID должен быть числом")

            # Пытаемся удалить аниме из базы
            if not self.db_manager.delete_film(int(film_id)):
                raise Exception("Аниме не найдено")  # Если запись не удалена, значит её не существовало

            self.accept()  # Закрываем диалог при успехе

        except Exception:
            self.show_error()  # Показываем ошибку при неудаче

    def show_error(self):
        """Отображение диалога ошибки при некорректном ID."""
        error_dialog = QMessageBox(self)
        error_dialog.setWindowTitle("Ошибка")
        error_dialog.setText("Неправильно, давай еще раз.")
        error_dialog.exec()


class BigInterfeis(QWidget):
    """Главное окно приложения - отображает интерфейс управления аниме.

    Это основное окно приложения, которое содержит:
    - Меню для управления данными
    - Панель фильтров для поиска и сортировки
    - Таблицу с списком аниме
    - Панель с постером выбранного аниме
    - Кнопки для действий с выделенным аниме

    Использует архитектуру MVC (Model-View-Controller), во какие словечки знаю:
    - Model: DatabaseManager (работает с данными)
    - View: BigInterfeis (отображает интерфейс)
    - Controller: BigCod (обрабатывает логику)
    """

    def __init__(self, controller):
        """Инициализация главного окна.

        controller - экземпляр класса BigCod, который обрабатывает логику
        """
        super().__init__()  # Конструктор родительского класса QWidget
        self.controller = controller
        self.initUI()  # Инициализируем интерфейс
        # Загружаем данные с небольшой задержкой после создания интерфейса
        # Это нужно, чтобы интерфейс успел отобразиться перед загрузкой данных
        QTimer.singleShot(100, self.controller.load_initial_data)

    def initUI(self):
        """Инициализация пользовательского интерфейса главного окна."""
        # Устанавливаем размер и позицию (x, y, ширина, высота)
        self.setGeometry(100, 100, 1400, 700)
        self.setWindowTitle('Управление аниме')  # Заголовок окна

        main_layout = QHBoxLayout()  # Горизонтальный компоновщик для разделения на левую и правую части

        # Левая часть: меню, фильтры, таблица, кнопки
        left_layout = QVBoxLayout()
        left_layout.addWidget(self.create_menu_bar())  # Меню вверху
        left_layout.addLayout(self.create_filter_panel())  # Панель фильтров
        left_layout.addLayout(self.create_table_panel())  # Таблица с данными
        left_layout.addLayout(self.create_button_panel())  # Панель кнопок

        # Правая часть: отображение постера
        right_layout = QVBoxLayout()
        right_layout.addWidget(self.create_poster_panel())  # Панель с постером

        # Добавляем левую и правую части в главный компоновщик
        # 70% ширины для левой части, 30% для правой
        main_layout.addLayout(left_layout, 70)
        main_layout.addLayout(right_layout, 30)

        # Устанавливаем главный компоновщик для окна
        self.setLayout(main_layout)

    def create_menu_bar(self):
        """Создание меню с операциями управления.

        Создает строку меню с одним пунктом "Изменить", который содержит:
        - Добавить аниме
        - Удалить аниме
        - Изменить или добавить картинку

        Каждый пункт меню привязан к соответствующему методу контроллера.
        """
        menu_bar = QMenuBar(self)  # Создаем панель меню

        # Создаем меню "Изменить"
        edit_menu = QMenu("Изменить", self)

        # Пункт "Добавить аниме"
        add_action = QAction("Добавить аниме", self)
        # Привязываем действие к методу контроллера
        add_action.triggered.connect(self.controller.open_add_dialog)
        edit_menu.addAction(add_action)  # Добавляем действие в меню

        # Пункт "Удалить аниме"
        delete_action = QAction("Удалить аниме", self)
        delete_action.triggered.connect(self.controller.open_delete_dialog)
        edit_menu.addAction(delete_action)

        # Пункт "Изменить или добавить картинку"
        change_poster_action = QAction("Изменить или добавить картинку", self)
        change_poster_action.triggered.connect(self.controller.change_poster)
        edit_menu.addAction(change_poster_action)

        # Добавляем меню "Изменить" в панель меню
        menu_bar.addMenu(edit_menu)

        return menu_bar  # Возвращаем созданную панель меню

    def create_filter_panel(self):
        """Создание панели фильтров для поиска и сортировки.

        Содержит:
        - Поиск по названию (реагирует на каждый символ)
        - Фильтр по жанру (выпадающий список)
        - Фильтр по году (поле ввода)
        - Фильтр по количеству эпизодов (группировка)
        - Сортировка по популярности

        Все фильтры применяются мгновенно при изменении значения (без кнопки "Применить").
        """
        filter_layout = QVBoxLayout()  # Вертикальный компоновщик для фильтров

        # === Поиск по названию ===
        search_layout = QHBoxLayout()  # Горизонтальный компоновщик для поиска
        self.search_input = QLineEdit()
        # Подсказка для пользователя
        self.search_input.setPlaceholderText("Введите первые буквы названия...")
        # При изменении текста вызываем метод apply_filters контроллера
        self.search_input.textChanged.connect(self.controller.apply_filters)
        search_layout.addWidget(QLabel("Поиск по названию:"))  # Метка
        search_layout.addWidget(self.search_input)  # Поле ввода
        search_layout.addStretch()  # Растягиваем оставшееся пространство
        filter_layout.addLayout(search_layout)  # Добавляем в основной компоновщик

        # === Группа фильтров ===
        filters_layout = QHBoxLayout()  # Горизонтальный компоновщик для группы фильтров

        # --- Фильтр по жанру ---
        self.genre_combo = QComboBox()
        # Добавляем стандартный вариант "Все жанры" с пустыми данными
        self.genre_combo.addItem("Все жанры", None)
        # При изменении выбранного жанра применяем фильтры
        self.genre_combo.currentIndexChanged.connect(self.controller.apply_filters)
        filters_layout.addWidget(QLabel("Жанр:"))
        filters_layout.addWidget(self.genre_combo)

        # --- Фильтр по году ---
        self.year_input = QLineEdit()
        self.year_input.setPlaceholderText("Введите год...")
        # При изменении текста применяем фильтры
        self.year_input.textChanged.connect(self.controller.apply_filters)
        filters_layout.addWidget(QLabel("Год:"))
        filters_layout.addWidget(self.year_input)

        # --- Фильтр по количеству эпизодов ---
        self.duration_combo = QComboBox()
        # Стандартный вариант - без фильтра
        self.duration_combo.addItem("Любая", None)
        # Варианты фильтрации по длительности
        self.duration_combo.addItem("До 28 эпизодов", "short")
        self.duration_combo.addItem("29-48 эпизодов", "medium")
        self.duration_combo.addItem("Более 48 эпизодов", "long")
        # При изменении применяем фильтры
        self.duration_combo.currentIndexChanged.connect(self.controller.apply_filters)
        filters_layout.addWidget(QLabel("Количество эпизодов:"))
        filters_layout.addWidget(self.duration_combo)

        # --- Сортировка по популярности ---
        self.popularity_combo = QComboBox()
        self.popularity_combo.addItem("Без сортировки", None)
        self.popularity_combo.addItem("Сначала популярные", "popular")
        self.popularity_combo.addItem("Сначала не популярные", "unpopular")
        # При изменении применяем фильтры
        self.popularity_combo.currentIndexChanged.connect(self.controller.apply_filters)
        filters_layout.addWidget(QLabel("Сортировать по:"))
        filters_layout.addWidget(self.popularity_combo)
        filters_layout.addStretch()  # Растягиваем оставшееся пространство

        filter_layout.addLayout(filters_layout)  # Добавляем группу фильтров в основной компоновщик

        return filter_layout  # Возвращаем созданный компоновщик

    def create_table_panel(self):
        """Создание таблицы для отображения списка аниме.

        Таблица содержит 6 столбцов:
        1. ID (не редактируется)
        2. Название (редактируется)
        3. Год (редактируется)
        4. Жанр (редактируется)
        5. Эпизоды (редактируется)
        6. Просмотры (редактируется)

        Поддерживает:
        - Редактирование на месте по двойному клику и Enter
        - Выделение целых строк
        - Автоматическое обновление постера при смене выделения
        """
        table_layout = QVBoxLayout()  # Вертикальный компоновщик для таблицы

        # Создаем таблицу с 0 строк и 6 столбцами
        self.table = QTableWidget(0, 6)
        # Устанавливаем заголовки столбцов
        self.table.setHorizontalHeaderLabels(["ID", "Название", "Год", "Жанр", "Эпизоды", "Просмотры"])

        # Настраиваем режимы редактирования:
        # - DoubleClicked: редактирование по двойному клику
        # - EditKeyPressed: редактирование по нажатию клавиши F2 или Enter
        self.table.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked |
                                   QTableWidget.EditTrigger.EditKeyPressed)

        # Привязываем обработчик изменения ячейки к методу контроллера
        self.table.itemChanged.connect(self.controller.on_item_changed)

        # Настраиваем выделение:
        # SelectRows - выделять целые строки
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        # SingleSelection - можно выделить только одну строку
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        # При изменении выделения обновляем постер
        self.table.itemSelectionChanged.connect(self.on_selection_changed)

        table_layout.addWidget(self.table)  # Добавляем таблицу в компоновщик
        return table_layout  # Возвращаем компоновщик

    def create_poster_panel(self):
        """Создание панели для отображения постера выбранного аниме.

        Панель содержит:
        - Заголовок "Постер аниме"
        - Место для отображения изображения (300x450 пикселей)
        - Название аниме под постером

        По умолчанию показывает текст "Постер не выбран" вместо изображения.
        """
        poster_widget = QWidget()  # Создаем виджет-контейнер
        poster_layout = QVBoxLayout()  # Вертикальный компоновщик

        # Заголовок панели
        poster_title = QLabel("Постер аниме")
        poster_title.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Выравнивание по центру
        # Стиль: жирный шрифт, размер 14px, отступы
        poster_title.setStyleSheet("font-weight: bold; font-size: 14px; margin: 10px;")
        poster_layout.addWidget(poster_title)

        # Метка для отображения постера
        self.poster_label = QLabel()
        self.poster_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Минимальный размер для постера
        self.poster_label.setMinimumSize(300, 450)
        # Стиль фона (светло-серый)
        self.poster_label.setStyleSheet("background-color: #f8f9fa;")
        # Текст по умолчанию
        self.poster_label.setText("Постер не выбран")
        poster_layout.addWidget(self.poster_label)

        # Метка для названия аниме под постером
        self.poster_film_title = QLabel("")
        self.poster_film_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        poster_layout.addWidget(self.poster_film_title)

        poster_layout.addStretch()  # Растягиваем оставшееся пространство
        poster_widget.setLayout(poster_layout)  # Устанавливаем компоновщик для виджета
        return poster_widget  # Возвращаем виджет панели

    def create_button_panel(self):
        """Создание панели кнопок управления в нижней части окна.

        Содержит три кнопки:
        1. "Смотреть онлайн" - открывает диалог подтверждения и затем поиск в Google
        2. "Стереть настройки" - сбрасывает все фильтры к значениям по умолчанию
        3. "Закрыть" - закрывает приложение

        Кнопки расположены слева, с растягивающимся пространством перед кнопкой "Закрыть".
        """
        button_layout = QHBoxLayout()  # Горизонтальный компоновщик для кнопок

        # Кнопка "Смотреть онлайн"
        self.watch_button = QPushButton("Смотреть онлайн")
        # Привязываем обработчик к методу контроллера
        self.watch_button.clicked.connect(self.controller.open_watch_dialog)

        # Кнопка "Стереть настройки"
        self.clear_settings_button = QPushButton("Стереть настройки")
        self.clear_settings_button.clicked.connect(self.controller.clear_settings)

        # Кнопка "Закрыть"
        self.close_button = QPushButton("Закрыть")
        # Стандартное закрытие окна
        self.close_button.clicked.connect(self.close)

        # Добавляем кнопки в компоновщик
        button_layout.addWidget(self.watch_button)
        button_layout.addWidget(self.clear_settings_button)
        button_layout.addStretch()  # Растягиваем пространство
        button_layout.addWidget(self.close_button)

        return button_layout  # Возвращаем компоновщик

    def on_selection_changed(self):
        """Обработчик изменения выделенной строки в таблице.

        Когда пользователь выбирает другую строку в таблице:
        1. Получаем информацию о выбранном аниме (ID и название)
        2. Если аниме выбрано, обновляем постер через контроллер
        """
        selected_film_info = self.get_selected_film_info()
        if selected_film_info:
            film_id, film_title = selected_film_info
            # Обращаемся к контроллеру для обновления постера
            self.controller.update_poster_for_selected_film(film_id, film_title)

    def get_search_text(self):
        """Получение текста для поиска по названию.

        Возвращает очищенный и приведенный к нижнему регистру текст из поля поиска.
        """
        return self.search_input.text().strip().lower()

    def get_selected_genre(self):
        """Получение выбранного жанра из комбо-бокса.

        Возвращает текст выбранного жанра (не ID!), например "Экшен" или "Все жанры".
        """
        return self.genre_combo.currentText()

    def get_year_text(self):
        """Получение текста для фильтра по году.

        Возвращает очищенный текст из поля ввода года.
        """
        return self.year_input.text().strip()

    def get_duration_filter(self):
        """Получение выбранного фильтра по длительности.

        Возвращает пользовательские данные (userData) выбранного элемента:
        None - без фильтра
        "short" - до 28 эпизодов
        "medium" - 29-48 эпизодов
        "long" - более 48 эпизодов
        """
        return self.duration_combo.currentData()

    def get_popularity_filter(self):
        """Получение выбранной сортировки по популярности.

        Возвращает пользовательские данные:
        None - без сортировки
        "popular" - сначала популярные
        "unpopular" - сначала непопулярные
        """
        return self.popularity_combo.currentData()

    def set_genres(self, genres):
        """Установка списка жанров в комбо-бокс жанров.

        genres - список кортежей [(id1, 'Жанр1'), (id2, 'Жанр2'), ...]

        Метод:
        1. Очищает текущий список
        2. Добавляет стандартный вариант "Все жанры"
        3. Добавляет все жанры из базы данных
        4. Для каждого жанра сохраняет ID в userData

        Это предотвращает дублирование жанров, так как данные берутся напрямую из базы.
        """
        self.genre_combo.clear()  # Очищаем текущие значения
        # Добавляем стандартный вариант "Все жанры" с пустыми данными
        self.genre_combo.addItem("Все жанры", None)
        # Добавляем жанры из базы данных
        for genre_id, genre_name in genres:
            self.genre_combo.addItem(genre_name, genre_id)  # text, userData=ID

    def display_films(self, films):
        """Отображение списка аниме в таблице.

        films - список кортежей с данными об аниме

        Метод:
        1. Блокирует сигналы изменения таблицы для предотвращения рекурсивных вызовов
        2. Удаляет все текущие строки
        3. Создает новые строки с данными
        4. Настраивает редактируемость ячеек (ID нельзя редактировать)
        5. Восстанавливает выделение на предыдущей или первой строке
        6. Автоматически подгоняет ширину столбцов

        Это обеспечивает плавное обновление интерфейса без мерцания.
        """
        current_row = self.table.currentRow()  # Сохраняем текущее выделение

        # Блокируем сигналы для предотвращения лишних обновлений
        self.table.blockSignals(True)
        self.table.setRowCount(0)  # Удаляем все строки
        self.table.setRowCount(len(films))  # Устанавливаем новое количество строк

        # Заполняем таблицу данными
        for row, film in enumerate(films):
            for col, value in enumerate(film):
                # Создаем элемент таблицы со значением
                item = QTableWidgetItem(str(value))
                # Для столбца ID (0) отключаем редактирование
                if col == 0:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                # Для остальных столбцов разрешаем редактирование
                else:
                    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                # Устанавливаем элемент в таблицу
                self.table.setItem(row, col, item)

        # Разблокируем сигналы
        self.table.blockSignals(False)
        # Автоматически подгоняем ширину столбцов
        self.table.resizeColumnsToContents()

        # Восстанавливаем выделение
        if 0 <= current_row < self.table.rowCount():
            # Если предыдущая строка существует, выделяем её
            self.table.selectRow(current_row)
        elif self.table.rowCount() > 0:
            # Иначе выделяем первую строку
            self.table.selectRow(0)

    def clear_filter_settings(self):
        """Сброс всех фильтров к значениям по умолчанию.

        Метод:
        1. Блокирует сигналы изменений для предотвращения множественных обновлений
        2. Очищает поле поиска
        3. Устанавливает первый вариант в комбо-боксах ("Все жанры", "Любая", "Без сортировки")
        4. Очищает поле года
        5. Разблокирует сигналы

        Блокировка сигналов необходима для предотвращения мерцания интерфейса
        и множественных запросов к базе данных при сбросе фильтров.
        """
        # Блокируем сигналы
        self.search_input.blockSignals(True)
        self.genre_combo.blockSignals(True)
        self.year_input.blockSignals(True)
        self.duration_combo.blockSignals(True)
        self.popularity_combo.blockSignals(True)

        # Сбрасываем значения
        self.search_input.clear()  # Очищаем поле поиска
        self.genre_combo.setCurrentIndex(0)  # "Все жанры"
        self.year_input.clear()  # Очищаем поле года
        self.duration_combo.setCurrentIndex(0)  # "Любая"
        self.popularity_combo.setCurrentIndex(0)  # "Без сортировки"

        # Разблокируем сигналы
        self.search_input.blockSignals(False)
        self.genre_combo.blockSignals(False)
        self.year_input.blockSignals(False)
        self.duration_combo.blockSignals(False)
        self.popularity_combo.blockSignals(False)

    def update_poster_display(self, film_title="", poster_data=None):
        """Отображение постера в правой панели.

        film_title - название аниме для отображения под постером
        poster_data - бинарные данные изображения из базы данных

        Метод:
        1. Если есть данные постера и название:
           - Загружает изображение из бинарных данных
           - Масштабирует его с сохранением пропорций
           - Отображает в метке
           - Показывает название под постером
        2. Если данных нет:
           - Показывает текст "Постер не выбран"
           - Очищает название

        Обрабатывает ошибки загрузки изображения.
        """
        if poster_data and film_title:
            try:
                # Создаем QImage и загружаем данные
                image = QImage()
                image.loadFromData(poster_data)
                # Создаем QPixmap из QImage
                pixmap = QPixmap.fromImage(image)
                # Масштабируем изображение с сохранением пропорций
                scaled_pixmap = pixmap.scaled(300, 450, Qt.AspectRatioMode.KeepAspectRatio,
                                              Qt.TransformationMode.SmoothTransformation)
                # Устанавливаем изображение в метку
                self.poster_label.setPixmap(scaled_pixmap)
                # Устанавливаем название под постером
                self.poster_film_title.setText(film_title)
            except Exception as e:
                # При ошибке показываем сообщение об ошибке
                print(f"Ошибка при загрузке постера: {e}")
                self.poster_label.setText("Ошибка загрузки\nпостера")
                self.poster_film_title.setText("")
        else:
            # Если данных нет, показываем заглушку
            self.poster_label.setText("Постер не выбран")
            self.poster_film_title.setText("")

    def get_selected_film_info(self):
        """Получение ID и названия выбранного аниме.

        Возвращает кортеж (film_id, film_title) для выделенной строки
        или (None, None) если ничего не выделено или возникла ошибка.

        Используется для:
        - Отображения постера
        - Удаления аниме
        - Просмотра онлайн
        - Изменения постера
        """
        current_row = self.table.currentRow()  # Получаем индекс выделенной строки
        if current_row >= 0:
            try:
                # Получаем ID из первого столбца (0) и преобразуем в число
                film_id = int(self.table.item(current_row, 0).text())
                # Получаем название из второго столбца (1)
                film_title = self.table.item(current_row, 1).text()
                return film_id, film_title  # Возвращаем кортеж
            except (AttributeError, ValueError):
                # Если элемент отсутствует или данные некорректны
                return None, None
        return None, None  # Если ничего не выделено

    def has_selected_film(self):
        """Проверка наличия выделенного аниме.

        Возвращает True если есть выделенная строка в таблице,
        False в противном случае.

        Используется для проверки перед операциями, требующими выбора аниме.
        """
        return self.table.currentRow() >= 0

    def show_error(self, message="Неправильно, давай еще раз."):
        """Отображение сообщения об ошибке.

        Создает и показывает стандартный диалог QMessageBox с указанным сообщением.
        Используется для отображения ошибок валидации и других проблем.
        """
        error_dialog = QMessageBox(self)  # Создаем диалог с родительским окном
        error_dialog.setWindowTitle("Ошибка")  # Заголовок
        error_dialog.setText(message)  # Текст сообщения
        error_dialog.exec()  # Показываем диалог модально

    def show_info(self, title, message):
        """Отображение информационного сообщения.

        Создает и показывает диалог с заголовком и сообщением.
        Используется для уведомлений об успешных операциях.
        """
        info_dialog = QMessageBox(self)
        info_dialog.setWindowTitle(title)  # Заголовок из параметра
        info_dialog.setText(message)  # Сообщение из параметра
        info_dialog.exec()


class BigCod:
    """Контроллер главного окна - реализует бизнес-логику приложения.

    Этот класс является связующим звеном между моделью (DatabaseManager)
    и представлением (BigInterfeis). Он обрабатывает действия пользователя
    и координирует работу с базой данных.

    Основные обязанности:
    - Обработка фильтров и сортировки
    - Редактирование данных в таблице
    - Открытие диалоговых окон
    - Обновление постера
    - Удаление и добавление записей
    """

    def __init__(self):
        """Инициализация контроллера.

        Создает экземпляры:
        - DatabaseManager для работы с данными
        - BigInterfeis для отображения интерфейса

        Инициализирует кеш для хранения всех аниме (self.all_films).
        """
        self.db_manager = DatabaseManager()  # Создаем менеджер базы данных
        self.view = BigInterfeis(self)  # Создаем интерфейс, передавая себя как контроллер
        self.all_films = []  # Кеш для хранения всех аниме

    def show(self):
        """Отображение главного окна.

        Просто вызывает метод show() у интерфейса.
        """
        self.view.show()

    def load_initial_data(self):
        """Загрузка начальных данных при запуске приложения.

        Вызывает метод refresh_table() для получения данных из базы
        и обновления интерфейса. Выполняется с небольшой задержкой после создания UI.
        """
        self.refresh_table()

    def refresh_table(self):
        """Обновление данных в таблице и фильтрах.

        1. Получает все аниме из базы данных
        2. Получает все жанры из базы данных
        3. Устанавливает жанры в комбо-бокс интерфейса
        4. Применяет текущие фильтры для отображения данных

        Обрабатывает ошибки и показывает сообщение об ошибке при проблемах.
        """
        try:
            # Получаем все аниме из базы и сохраняем в кеш
            self.all_films = self.db_manager.get_all_films()
            # Получаем все жанры из базы
            genres = self.db_manager.get_all_genres()
            # Устанавливаем жанры в интерфейс (без дублирования)
            self.view.set_genres(genres)
            # Применяем текущие фильтры
            self.apply_filters()
        except Exception as e:
            print(f"Ошибка при обновлении таблицы: {e}")
            self.view.show_error()

    def apply_filters(self):
        """Применение всех фильтров к списку аниме.

        Порядок применения фильтров:
        1. Поиск по началу названия
        2. Фильтр по жанру
        3. Фильтр по году
        4. Группировка по длительности
        5. Сортировка по популярности

        После применения фильтров:
        - Отображает результаты в таблице
        - Обновляет постер для первого элемента

        Использует кеш self.all_films для фильтрации без обращения к базе.
        """
        try:
            # Начинаем с копии всех аниме
            filtered_films = self.all_films.copy()

            # === 1. Фильтр по названию ===
            search_text = self.view.get_search_text()
            if search_text:
                # Оставляем только аниме, название которых начинается с search_text
                filtered_films = [film for film in filtered_films
                                  if film[1].lower().startswith(search_text)]

            # === 2. Фильтр по жанру ===
            selected_genre = self.view.get_selected_genre()
            if selected_genre != "Все жанры":
                # Оставляем только аниме с выбранным жанром (столбец 3)
                filtered_films = [film for film in filtered_films if film[3] == selected_genre]

            # === 3. Фильтр по году ===
            year_text = self.view.get_year_text()
            if year_text and year_text.isdigit():
                year = int(year_text)
                # Оставляем только аниме с указанным годом (столбец 2)
                filtered_films = [film for film in filtered_films if film[2] == year]

            # === 4. Фильтр по длительности ===
            duration_filter = self.view.get_duration_filter()
            # Столбец 4 содержит количество эпизодов
            if duration_filter == "short":
                filtered_films = [film for film in filtered_films if film[4] <= 28]
            elif duration_filter == "medium":
                filtered_films = [film for film in filtered_films if 29 <= film[4] <= 48]
            elif duration_filter == "long":
                filtered_films = [film for film in filtered_films if film[4] > 48]

            # === 5. Сортировка по популярности ===
            popularity_filter = self.view.get_popularity_filter()
            if popularity_filter == "popular":
                # Сначала популярные: сортируем по просмотрам (убывание), затем по названию (возрастание)
                filtered_films.sort(key=lambda x: (-int(x[5]), x[1].lower()))
            elif popularity_filter == "unpopular":
                # Сначала непопулярные: сортируем по просмотрам (возрастание), затем по названию
                filtered_films.sort(key=lambda x: (int(x[5]), x[1].lower()))

            # Отображаем отфильтрованные данные в таблице
            self.view.display_films(filtered_films)

            # Если есть результаты, обновляем постер для выделенного аниме
            if filtered_films:
                self.update_poster_for_selected_film()
        except Exception as e:
            print(f"Ошибка при применении фильтров: {e}")
            self.view.show_error()

    def update_poster_for_selected_film(self, film_id=None, film_title=None):
        """Обновление постера для выбранного аниме.

        Если film_id и film_title не переданы:
        - Получает информацию о выделенном аниме из интерфейса
        - Если ничего не выделено, очищает постер

        Если переданы:
        - Получает данные постера из базы данных по film_id
        - Обновляет постер в интерфейсе

        Обрабатывает ошибки и не прерывает работу приложения.
        """
        try:
            # Если ID и название не переданы, получаем их из интерфейса
            if film_id is None or film_title is None:
                film_info = self.view.get_selected_film_info()
                if film_info:
                    film_id, film_title = film_info
                else:
                    # Если ничего не выделено, очищаем постер
                    self.view.update_poster_display()
                    return

            # Получаем бинарные данные постера из базы
            poster_data = self.db_manager.get_film_poster(film_id)
            # Обновляем отображение постера в интерфейсе
            self.view.update_poster_display(film_title, poster_data)

        except Exception as e:
            print(f"Ошибка при обновлении постера: {e}")

    def on_item_changed(self, item):
        """Обработчик изменений в ячейках таблицы.

        Вызывается когда пользователь редактирует ячейку в таблице.
        Определяет:
        - Какое поле было изменено (по номеру столбца)
        - Какой тип данных ожидается
        - Как обновить запись в базе данных

        Особые случаи:
        - Столбец 3 (жанр) требует поиска ID по названию
        - Числовые поля проверяются на соответствие формату

        При ошибке изменения откатываются через refresh_table().
        """
        if not item:
            return  # Если элемент пустой, ничего не делаем

        try:
            row = item.row()  # Получаем номер строки
            column = item.column()  # Получаем номер столбца
            # Получаем ID аниме из первого столбца (0) текущей строки
            film_id = int(self.view.table.item(row, 0).text())
            new_value = item.text()  # Получаем новое значение

            # Сопоставление столбцов с полями базы данных и типами данных
            field_map = {
                1: ("title", str),  # Название - строка
                2: ("year", int),  # Год - число
                3: ("genre", str),  # Жанр - строка (название)
                4: ("duration", int),  # Эпизоды - число
                5: ("prosmotrs", str)  # Просмотры - строка
            }

            # Если столбец не в списке редактируемых, ничего не делаем
            if column not in field_map:
                return

            field_name, field_type = field_map[column]

            # Валидация для числовых полей
            if field_type == int and not new_value.isdigit():
                self.view.show_error(f"Поле должно содержать число")
                self.refresh_table()  # Откатываем изменения
                return

            # Специальная обработка для жанра (поиск ID по названию)
            if column == 3:
                success = self.db_manager.update_film_genre(film_id, new_value)
            else:
                # Для числовых полей преобразуем значение
                if field_type == int:
                    new_value = int(new_value)
                # Обновляем поле в базе
                success = self.db_manager.update_film_field(film_id, field_name, new_value)

            if success:
                # При успехе обновляем кеш всех аниме
                self.all_films = self.db_manager.get_all_films()
            else:
                # При ошибке показываем сообщение и откатываем изменения
                self.view.show_error("Ошибка при сохранении изменений в базу данных")
                self.refresh_table()  # Откатываем изменения

        except Exception as e:
            print(f"Ошибка при изменении элемента: {e}")
            self.view.show_error("Произошла ошибка при сохранении")
            self.refresh_table()  # Откатываем изменения

    def open_add_dialog(self):
        """Открытие диалога добавления аниме.

        1. Создает диалоговое окно Addd
        2. Передает менеджер базы данных
        3. Если диалог закрыт с кодом Accepted, обновляет таблицу
        4. Обрабатывает ошибки создания диалога
        """
        try:
            dialog = Addd(self.view, self.db_manager)  # Создаем диалог с родительским окном
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.refresh_table()  # Обновляем таблицу при успехе
        except Exception as e:
            print(f"Ошибка при открытии диалога добавления: {e}")
            self.view.show_error()

    def open_delete_dialog(self):
        """Открытие диалога удаления аниме.

        Реализует два сценария:
        1. Если в таблице выделена строка:
           - Показывает диалог подтверждения с названием аниме
           - При подтверждении удаляет запись
        2. Если ничего не выделено:
           - Открывает диалог Delit для ввода ID вручную

        При успешном удалении показывает информационное сообщение.
        """
        try:
            if self.view.has_selected_film():
                # Получаем информацию о выделенном аниме
                film_id, film_title = self.view.get_selected_film_info()

                # Показываем диалог подтверждения удаления
                reply = QMessageBox.question(self.view, 'Подтверждение удаления',
                                             f'Вы уверены, что хотите удалить аниме "{film_title}"?',
                                             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

                if reply == QMessageBox.StandardButton.Yes:
                    # Пытаемся удалить аниме
                    if self.db_manager.delete_film(film_id):
                        self.view.show_info("Успех", "Аниме успешно удалено!")
                        self.refresh_table()  # Обновляем таблицу
                    else:
                        raise Exception("Ошибка при удалении аниме")
            else:
                # Если ничего не выделено, открываем диалог для ввода ID
                dialog = Delit(self.view, self.db_manager)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    self.refresh_table()
        except Exception as e:
            print(f"Ошибка при удалении аниме: {e}")
            self.view.show_error()

    def open_watch_dialog(self):
        """Открытие диалога просмотра онлайн.

        1. Проверяет, есть ли выделенное аниме
        2. Если есть - открывает диалог IamRobot
        3. Если нет - показывает ошибку
        4. При подтверждении в диалоге:
           - Увеличивает счетчик просмотров
           - Открывает поиск в Google
           - Обновляет таблицу

        Диалог IamRobot не эмулирует проверку "Я не робот".
        """
        try:
            if self.view.has_selected_film():
                # Получаем информацию о выделенном аниме
                film_id, film_title = self.view.get_selected_film_info()
                # Создаем и показываем диалог просмотра
                dialog = IamRobot(self.view, self.db_manager, film_id, film_title)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    self.refresh_table()  # Обновляем таблицу после просмотра
            else:
                self.view.show_error("Пожалуйста, выберите аниме для просмотра")
        except Exception as e:
            print(f"Ошибка при открытии диалога просмотра: {e}")
            self.view.show_error()

    def change_poster(self):
        """Изменение постера для выбранного аниме.

        1. Проверяет, есть ли выделенное аниме
        2. Открывает системный диалог выбора файла изображения
        3. Проверяет существование файла
        4. Обновляет постер в базе данных
        5. При успехе показывает информационное сообщение
        6. Обновляет таблицу и постер

        Поддерживаемые форматы: png, jpg, jpeg, bmp, gif
        """
        try:
            if not self.view.has_selected_film():
                self.view.show_error("Пожалуйста, выберите аниме для изменения постера")
                return

            # Получаем информацию о выделенном аниме
            film_id, film_title = self.view.get_selected_film_info()

            # Открываем диалог выбора файла
            file_path, _ = QFileDialog.getOpenFileName(
                self.view,
                f"Выберите постер для аниме '{film_title}'",
                "",
                "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)"
            )

            if file_path:
                # Проверяем существование файла
                if not os.path.exists(file_path):
                    self.view.show_error("Файл не найден")
                    return

                # Обновляем постер в базе данных
                if self.db_manager.update_film_poster(film_id, file_path):
                    self.view.show_info("Успех", f"Постер для аниме '{film_title}' успешно обновлен!")
                    self.refresh_table()  # Обновляем таблицу
                else:
                    raise Exception("Ошибка при обновлении постера")

        except Exception as e:
            print(f"Ошибка при изменении постера: {e}")
            self.view.show_error()

    def clear_settings(self):
        """Сброс всех фильтров и настроек.

        1. Вызывает метод clear_filter_settings интерфейса
        2. Применяет фильтры (что отобразит все аниме)
        3. Обрабатывает ошибки

        Это возвращает интерфейс в исходное состояние.
        """
        try:
            self.view.clear_filter_settings()  # Сбрасываем фильтры в интерфейсе
            self.apply_filters()  # Применяем фильтры (отобразятся все аниме)
        except Exception as e:
            print(f"Ошибка при очистке настроек: {e}")
            self.view.show_error()


if __name__ == '__main__':
    """Точка входа в приложение.

    Логика запуска:
    1. Создаем QApplication - основной объект PyQt приложения
    2. Показываем диалог приветствия (Ferst)
    3. Если пользователь согласился с политикой (Accepted):
       - Создаем контроллер BigCod
       - Показываем главное окно
       - Запускаем основной цикл событий
    4. Если пользователь не согласился или закрыл диалог:
       - Завершаем приложение

    Это позволяет показать важную информацию перед использованием приложения
    и реализовать простую защиту от случайного запуска.
    """
    app = QApplication(sys.argv)  # Создаем основное приложение

    # Показываем диалог приветствия
    welcome_dialog = Ferst()
    result = welcome_dialog.exec()

    if result == QDialog.DialogCode.Accepted:
        # Если пользователь согласился, создаем и показываем основное окно
        controller = BigCod()
        controller.show()
        sys.exit(app.exec())  # Запускаем основной цикл событий
    else:
        # Если пользователь не согласился, завершаем приложение
        sys.exit()