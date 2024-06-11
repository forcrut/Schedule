import gspread as gs
import os
import re


FROM_ROW = 4
TO_ROW = 4
N_COLUMNS = 4
COURSES = ["3 курс", "4 курс"]  # "1 курс", "2 курс",
# количество записей в одной паре(8.15-9.35, ...)
ROWS_IN_LESSON = 4 
LESSONS_IN_DAY = 9

with open(os.path.join(os.path.dirname(__file__), '.env'), 'r') as file:
	for line in file:
		# Игнорируем пустые строки и строки, начинающиеся с #
		line = line.strip()
		if line and not line.startswith('#'):
			key, value = line.strip().split('=', 1)
			os.environ[key] = value


client_json = {
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

client = gs.service_account_from_dict(client_json)

sheets_from = client.open_by_url("https://docs.google.com/spreadsheets/d/1ebR4EpF48LlKPRo82aDT1ojHU7uzBi1BvcJCCgQKeUY")
sheets_to = client.open_by_url("https://docs.google.com/spreadsheets/d/1cbaadvTmieE714fNn2_Id_aua6nP7buFJJ2KzWF7CAQ")

audiences = ['"{}/"&info!$A4', '"{}/"&info!$A11', '"{}/"&info!$A12']
form_audiences = lambda aud, encl_id: '=' + audiences[int(encl_id)].format(aud,)


for name in COURSES:
	print(f"------------Insert into '{name}' sheet------------")
	row_len = lesson_counter = day_counter = None
	row_ind = TO_ROW
	worksheet_from = sheets_from.worksheet(name)
	worksheet_data = worksheet_from.get_all_values()

	worksheet_to = sheets_to.worksheet(name)

	for buffer_row in worksheet_data[FROM_ROW - 1:]:
		if row_len is None:
			row_len = len(buffer_row[2:-2])
		buffer_to = []

		# TODO
		if buffer_row[0]:
			if day_counter is not None:
				row_ind += ROWS_IN_LESSON * LESSONS_IN_DAY - day_counter
				lesson_counter = None
			day_counter = 0

		if buffer_row[1]:
			if lesson_counter is not None and lesson_counter < ROWS_IN_LESSON:
				row_ind += ROWS_IN_LESSON - lesson_counter
				day_counter += ROWS_IN_LESSON - lesson_counter
			lesson_counter = 0
		
		for lesson in [buffer_row[2 + i*N_COLUMNS:2 + (i+1)*N_COLUMNS] for i in range(row_len//N_COLUMNS)]:
			# if lesson[1]:
			print(f"----------------------------------------------------------")
			print(f"Lesson: {lesson}")
			lesson = list(map(lambda elem: elem.strip(), lesson))
			for lesson_elem_id in range(N_COLUMNS):
				match lesson_elem_id:
					case 0:
						if len(lesson[0].split()) == 2:
							buffer_to += lesson[0].split()
						elif len(lesson[0]) > 1:
							buffer_to += ["", lesson[lesson_elem_id]]
						else:
							buffer_to += [lesson[lesson_elem_id], ""]
					case 2:
						buffer_to.append(lesson[lesson_elem_id])
						buffer_to += ["", ""]
					case 1:
						if not lesson[lesson_elem_id].strip():
							buffer_to.append("")
						else:
							typer = input(f"В ячейке находиться {lesson[lesson_elem_id]}\nЕсли хотите изменить, то введите новое значение ячейки,\n если нет, то прожмите Enter: ").strip()
							buffer_to.append(f'="{typer if typer else lesson[lesson_elem_id]}"'.replace('\\n', '"&СИМВОЛ(10)&"').replace('\n', '"&СИМВОЛ(10)&"'))
						# buffer_to.append(f'="{typer if typer else lesson[lesson_elem_id]}"'.replace('\\n', '"&СИМВОЛ(10)&"').replace('\n', '"&СИМВОЛ(10)&"'))
					case 3:
						if not lesson[lesson_elem_id].strip():
							buffer_to.append("")
						elif re.search(r'(ФМО|фмо)', lesson[lesson_elem_id]):
							# lesson[lesson_elem_id].lower().split("фмо")[0].strip()
							print(f'Аудитория: {lesson[lesson_elem_id].lower().replace("фмо", "").strip()}')
							buffer_to.append(f'{form_audiences(lesson[lesson_elem_id].lower().split("фмо")[0].strip(), 1)}')
						elif re.search(r'(ГЕОФ|геоф)', lesson[lesson_elem_id]):
							# lesson[lesson_elem_id].lower().split("геоф")[0].strip()
							print(f'Аудитория: {lesson[lesson_elem_id].lower().replace("геоф", "").strip()}')
							buffer_to.append(f'{form_audiences(lesson[lesson_elem_id].lower().split("геоф")[0].strip(), 2)}')
						else:
							# typer = input(f"""
							# 		В ячейке находиться {lesson[lesson_elem_id]}
							# 		Если хотите изменить, то введите новое значение ячейки и цифру через пробел
							# 		0 для главного корпуса, 1 для ФМО, 2 для Географического
							# 		для отображения правильного корпуса: """).strip()
							# if not typer:
							buffer_to.append(f'{form_audiences(lesson[lesson_elem_id], 0)}')
							# else:
							# 	buffer_to.append(f'{form_audiences(*typer.split())}')

		print(f"To_insert: {buffer_to}")
		worksheet_to.update(range_name=f'C{row_ind}:{gs.utils.rowcol_to_a1(row_ind,  row_len + 3 * row_len//N_COLUMNS + 2)}', values=[buffer_to], raw=False)
		lesson_counter += 1
		day_counter += 1
		row_ind += 1
	# break
