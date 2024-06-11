import sqlite3 as sl
import re
import requests
import json
from Google_API import Google_API
import warnings

# MULTIPLICITY = 2
# N_COURSES = 6


class University_schedule:
	"""
		Класс, отвечающий за создание и заполнение базы данных расписания университета.
	"""


	def __init__(self):
		"""

		"""

		self.university_name = None
		self.connection = None
		self.api = None
		self.MULTIPLICITY = None
		self.N_COURSES = 6


	def __create(self) -> None:
		"""
			Создание следующих таблиц, если таковые отсутсвуют:
				"Schedule": id, day_of_week, call_id, discipline_id, audience_id, teacher_id, group_id, 
					subgroup(а,б,в,...), week_multiplicity(кратность номера недели), lesson_type(л, п, лаб), 
					period(уточнения сроков проведения занятий), additional_info(иная уточняющая информация);
				"Groups": id, course(номер курса), number(если есть, иначе краткое название группы), name(специальность/название), 
					education_type_id, faculty_id;
				"Education_types": id, type(тип обучения);
				"Call_schedule": id, time_interval(временной интервал пары);
				"Disciplines": id, short_name(краткое название), full_name(полное наименование);
				"Audiences": id, enclosure_id, number(номер аудитории), type(тип аудитории, по критерию: возможности использование аппаратуры), 
					dimensions(вместимость аудитории);
				"Enclosures": id, name, address(адрес корпуса), image_name(путь к файлу содержащему изображение корпуса;
				"Faculties": id, short_name(краткое название), full_name(полное наименование);
				"Teachers": id, full_name, job_title(должность преподавателя), image_name(путь к файлу содержащему изображение преподавателя), 
					site_link(ссылка на источник с дополнытельной информацией о преподавателе).
		"""
		
		try:
			self.connection.execute("""
				CREATE TABLE IF NOT EXISTS "Education_types" (
					"id" INTEGER NOT NULL PRIMARY KEY,
					"type" VARCHAR(40) NOT NULL UNIQUE
				);
			""")

			self.connection.execute("""
				CREATE TABLE IF NOT EXISTS "Call_schedule" (
					"id" INTEGER NOT NULL PRIMARY KEY,
					"time_interval" VARCHAR(15) NOT NULL UNIQUE
				);
			""")

			self.connection.execute("""
				CREATE TABLE IF NOT EXISTS "Disciplines" (
					"id" INTEGER NOT NULL PRIMARY KEY,
					"short_name" VARCHAR(10) NOT NULL DEFAULT "",
					"full_name" VARCHAR(50) NOT NULL DEFAULT "",
					UNIQUE("short_name", "full_name")
				);
			""")

			self.connection.execute("""
				CREATE TABLE IF NOT EXISTS "Enclosures" (
					"id" INTEGER NOT NULL PRIMARY KEY,
					"name" VARCHAR(50) NOT NULL,
					"address" VARCHAR(100) NOT NULL,
					"image_name" VARCHAR(20) DEFAULT NULL
				);
			""")

			self.connection.execute("""
				CREATE TABLE IF NOT EXISTS "Audiences" (
					"id" INTEGER NOT NULL PRIMARY KEY,
					"enclosure_id" INTEGER NOT NULL,
					"number" VARCHAR(15) NOT NULL,
					"type" VARCHAR(20) DEFAULT NULL,
					"capacity" INTEGER DEFAULT NULL,
					FOREIGN KEY("enclosure_id") REFERENCES "Enclosures"("id") ON UPDATE CASCADE ON DELETE CASCADE,
					UNIQUE("enclosure_id", "number")
				);
			""")

			self.connection.execute("""
				CREATE TABLE IF NOT EXISTS "Faculties" (
					"id" INTEGER NOT NULL PRIMARY KEY,
					"short_name" VARCHAR(10) NOT NULL,
					"full_name" VARCHAR(50) NOT NULL UNIQUE
				);
			""")

			self.connection.execute(f"""
				CREATE TABLE IF NOT EXISTS "Groups" (
					"id" INTEGER NOT NULL PRIMARY KEY,
					"course" TINYINT NOT NULL CHECK("course" in {tuple(range(1, self.N_COURSES+1))}),
					"number" VARCHAR(10) NOT NULL,
					"name" VARCHAR(100) NOT NULL,
					"education_type_id" INTEGER NOT NULL,
					"faculty_id" INTEGER NOT NULL,
					FOREIGN KEY("education_type_id") REFERENCES "Education_types"("id") ON UPDATE CASCADE ON DELETE CASCADE,
					FOREIGN KEY("faculty_id") REFERENCES "Faculties"("id") ON UPDATE CASCADE ON DELETE CASCADE,
					UNIQUE("education_type_id", "faculty_id", "course", "number")
				);
			""")

			self.connection.execute("""
				CREATE TABLE IF NOT EXISTS "Teachers" (
					"id" INTEGER NOT NULL PRIMARY KEY,
					"full_name" VARCHAR(50) NOT NULL,
					"job_title" VARCHAR(70) NOT NULL,
					"image_name" VARCHAR(20) DEFAULT NULL,
					"site_link" VARCHAR(200) DEFAULT NULL,
					UNIQUE("full_name", "job_title")
				);
			""")

			self.connection.execute(f"""
				CREATE TABLE IF NOT EXISTS "Schedule" (
					"id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
					"day_of_week" TINYINT NOT NULL CHECK("day_of_week" in (1, 2, 3, 4, 5, 6, 7)),
					"call_id" INTEGER NOT NULL,
					"discipline_id" INTEGER NOT NULL,
					"audience_id" INTEGER  DEFAULT NULL,
					"teacher_id" INTEGER DEFAULT NULL,
					"group_id" INTEGER NOT NULL,
					"subgroup" VARCHAR(10) DEFAULT NULL,
					"week_multiplicity" TINYINT CHECK("week_multiplicity" is NULL or 1 <= "week_multiplicity" <= {self.MULTIPLICITY}) DEFAULT NULL,
					"lesson_type" VARCHAR(5) DEFAULT NULL,
					"period" VARCHAR(50) DEFAULT NULL,
					"additional_info" VARCHAR(100) DEFAULT NULL,
					FOREIGN KEY("call_id") REFERENCES "Call_schedule"("id") ON UPDATE CASCADE ON DELETE CASCADE,
					FOREIGN KEY("discipline_id") REFERENCES "Disciplines"("id") ON UPDATE CASCADE ON DELETE CASCADE,
					FOREIGN KEY("audience_id") REFERENCES "Audiences"("id") ON UPDATE CASCADE ON DELETE CASCADE,
					FOREIGN KEY("teacher_id") REFERENCES "Teachers"("id") ON UPDATE CASCADE ON DELETE CASCADE,
					FOREIGN KEY("group_id") REFERENCES "Groups"("id") ON UPDATE CASCADE ON DELETE CASCADE
				);
			""")
			# UNIQUE(day_of_week, call_id, group_id, subgroup, week_multiplicity)

			self.connection.execute("""
	            CREATE TRIGGER IF NOT EXISTS check_schedule BEFORE INSERT ON Schedule
	            FOR EACH ROW
	            BEGIN
	                SELECT RAISE(IGNORE)
	                WHERE EXISTS (
	                    SELECT 1 FROM Schedule
	                    WHERE group_id = NEW.group_id AND day_of_week = NEW.day_of_week AND call_id = NEW.call_id AND subgroup is NEW.subgroup AND week_multiplicity is NEW.week_multiplicity
	                );
	            END;
	        """)

			self.connection.commit()
		except:
			raise Exception("Something wrong with creating tables")


	def connect_db(self, university_name: str, ignore_connection: bool=False) -> None:
		"""
			Подключение к базе данных университета по его наименованию.
			Входные параметры:
				university_name: наименование университета,
				ignore_connection: отвечает за игнорирование наличия текущего соединение.

		"""

		try:
			self.connection.execute("SELECT 1")
			if ignore_connection:
				self.connection.close()
				raise Exception
			warnings.warn("Connection is not closed: you can not connect to database, please close current connection before or use ignore_connection=True")
		except:
			try:
				self.connection = sl.connect(university_name + ".db")
				self.university_name = university_name
			except:
				raise Exception(f"Something wrong with connection to database '{university_name}.db'")


	def close_connection(self) -> None:
		"""
			Закрытие текущего соединения.
		"""

		try:
			self.connection.execute("SELECT 1")
			self.connection.close()
		except:
			warnings.warn("Can not close connection, it is already closed")



	def create_db(self) -> None:
		"""
			Создание базы данных в случае отсутсвия таковой(название: 'university name.db').
			При наличие базы данных будет выдано предупреждение о её существовании, при этом ничего не будет изменено.
		"""

		if self.university_name is None:
			raise Exception("Can't create database, university name wasn't transferred")

		try:
			import os
			if os.path.exists(f"{self.university_name}.db"):
				warnings.warn("Warning, database already exists")
			self.__create()
			del os
		except:
			raise Exception("Something wrong with creating database")


	def drop_db(self) -> None:
		"""
			Удаление базы данных с названием 'university name.db'.
			В случае отсутсвия такой базы данных будет выдано предупреждение.
		"""

		if self.university_name is None:
			raise Exception("Can't drop database, university name wasn't transferred")
		try:
			import os
			if os.path.exists(f"{self.university_name}.db"):
				os.remove(f"{self.university_name}.db")
			else:
				warnings.warn("Warning, database may no longer exist")
			del os
		except:
			raise Exception("Something wrong with drop database")


	def __special_insert(self, special_data: list[str]) -> None:
		"""
			Заолнение таблиц Call_schedule, Enclouserd, Faculties в базе данных.
		"""

		cursor = self.connection.cursor()

		if cursor.execute("SELECT 1 FROM Call_schedule LIMIT 1").fetchone() is None:
			for index, time in enumerate(special_data['call_schedule'], start=1):
				cursor.execute(
		            "INSERT INTO Call_schedule (id, time_interval) VALUES (?, ?)",
		            (index, time)
		        )
			self.connection.commit()

		if cursor.execute("SELECT 1 FROM Faculties WHERE short_name = ? and full_name = ?", special_data['fac_name']).fetchone() is None:
			cursor.execute(
				"INSERT INTO Faculties (short_name, full_name) VALUES (?, ?)",
				special_data['fac_name']
			)
			self.connection.commit()

		if cursor.execute("SELECT 1 FROM Enclosures LIMIT 1").fetchone() is None:
			cursor.executemany(
				"INSERT INTO Enclosures (id, name, address) VALUES (?, ?, ?)",
				[[enclosure[0], enclosure[1], "" if len(enclosure) == 2 else enclosure[2]] for enclosure in special_data['enclosures']]
			)
			self.connection.commit()


	def __insert(self, sheet_data: dict) -> None:
		"""
			Заполнение базы данных.
		"""

		cursor = self.connection.cursor()

		"""------------------------------------Получение id факультета------------------------------------------------"""
		
		faculty_id = cursor.execute(
				"SELECT id FROM Faculties WHERE short_name = ? and full_name = ?",
				sheet_data['fac_name']
			).fetchone()[0]

		"""------------------------------------Обработка education_type------------------------------------------------"""

		cursor.execute(
			"INSERT OR IGNORE INTO Education_types (type) VALUES (?) RETURNING id",
			(sheet_data['education_type'],)
		)
		education_type_id = cursor.fetchone()
		# Получение id данного типа обучения
		if education_type_id is None:
			education_type_id = cursor.execute(
				"SELECT id FROM Education_types WHERE type = ?",
				(sheet_data['education_type'],)
			).fetchone()[0]
		else:
			education_type_id = education_type_id[0]
		

		"""------------------------------------Цикл по расписанию каждой из групп данного курса------------------------------------------------"""
		
		for key, group_data in sheet_data['groups'].items():
			# заполнение таблицы Groups
			# TODO course
			cursor.execute(
				"INSERT OR IGNORE INTO Groups (course, number, name, education_type_id, faculty_id) VALUES (?, ?, ?, ?, ?) RETURNING id",
				(sheet_data['course'], key, group_data['name'], education_type_id, faculty_id)
			)
			group_id = cursor.fetchone()
			# Получение id данной группы
			if group_id is None:
				group_id = cursor.execute(
					"SELECT id FROM Groups WHERE course = ? and number = ? and education_type_id = ? and faculty_id = ?",
					(sheet_data['course'], key, education_type_id, faculty_id)
				).fetchone()[0]
			else:
				group_id = group_id[0]
			# buffer содержит преобразованное к нужному виду расписание для заполнения базы данных Schedule
			buffer = []
			# цикл по каждой записи в расписании
			for data in group_data['schedule']:
				# обработка значения колонки 'Аудитория/корпус'
				if data[-1]:
					try:
						audience, enclosure_id = map(lambda elem: elem.strip(), data[-1].split('/'))
						# проверка существования id корпуса
						if cursor.execute("SELECT 1 FROM Enclosures WHERE id = ?", (enclosure_id,)).fetchone() is None:
							raise Exception(f"Enclosure with index {enclosure_id} does not exist")
						# заполнение таблицы Audiences
						cursor.execute(
							"INSERT OR IGNORE INTO Audiences (number, enclosure_id) VALUES (?, ?) RETURNING id",
							(audience, int(enclosure_id))
						)
						audience_id = cursor.fetchone()
						# получение id аудитории
						if audience_id is None:
							audience_id = cursor.execute(
								"SELECT id FROM Audiences WHERE number = ? and enclosure_id = ?",
								(audience, int(enclosure_id))
							).fetchone()[0]
						else:
							audience_id = audience_id[0]
						audience = enclos = None
					except:
						raise Exception(f"Something wrong while getting audience number and enclosude id from {data[-1]}")
				else:
					audience_id = None 
				# TODO точно ли важно отсуствие пробелов между частями ФИО
				# получение ФИО преподавателя из поля 'Название дисциплины, преподаватель'
				teacher_name = re.search(r'[А-ЯЁа-я\-]*\s[А-Я][\.,]\s*[А-Я][\.,]', data[4])
				# обработка ФИО перподавателя
				if teacher_name is not None:
					# TODO множество преподавателей
					teacher_name = teacher_name.group(0)
					# заполнение таблицы Teachers
					cursor.execute(
						"INSERT OR IGNORE INTO Teachers (full_name, job_title) VALUES (?, ?) RETURNING id",
						(db_teacher_name:=' '.join(teacher_name.lower().replace(',', '.').split()), "")
					)
					teacher_id = cursor.fetchone()
					# получение id преподавателя
					if teacher_id is None:
						teacher_id = cursor.execute(
							"SELECT id FROM Teachers WHERE full_name = ? and job_title = ?",
							(db_teacher_name, "")
						).fetchone()[0]
					else:
						teacher_id = teacher_id[0]
					# получение названия дисциплины
					discipline_name = data[4].rstrip(teacher_name).rstrip()
				else:
					teacher_id = None
					discipline_name = data[4]
				# заполнение таблицы Disciplines
				cursor.execute(
						"INSERT OR IGNORE INTO Disciplines (short_name, full_name) VALUES (?, ?) RETURNING id",
						(discipline_name, "") if re.match(r'^[А-ЯЁ]+$', discipline_name) else ("", discipline_name)
					)
				discipline_id = cursor.fetchone()
				# получение id дисциплины
				if discipline_id is None:
					discipline_id = cursor.execute(
						"SELECT id FROM Disciplines WHERE short_name = ? and full_name = ?",
						(discipline_name, "") if re.match(r'^[А-ЯЁ]+$', discipline_name) else ("", discipline_name)
					).fetchone()[0]
				else:
					discipline_id = discipline_id[0]
				# обработка поля 'неделя' (номер по модулю self.MULTIPLICITY)
				if data[3]:
					try:
						data[3] = int(data[3].lower().replace('н', '').strip())
					except:
						print(data[3])
						raise Exception(f"{data[3]} is not like 'nн', where n is week multiplicity")
				# добавление обработанного урока в buffer
				buffer += [data[:2] + [discipline_id, audience_id, teacher_id, group_id] + data[2:4] + data[5:8]]
			# заполнение таблицы Schedule
			try:
				cursor.executemany(
						"""INSERT OR IGNORE INTO Schedule 
						(day_of_week, call_id, discipline_id, audience_id, teacher_id, group_id, subgroup, week_multiplicity, lesson_type, period, additional_info) \
						VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
						buffer
					)
				self.connection.commit()
			except:
				raise Exception(f"Something wrong while inserting schedule of {sheet_data['course']} course, group '{key}'")


	def upload(self, gs_link: str, drop_database: bool=True) -> None:
		"""
			Заполнение базы данных с помощью расписания, хранящемся в Google Таблицах.
			Входные параметры:
				gs_link: ссылка на удовлетворяющий шаблону файл с расписанием в Google Таблицах,
				drop_database: удалить ли базу данных перед заполнением(по умолчанию True).
		"""
		
		if not re.match(r'^https://docs.google.com.*', gs_link):
			raise Exception(f"{gs_link} must point to Google Sheets")
		try:
			response = requests.get(gs_link)
			if not response.ok:
				raise Exception
			response = None
		except:
			raise Exception(f"Something wrong with '{gs_link}', check url and try again")

		if self.api is None:
			self.api = Google_API()
		
		self.api.open(url_google_sheets=gs_link)
		data_generator = self.api.execute()
		info_sheet_json = next(data_generator)

		"""------------------------------------Подгрузка "info.json"------------------------------------------------"""
		
		with open("info.json", "r") as file:
			buffer = json.load(file)
			try:
				university_information = buffer[info_sheet_json['uni_name']]
			except:
				raise Exception(f"'{info_sheet_json['uni_name']}' isn't found in 'info.json'")
			
			buffer = None
		
		"""------------------------------------Обработка названия университета------------------------------------------------"""
		
		if self.university_name is None:
			self.university_name = info_sheet_json['uni_name']
		elif self.university_name != info_sheet_json['uni_name']:
			warnings.warn(f"Found document about another university {info_sheet_json['uni_name']}, but current processed university is {self.university_name}")

		"""------------------------------------Обработка названия факультета------------------------------------------------"""
		
		try:
			buffer = university_information['faculties'].index(info_sheet_json['fac_name'])
		except:
			raise Exception(f"Faculty name: {info_sheet_json['fac_name']}, isn't recognised")

		"""------------------------------------Обработка константы MULTIPLICITY------------------------------------------------"""

		try:
			if university_information['MULTIPLICITY'][buffer] != self.MULTIPLICITY:
				self.MULTIPLICITY = int(university_information['MULTIPLICITY'][buffer])
		except KeyError:
			raise Exception(f"Field MULTIPLICITY is absent in 'json.info'")
		except ValueError:
			raise Exception(f"Field MULTIPLICITY in 'json.info' should be int or str")

		"""------------------------------------Обработка константы N_COURSES------------------------------------------------"""

		try:
			if university_information['N_COURSES'][buffer] != self.N_COURSES:
				self.N_COURSES = int(university_information['N_COURSES'][buffer])
		except KeyError:
			raise Exception(f"Field N_COURSES is absent in 'json.info'")
		except ValueError:
			raise Exception(f"Field N_COURSES in 'json.info' should be int or str")

		"""------------------------------------Обработка информации о корпусах университета------------------------------------------------"""
		
		if info_sheet_json['enclosures'] != {row[0]: row[1] for row in university_information['enclosures']}:
			raise Exception(f"Enclosures in file {gs_link} don't match to file 'info.json'")
		info_sheet_json['enclosures'] = university_information['enclosures']
		university_information = None

		"""------------------------------------Сброс базы данных при необходимости------------------------------------------------"""
		
		if drop_database:
			self.drop_db()
			if not (self.connection is None or self.connection.cursor().connection is None):
				self.close_connection()
		
		# TODO
		"""------------------------------------Переподключение к базе данных при необходимости------------------------------------------------"""

		try:
			self.connection.execute("SELECT 1")
			if self.university_name != info_sheet_json['uni_name']:
				raise Exception
		except:
			self.connect_db(info_sheet_json['uni_name'], ignore_connection=True)
		finally:
			self.create_db()
		del info_sheet_json['uni_name']

		"""------------------------------------Заполнение базы данных------------------------------------------------"""
		
		for data in data_generator:
			if data.get('course'):
				self.__insert(data | {'fac_name': info_sheet_json['fac_name']})
			elif data.get('call_schedule'):
				self.__special_insert(data | info_sheet_json)

		self.api = None


	def uploadmany(self, gs_links: list[str] | tuple[str] | set[str], drop_database: bool=True) -> None:
		"""
			Заполнение базы данных с помощью расписания, хранящемся в Google Таблицах.
			Входные параметры:
				gs_links: ссылки на удовлетворяющие шаблону(подробнее в README.txt) файлы с расписанием в Google Таблицах.
				drop_database: удалить ли базу данных перед началом заполнения(по умолчанию True).
		"""

		try:
			self.upload(gs_link=gs_links[0], drop_database=drop_database)
		except IndexError:
			warnings.warn("No links were sent to function 'uploadmany'")

		for gs_link in gs_links[1:]:
			self.upload(gs_link=gs_link, drop_database=False)


if __name__ == '__main__':
	import os

	with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'), 'r') as file:
		for line in file:
			# Игнорируем пустые строки и строки, начинающиеся с #
			line = line.strip()
			if line and not line.startswith('#'):
				key, value = line.strip().split('=', 1)
				os.environ[key] = value

	university = University_schedule()
	link = "https://docs.google.com/spreadsheets/d/1cbaadvTmieE714fNn2_Id_aua6nP7buFJJ2KzWF7CAQ"
	# university.upload(gs_link=link)
	university.uploadmany(gs_links=[link, link])
	# university.connect_db()
	# print(University_schedule.__doc__)
	# print(help(University_schedule))
