from flask import render_template, request, current_app, jsonify, send_from_directory
from app.SQLite import SQLite
import os
import logging

# TODO не существующее расписание для проверки ошибок

# logging.basicConfig(filename='app.log', level=logging.INFO)


@current_app.route('/')
def index():
	return render_template('index.html', unis_names=SQLite.get_unis_names())


# @current_app.before_request
# def log_request_info():
# 	logging.info('Request URL: %s', request.url)
# 	logging.info('Request Method: %s', request.method)
# 	logging.info('Request Headers: %s', request.headers)
# 	logging.info('Request Data: %s', request.get_data())


@current_app.route('/favicon.ico')
def favicon():
    return send_from_directory(current_app.root_path, 'favicon.ico', mimetype='image/vnd.microsoft.icon')


@current_app.route('/get_options', methods=['GET'])
def get_options():
	level = int(request.args.get('level'))

	match level:
		case 0:

			next_level_options, filename, information = SQLite.get_schedule_for_teacher(request.args)

			if not filename or not os.path.exists(current_app.static_folder + f"/images/{filename}"):
				filename = os.getenv('DEFAULT_TEACHER_IMAGE')
			
			return jsonify({'options': next_level_options, 'tag': 
				f'<a class="text-xl openModalButton" data-photo="{filename}" data-information="{information}">{request.args.get("teacher_name")}</a>'})
		case 1:
			next_level_options = SQLite.get_facs_names(request.args)
		case 2:
			next_level_options = SQLite.get_education_types(request.args)
		case 3:
			next_level_options = SQLite.get_courses(request.args)
		case 4:
			next_level_options = SQLite.get_groups_names(request.args)
		case 5:
			next_level_options = SQLite.get_schedule_for_students(request.args)

	return jsonify({'options': next_level_options})


@current_app.route('/get_photo/<string:filename>')
def get_photo(filename):
	return send_from_directory(current_app.static_folder + '/images', filename)


@current_app.route('/search', methods=['GET'])
def search():
	query = request.args.get('query', '')
	if query.strip():
		return jsonify(SQLite.get_teachers(request.args, query))
	else:
		return []


