import sqlite3


class SQLdatabase:
    def __init__(self):
        self.connection = sqlite3.connect("db.db")
        self.cursor = self.connection.cursor()

    def create_user(self, user_id) -> None:
        """Создания юзера в БД"""
        with self.connection:
            return self.cursor.execute("INSERT INTO users(user_id) VALUES (?)", (user_id,))

    def get_id(self, user_id) -> int:
        """Получение ID"""
        with self.connection:
            return self.cursor.execute("SELECT id FROM users WHERE `user_id` = ?", (user_id,)).fetchone()[0]

    def user_exist(self, user_id) -> bool:
        """Проверка наличия юзера в БД"""
        with self.connection:
            result = self.cursor.execute("SELECT * FROM users WHERE `user_id` = ?", (user_id,)).fetchall()
            return bool(len(result))

    def make_record(self, text, user_id) -> None:
        """Создание записи """
        with self.connection:
            return self.cursor.execute("INSERT INTO notes (owner, text) VALUES (?,?)", (user_id, text))

    def add_power(self, user_id, power) -> None:
        """Добавление важности"""
        with self.connection:
            id_note = self.cursor.execute("SELECT MAX(id) FROM notes WHERE owner = ?", (user_id,)).fetchone()[0]
            return self.cursor.execute("UPDATE notes SET power = ? WHERE id = ?", (power, id_note))

    def get_records(self, user_id) -> str:
        """Получение всех записей юзера"""
        with self.connection:
            self.cursor.execute("DELETE FROM notes WHERE power is NULL")
            lst = self.cursor.execute("SELECT text, power, id FROM notes WHERE owner = ?", (user_id,)).fetchall()
            records = []
            power_s = {
                1: "очень важно",
                2: "средне",
                3: "заметка"
            }
            for (t, p, i) in lst:
                records.append(f"{power_s[p].capitalize()} : {t}\nУдалить запись /del{i}\n")
            return "\n".join(records)

    def get_records_power(self, user_id, power) -> str:
        """ Получение всех записей юзера с значением важности"""
        with self.connection:
            lst = self.cursor.execute("SELECT text, id FROM notes WHERE owner = ? AND power = ?",
                                      (user_id, power)).fetchall()
            records = []
            for (t, i) in lst:
                records.append(f"{t}\nУдалить запись /del{i}\n")
            return "\n".join(records)

    def delete_record(self, id_r, id_u) -> None:
        """ Удаление записи"""
        with self.connection:
            return self.cursor.execute("DELETE FROM notes WHERE id = ? AND owner = ?", (id_r, id_u))

    def get_counts(self, user_id) -> tuple:
        """ Получение всех количества записей по важности"""
        with self.connection:
            power_1 = \
                self.cursor.execute("SELECT COUNT(*) FROM notes WHERE power = 1 AND owner = ?", (user_id,)).fetchone()[
                    0]
            power_2 = \
                self.cursor.execute("SELECT COUNT(*) FROM notes WHERE power = 2 AND owner = ?", (user_id,)).fetchone()[
                    0]
            power_3 = \
                self.cursor.execute("SELECT COUNT(*) FROM notes WHERE power = 3 AND owner = ?", (user_id,)).fetchone()[
                    0]
            return power_1, power_2, power_3
