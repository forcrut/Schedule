import gspread
from typing import Generator
import re
import warnings
import os


"""------------------------------------Константы------------------------------------------------"""

N_COLUMNS = 7
DAY_OF_WEEK = {"понедельник": 1, "вторник": 2, "среда": 3, "четверг": 4, "пятница": 5, "суббота": 6, "воскресенье": 7}
EDUCATION_TYPES = {"дневное отделение", "дневное отделение(сокр.)", "заочное отделение", "заочное отделение(сокр.)"}


class Google_API:
	"""
		Парсер документа в Google Таблицах, содержащего расписание одного факультета. 
	"""

	def __init__(self) -> None:
		"""
			Создание client(аккаунта подключения к Google API).
		"""

		account_json = {
		    "type": os.getenv("GOOGLE_SERVICE_ACCOUNT_TYPE"),
		    "project_id": os.getenv("GOOGLE_SERVICE_ACCOUNT_PROJECT_ID"),
		    "private_key_id": os.getenv("GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY_ID"),
		    "private_key": os.getenv("GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY").replace("\\n", "\n"),
		    "client_email": os.getenv("GOOGLE_SERVICE_ACCOUNT_CLIENT_EMAIL"),
		    "client_id": os.getenv("GOOGLE_SERVICE_ACCOUNT_CLIENT_ID"),
		    "auth_uri": os.getenv("GOOGLE_SERVICE_ACCOUNT_AUTH_URI"),
		    "token_uri": os.getenv("GOOGLE_SERVICE_ACCOUNT_TOKEN_URI"),
		    "auth_provider_x509_cert_url": os.getenv("GOOGLE_SERVICE_ACCOUNT_AUTH_PROVIDER_CERT_URL"),
		    "client_x509_cert_url": os.getenv("GOOGLE_SERVICE_ACCOUNT_CLIENT_CERT_URL"),
		    "universe_domain": os.getenv("GOOGLE_SERVICE_ACCOUNT_UNIVERSE_DOMAIN")
		}

		try:
			self.client = gspread.service_account_from_dict(account_json)
		except:
			raise Exception(f"Failed to establish client")


	def open(self, url_google_sheets: str) -> None:
		"""
			Получение документа посредствам соединения с Google Таблицами.
			Входные параметры:
				url_google_sheets: ссылка на необходимый Google документ, содержащий расписание для парсинга.
		"""

		try:
			self.google_sheets = self.client.open_by_url(url_google_sheets)
			self.current_url = url_google_sheets
		except:
			raise Exception(f"Failed to open document by url: {url_google_sheets}")


	def info_handler(self, info_worksheet: gspread.worksheet.Worksheet) ->  dict:
		"""
			Обработка страницы 'info'.
			Входные параметры:
				info_worksheet: экземпляр класса Worksheet, представляющий страницу "info".
			Возвращает 
				{
					'uni_name': university_name, 
					'fac_name': [short_fac_name, full_fac_name]
				}, 
				аббревиатура университета и название(краткое и полное) факультета записаны на странице 'info'.
		"""

		"""------------------------------------Считывание данных страницы------------------------------------------------"""
		
		try:
			data = list(map(lambda row: list(map(lambda elem: elem.strip(), row)), info_worksheet.get_all_values()))
		except gspread.exceptions.APIError:
			self.google_sheets = self.client.open_by_url(self.url_google_sheets)
			info_worksheet = self.google_sheets.worksheet("info")
			data = list(map(lambda row: list(map(lambda elem: elem.strip(), row)), info_worksheet.get_all_values()))

		if data == [[]]:
			raise Exception(f'"info" sheet is empty')

		info_dict = dict.fromkeys(['uni_name', 'fac_name', 'enclosures'])
		
		info_dict['uni_name'] = data[0][0]

		"""------------------------------------Обработка названия университета------------------------------------------------"""

		if not info_dict['uni_name']:
			raise Exception("University name can't be ''")
		
		"""------------------------------------Обработка наименования факультета------------------------------------------------"""

		fac_short_name, *fac_full_name = data[1][0].split()
		fac_full_name = ' '.join(fac_full_name)
		info_dict['fac_name'] = [fac_short_name.upper(), fac_full_name.upper()]

		if not fac_short_name or not fac_full_name:
			raise Exception(f"Facylty name is missed")

		"""------------------------------------Обработка информации о корпусах------------------------------------------------"""
		
		try:
			if data[2][0] != 'Номера' and data[2][1] != 'Корпуса':
				raise Exception(f'Sheet "info" does not have columns "Номера" и "Корпуса" in required cells')
		except:
			raise Exception("Columns 'Номера' and 'Корпуса' are not recognised")

		info_dict['enclosures'] = {}
		for row in data[3:]:
			if not row[0].isnumeric():
				raise Exception(f'In sheet "info": {row[0]} is not numeric')
			elif (buffer:=int(row[0])) <= 0:
				raise Exception("Enclosure's number should be positive")
			elif not row[1]:
				raise Exception(f"{row[0]} enclosure does not have the name")
			info_dict['enclosures'][buffer] = row[1]
		buffer = None

		if not info_dict['enclosures']:
			warnings.warn(f'Sheet "info" does not contain information about enclosures')

		return info_dict


	def execute(self) -> dict:
		"""
			Обработка Google таблицы, содержащей расписание факультета университета (листы с названием "n курс" или "n course", где n - номер курса), 
				а также лист с названием "info", содержащий информацию о названии данного факультета и корпусах данного университета.
			Примечение: другие листы будут проигнорированы.
			Возвращает dict следующего вида:
				{ 
					'course': n,
					'education_type': education type, 
					'groups': {group_number: {'name': group_name, 'schedule': [day_of_week_ind, call_schedule_index, ...]}, ...}
				} 
				если страница имеет название "n курс" или "n course", 
				{
					'uni_name': university_name,
					'fac_name': [short_faculty_name, full_faculty_name],
					'enclosures': [[id, name], ...]
				}
				если страница называется "info", иначе игнорируется.
			Первоочередно обрабатывается страница "info" с проверкой, содержащейся в ней информации:
				название университета(аббревиатуру) и информация о корпусах университета.
			Примечание:
				при обработке первой страницы типа "n курс"/"n course" один раз дополнительно возвращается dict:
				{
					'call_schedule': [time_of_first_lesson, ...]
				}, 
				содержащий временные интервалы пар.
		"""
			
		"""---------------------------------------Считывание страницы "info"--------------------------------------------------"""

		try:
			yield self.info_handler(self.google_sheets.worksheet("info"))
		except:
			raise Exception(f"sheet 'info' is absent")

		sheets_ind = 0
		
		columns, call_schedule = [], []
		lesson_teacher_ind = columns_formed = call_schedule_formed = False
		while True:
						
			"""---------------------------------------Получение страницы------------------------------------------------------"""

			try:
				worksheet = self.google_sheets.get_worksheet(sheets_ind)
				worksheet_name = worksheet.title
			except gspread.exceptions.WorksheetNotFound:
				break
			except gspread.exceptions.APIError:
				self.google_sheets = self.client.open_by_url(self.url_google_sheets)
				worksheet = self.google_sheets.get_worksheet(sheets_ind)
				worksheet_name = worksheet.title
			except:
				raise Exception("Something went wrong by reading document")

			to_yield = dict.fromkeys(['course', 'education_type', 'groups'])

			if re.match(r"^[\s\n]*\d[\s\n]+(course|курс)[\s\n]*$", worksheet_name.strip().lower()):
				try:
					to_yield['course'] = int(worksheet_name.split()[0])
				except ValueError:
					raise Exception(f"Group name sheet doesn't match the pattern")

				if to_yield['course'] <= 0:
					raise Exception("Course number can't be less than 1")
			else:
				if worksheet_name != "info":
					warnings.warn(f"Unrecognised sheet '{worksheet_name}' in {self.current_url}, it's ignored")
				sheets_ind += 1
				continue
			
			"""---------------------------------------Считывание страницы------------------------------------------------------"""

			try:
				worksheet_data = worksheet.get_all_values()
			except gspread.exceptions.APIError:
				self.google_sheets = self.client.open_by_url(self.url_google_sheets)
				worksheet = self.google_sheets.get_worksheet(sheets_ind)
				worksheet_data = worksheet.get_all_values()

			# worksheet_data = worksheet.get_all_values()
			
			try:
				rowCount, columnCount = len(worksheet_data), worksheet.column_count
			except gspread.exceptions.APIError:
				self.google_sheets = self.client.open_by_url(self.url_google_sheets)
				worksheet = self.google_sheets.get_worksheet(sheets_ind)
				rowCount, columnCount = len(worksheet_data), worksheet.column_count
			
			# rowCount, columnCount = len(worksheet_data), worksheet.column_count

			"""---------------------------------------Обработка типа обучения--------------------------------------------------"""

			to_yield['education_type'] = ' '.join(next(filter(lambda elem: elem, worksheet_data[0])).lower().split())

			if to_yield['education_type'] not in EDUCATION_TYPES:
				raise Exception(f"Unrecognised education type: {to_yield['education_type']}")
			
			"""---------------------------------------Обработка названий групп--------------------------------------------------"""

			second_row = worksheet_data[1][2:-2]
			groups_information = [[], []]

			for buffer in filter(lambda group: group, second_row):
				buffer = re.split(r'[,|/&]+', buffer.replace('\n', ' '))
				if len(buffer) != 2:
					raise Exception(f"Irregularly shaped group name found on page '{worksheet_name}'")

				groups_information[0].append(buffer[0].strip().upper())
				if not groups_information[0][-1]:
					raise Exception(f"Irregularly shaped group number found on page {worksheet_name}")
				groups_information[1].append(' '.join(buffer[1].split()).lower())
				if not groups_information[1][-1]:
					groups_information[1][-1] = groups_information[0][-1]

			to_yield['groups'] = dict.fromkeys(groups_information[0])

			if len(groups_information[0]) != (columnCount - 4)//N_COLUMNS:
				raise Exception(f"Unnamed group found on page {worksheet_name}")
			second_row = None

			for group_number, group_name in zip(*groups_information):
				to_yield['groups'][group_number] = {'name': group_name, 'schedule': []}
			groups_information = groups_information[0]

			"""---------------------------------------Обработка столбцов расписания-----------------------------------------------"""

			third_row = worksheet_data[2]

			if not columns_formed:
				columns = list(map(lambda buffer: buffer.strip().lower(), third_row[2:N_COLUMNS+2]))
				columns = [columns[i] for i in range(N_COLUMNS) if columns[i] and 
							(not re.match(r".*название.*\s.*дисциплины.*\s.*преподаватель.*", columns[i]) or (lesson_teacher_ind:=i) != -1)]
				if len(set(columns)) != len(columns):
					raise Exception(f"Columns have duplicates in their names")
				elif lesson_teacher_ind is None:
					raise Exception(f"Missing column 'Название дисциплины, преподаватель'")

				columns_formed = True

			for j in range(2, columnCount - 2, N_COLUMNS):
				if [column.strip().lower() for column in third_row[j:j+N_COLUMNS]] != columns:
					raise Exception(f"Columns in second row don't match")
			third_row = None

			"""---------------------------------------Считывание расписания--------------------------------------------------------"""
			
			cur_day_of_week_index = cur_lesson_time = None
			for i in range(4, rowCount - 1):
				buffer_row = list(map(lambda elem: elem.strip(), worksheet_data[i - 1]))
				
				if buffer_row[0]:
					cur_day_of_week_index = DAY_OF_WEEK[buffer_row[0].lower()]
					cur_call_schedule_index = 0

				if buffer_row[1]:
					cur_lesson_time = buffer_row[1]
					if not call_schedule_formed and cur_lesson_time not in call_schedule:
						call_schedule.append(cur_lesson_time)
					elif not call_schedule_formed:
						call_schedule_formed = True
						yield {'call_schedule': call_schedule}
					elif cur_lesson_time not in call_schedule:
						raise Exception(f"Lesson time '{cur_lesson_time}' does not match 'call_schedule'")
					cur_call_schedule_index += 1

				for j in range(2, columnCount - 2, N_COLUMNS):

					if (buffer_information:=buffer_row[j:j+N_COLUMNS])[lesson_teacher_ind]:
						to_yield['groups'][groups_information[(j-2) // N_COLUMNS]]['schedule'].append([cur_day_of_week_index, cur_call_schedule_index] + \
							list(map(lambda elem: elem if elem else None, buffer_information)))
					elif any(map(lambda elem: not re.match(r'^[\s\n]*$', elem), buffer_information)):
						warnings.warn(f"Lesson in the cells ({i}, {j+1}):({i}, {j+N_COLUMNS}) weird, check columns")

			worksheet_data = None
			
			"""------------------------------------Возвращение информации обработанной страницы-----------------------------------"""

			yield to_yield
			sheets_ind += 1


if __name__ == '__main__':
	api = Google_API()
	api.open(url_google_sheets="https://docs.google.com/spreadsheets/d/1cbaadvTmieE714fNn2_Id_aua6nP7buFJJ2KzWF7CAQ")
	[print(returned) for returned in api.execute()]
