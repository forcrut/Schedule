# # from . import db


# # class User(db.Model):
# # 	id = db.Column(db.Integer, primary_key=True)
# # 	username = db.Column(db.String(), unique=True, nullable=False)
# # 	email = db.Column(db.String(), unique=True, nullable=False)

# # 	def __repr__(self):
# # 		return f"<User {self.username}>"


# from flask import render_template, request, current_app, jsonify, session
# from app.SQLite import SQLite


# @current_app.route('/')
# def index():
#     return render_template('index_2.html', unis_names=SQLite.get_unis_names())


# # @close_db.route('/favicon.ico')
# # def favicon():
# #     return send_from_directory(app.root_path, 'favicon.ico', mimetype='image/vnd.microsoft.icon')


# @current_app.route('/get_options', methods=['GET'])
# def get_options():
# 	level = int(request.args.get('level'))
# 	selected_value = request.args.get('selected_value')

# 	match level:
# 		case 1:
# 			next_level_options = get_db(selected_value).get_facs_names()
# 		case 2:
# 			next_level_options = get_db().get_education_types(fac_name=selected_value.upper())
# 		case 3:
# 			next_level_options = get_db().get_courses(education_type=selected_value.lower())
# 		case 4:
# 			next_level_options = get_db().get_groups_names(course=selected_value)
# 		case 5:
# 			next_level_options = get_db().get_schedule_for_students(group_name=selected_value)

# 	return jsonify({'options': next_level_options})


# # @current_app.route('/get_options', methods=['GET'])
# # def get_options():
# # 	level = int(request.args.get('level'))
# # 	selected_value = request.args.get('selected_value')

# # 	match level:
# # 		case 1:
# # 			try:
# # 				global sqlite
# # 				sqlite.close_connection()
# # 			except NameError:
# # 				pass
# # 			finally:
# # 				sqlite = SQLite(selected_value)

# # 			next_level_options = sqlite.get_facs_names()
# # 		case 2:
# # 			next_level_options = sqlite.get_education_types(fac_name=selected_value.upper())
# # 		case 3:
# # 			next_level_options = sqlite.get_courses(education_type=selected_value.lower())
# # 		case 4:
# # 			next_level_options = sqlite.get_groups_names(course=selected_value)
# # 		case 5:
# # 			next_level_options = sqlite.get_schedule_for_students(group_name=selected_value)

# # 	return jsonify({'options': next_level_options})


# @current_app.route('/search', methods=['GET'])
# def search():
# 	query = request.args.get('query', '')
# 	if len(query) >= 2:
# 		try:
# 			global sqlite
# 			sqlite.close_connection()
# 		except NameError:
# 			pass
# 		finally:
# 			sqlite = SQLite(request.args.get('uni_name'))

# 		return jsonify(sqlite.get_teachers(query))
# 	else:
# 		return []


