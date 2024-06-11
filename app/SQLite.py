import os
import sqlite3 as sl
import itertools


"""------------------------------------Константы------------------------------------------------"""

DAY_OF_WEEK = {1: "Понедельник", 2: "Вторник", 3: "Среда", 4: "Четверг", 5: "Пятница", 6: "Суббота", 7: "Воскресенье"}
TEACHER_INFO = "<b>ФИО:</b> {}\n<b>Должность:</b> {}\n<b>Ресурс:</b> <a href='#'>{}</a>"
AUD_ENCL_INFO = "<b>Ауд./корпус:</b> {}\n<b>Наименования корпуса:</b> {}\n<b>Адрес корпуса:</b> {}\n<b>Тип аудитории:</b> {}\n<b>Вместимость аудитории:</b> {}\n"
TAG = '<a class="openModalButton {}-click" data-photo="{}" data-information="{}">{}</a>'


class SQLite:
	"""
		
	"""

	@classmethod
	def __preprocess_st_schedule(cls, row: tuple) -> tuple:
		"""

		"""
		
		if row[8]:
			teacher_name = ' '.join(map(lambda name_part: name_part.capitalize(), row[8].split()))
			buffer = [elem if elem else "" for elem in row[:3]]
			teacher_info = TEACHER_INFO.format(teacher_name, buffer[0], buffer[2])
			row = row[:8] + (TAG.format('teacher', buffer[1] if buffer[1] else os.getenv("DEFAULT_TEACHER_IMAGE"), teacher_info, teacher_name),) + row[9:]
			buffer = teacher_info = None

		if row[12]:
			buffer = [elem if elem else "" for elem in row[13:]]
			aud_encl_info = AUD_ENCL_INFO.format(row[12], buffer[2], buffer[3], buffer[0], buffer[1])
			row = row[:12] + (TAG.format('enclosure', buffer[4] if buffer[4] else os.getenv("DEFAULT_ENCLOSURE_IMAGE"), aud_encl_info, row[12]),)
			buffer = aud_encl_info = None

		return row[3:13]


	@classmethod
	def __preprocess_teacher_schedule(cls, row: tuple) -> tuple:
		"""

		"""

		if row[9]:
			buffer = [elem if elem else "" for elem in row[10:]]
			aud_encl_info = AUD_ENCL_INFO.format(row[9], buffer[2], buffer[3], buffer[0], buffer[1])
			row = row[:9] + (TAG.format('enclosure', buffer[4] if buffer[4] else os.getenv("DEFAULT_ENCLOSURE_IMAGE"), aud_encl_info, row[9]),)
			buffer = aud_encl_info = None

		return row[:10]



	@classmethod
	def get_schedule_for_students(cls, params: dict) -> tuple:
		"""
			Метод класса, который по набору параметров возвращает расписание.
			Входные параметры:
				params - кортеж параметров следующего вида:
				{
					'uni_name': наименование университета,
					'fac_name': наименование факультета,
					'education_type': тип обучения,
					'course': курс,
					'group_name': название группы
				}
		"""

		for key in ['uni_name', 'fac_name', 'education_type', 'course', 'group_name']:
			try:
				params[key]
			except KeyError:
				raise Exception(f"Param '{key}' is not found in params")

		group_name = params['group_name'].split("||")
		connection = sl.connect(os.path.join(os.getenv('DATABASES_PATH'), params['uni_name'] + '.db'))
		cursor = connection.cursor()

		data_gen = cursor.execute(
			"""
				WITH current_group AS(
					SELECT id FROM Groups 
					WHERE course = ? and education_type_id = (SELECT id FROM Education_types WHERE type = ?)
						and faculty_id = (SELECT id FROM Faculties WHERE full_name = ?) and name = ? and number = ?
				)
				SELECT Teachers.job_title, Teachers.image_name, Teachers.site_link, day_of_week as "День", time_interval as "Время", 
					subgroup as "Подгруппа", week_multiplicity as "Неделя", COALESCE(NULLIF(Disciplines.full_name, ''), Disciplines.short_name) as "Название дисциплины", 
					Teachers.full_name as "Преподаватель", lesson_type as "Вид", period as "Период",
					additional_info as "Дополнительная информация", number || '/' || enclosure_id as "Ауд./корпус",
					Audiences.type, Audiences.capacity, Enclosures.name, Enclosures.address, Enclosures.image_name
				FROM (SELECT Schedule.* from Schedule, current_group WHERE group_id = (current_group.id)) 
				INNER JOIN Disciplines on Disciplines.id = discipline_id
				LEFT JOIN Teachers on Teachers.id = teacher_id
				LEFT JOIN Audiences on Audiences.id = audience_id
				LEFT JOIN Enclosures on Enclosures.id = Audiences.enclosure_id
				INNER JOIN Call_schedule on Call_schedule.id = call_id
				ORDER BY day_of_week, call_id
			""",
			(params['course'], params['education_type'].lower(), params['fac_name'].upper(), group_name[1].lstrip(), group_name[0].rstrip())
		)

		try:
			row = cls.__preprocess_st_schedule(next(data_gen))
			cur_day = row[0]
			data = [list(row[0] for row in cursor.description[4:13]), DAY_OF_WEEK[cur_day], row[1:]]

			for row in data_gen:
				if cur_day != row[3]:
					cur_day = row[3]
					data.append(DAY_OF_WEEK[cur_day])
				data.append(cls.__preprocess_st_schedule(row)[1:])
		except StopIteration:
			data = ()
		finally:
			connection.close()

		return data


	@classmethod
	def get_schedule_for_teacher(cls, params: dict) -> tuple:
		"""
			
		"""

		for key in ['uni_name', 'teacher_name']:
			try:
				params[key]
			except KeyError:
				raise Exception(f"Param '{key}' is not found in params")
		teacher_name = params['teacher_name'].lower()

		connection = sl.connect(os.path.join(os.getenv('DATABASES_PATH'), params['uni_name'] + '.db'))
		cursor = connection.cursor()

		teacher_info = cursor.execute(
			"""
				SELECT id, job_title, image_name, site_link FROM Teachers WHERE full_name = ?
			""",
			(teacher_name,)
		).fetchone()

		data_gen = cursor.execute(
			"""
				SELECT day_of_week as "День", time_interval as "Время", subgroup as "Подгруппа", week_multiplicity as "Неделя", 
					Disciplines.full_name as "Название дисциплины",	Groups.number || '-' || course || ' || ' || Groups.name as "Группа", lesson_type as "Вид", 
					period as "Период", additional_info as "Дополнительная информация", Audiences.number || '/' || enclosure_id as "Ауд./корпус",
					Audiences.type, Audiences.capacity, Enclosures.name, Enclosures.address, Enclosures.image_name
				FROM (SELECT * FROM Schedule WHERE teacher_id = ?)
				INNER JOIN Disciplines on Disciplines.id = discipline_id
				LEFT JOIN Audiences on Audiences.id = audience_id
				LEFT JOIN Enclosures on Enclosures.id = Audiences.enclosure_id
				INNER JOIN Call_schedule on Call_schedule.id = call_id
				INNER JOIN Groups on Groups.id = group_id
				ORDER BY day_of_week, call_id
			""",
			(teacher_info[0],)
		)

		teacher_info = list(map(lambda elem: elem if elem else "", teacher_info[1:]))

		try:
			row = cls.__preprocess_teacher_schedule(next(data_gen))
			cur_day = row[0]
			data = [list(row[0] for row in cursor.description[1:10]), DAY_OF_WEEK[cur_day], row[1:]]

			for row in data_gen:
				if cur_day != row[0]:
					cur_day = row[0]
					data.append(DAY_OF_WEEK[cur_day])
				data.append(cls.__preprocess_teacher_schedule(row)[1:])
		except StopIteration:
			data = ()
		finally:
			connection.close()

		return data, teacher_info[1], TEACHER_INFO.format(teacher_name, teacher_info[0], teacher_info[2])


	# def close_connection(self):
	# 	"""

	# 	"""
		
	# 	if self.connection is None or self.connection.cursor().connection is None:
	# 		self.connection.close()
		
	# 	self.course = None
	# 	self.education_type_id = None
	# 	self.faculty_id = None
	# 	self.closed = True


	@classmethod
	def get_teachers(cls, params: dict, pattern: str='') -> list | None:
		"""

		"""

		try:
			params['uni_name']
		except KeyError:
			raise Exception(f"Param 'uni_name' is not found in params")
		
		connection = sl.connect(os.path.join(os.getenv('DATABASES_PATH'), params['uni_name'] + '.db'))
		cursor = connection.cursor()

		data_gen = cursor.execute(
			"""
				SELECT full_name FROM Teachers
				WHERE full_name LIKE "%" || ? || "%"
			""",
			(pattern.lower(),)
		)

		data = data_gen if data_gen is None else list(map(lambda lower_name: ' '.join(map(lambda name_part: name_part.capitalize(), lower_name.split())), itertools.chain(*data_gen.fetchall()))) # TODO capitalize
		connection.close()

		return data


	@classmethod
	def get_unis_names(cls) -> list | None:
		"""

		"""

		return list(map(lambda file: file.removesuffix('.db'), filter(lambda file: file.endswith('.db'), os.listdir(os.getenv('DATABASES_PATH')))))


	@classmethod
	def get_facs_names(cls, params: dict) -> list | None:
		"""

		"""

		try:
			params['uni_name']
		except KeyError:
			raise Exception(f"Param 'uni_name' is not found in params")

		connection = sl.connect(os.path.join(os.getenv('DATABASES_PATH'), params['uni_name'] + '.db'))
		cursor = connection.cursor()

		data_gen = cursor.execute(
			"""
				SELECT full_name FROM Faculties
			"""
		)

		data = data_gen if data_gen is None else list(map(lambda name_part: name_part.capitalize(), itertools.chain(*data_gen.fetchall())))
		connection.close()

		return data


	@classmethod
	def get_education_types(cls, params: dict) -> list | None:
		"""

		"""

		for key in ['uni_name', 'fac_name']:
			try:
				params[key]
			except KeyError:
				raise Exception(f"Param '{key}' is not found in params")

		connection = sl.connect(os.path.join(os.getenv('DATABASES_PATH'), params['uni_name'] + '.db'))
		cursor = connection.cursor()

		data_gen = cursor.execute(
			"""
				SELECT DISTINCT Education_types.type FROM Groups
				INNER JOIN Education_types on Education_types.id = education_type_id
				WHERE faculty_id = (SELECT id FROM Faculties WHERE full_name = ?)
			""",
			(params['fac_name'].upper(),)
		)

		data = data_gen if data_gen is None else list(map(lambda name_part: name_part.capitalize(), itertools.chain(*data_gen.fetchall())))
		connection.close()

		return data


	@classmethod
	def get_courses(cls, params: dict) -> list | None:
		"""

		"""

		for key in ['uni_name', 'fac_name', 'education_type']:
			try:
				params[key]
			except KeyError:
				raise Exception(f"Param '{key}' is not found in params")

		connection = sl.connect(os.path.join(os.getenv('DATABASES_PATH'), params['uni_name'] + '.db'))
		cursor = connection.cursor()

		data_gen = cursor.execute(
			"""
				SELECT min(course), max(course) FROM Groups
				WHERE faculty_id = (SELECT id FROM Faculties WHERE full_name = ?)
					and education_type_id = (SELECT id FROM Education_types WHERE type = ?)
			""",
			(params['fac_name'].upper(), params['education_type'].lower())
		)
		
		if data_gen is not None:
			m, M = data_gen.fetchone()

		data = data_gen if data_gen is None else list(range(m, M+1))
		connection.close()

		return data


	@classmethod
	def get_groups_names(cls, params: dict) -> list | None:
		"""

		"""

		for key in ['uni_name', 'fac_name', 'education_type', 'course']:
			try:
				params[key]
			except KeyError:
				raise Exception(f"Param '{key}' is not found in params")

		connection = sl.connect(os.path.join(os.getenv('DATABASES_PATH'), params['uni_name'] + '.db'))
		cursor = connection.cursor()
		
		data_gen = cursor.execute(
			"""
				SELECT number || ' || ' || name as full_name FROM Groups
				WHERE faculty_id = (SELECT id FROM Faculties WHERE full_name = ?)
					and education_type_id = (SELECT id FROM Education_types WHERE type = ?) and course = ?
				ORDER BY full_name
			""",
			(params['fac_name'].upper(), params['education_type'].lower(), params['course'])
		)

		data = data_gen if data_gen is None else list(itertools.chain(*data_gen.fetchall()))
		connection.close()

		return data



# if __name__ == '__main__':
# 	os.environ['DATABASES_PATH'] = '/home/crut/Desktop/flask_app/dbs'
# 	form = {}
# 	form['uni_name'] = SQLite.get_unis_names()[0]
# 	print(f"Выбранный университет: {form['uni_name']}")
# 	obj = SQLite(form['uni_name'])
	
# 	print("Все учителя:", obj.get_teachers())
# 	form['teacher_name'] = obj.get_teachers("Ам")[0]
# 	print(f"Выбранный учитель: {form['teacher_name']}")
# 	print(obj.get_schedule_for_teacher(form['teacher_name'])) 
	
# 	obj = SQLite(form['uni_name'])
# 	print("Все доступные факультеты:", obj.get_facs_names())
# 	form['fac_name'] = "ММФ"
# 	print(f"Выбранный факультет: {form['fac_name']}")
# 	print("Все доступные типы обучения:", obj.get_education_types(form['fac_name']))
# 	form['education_type'] = obj.get_education_types(form['fac_name'])[0]
# 	print(f"Выбранный тип обучения: {form['education_type']}")
# 	print("Все доступные курсы:", obj.get_courses(form['education_type']))
# 	form['course'] = obj.get_courses(form['education_type'])[0]
# 	print(f"Выбранный курс: {form['course']}")
# 	print("Все доступные группы:", obj.get_groups_names(form['course']))
# 	form['group_name'] = obj.get_groups_names(form['course'])[0]
# 	print(f"Выбранная группа: {form['group_name']}")
# 	print(obj.get_schedule_for_students(form['group_name']))
