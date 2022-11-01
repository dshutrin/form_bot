import sqlite3
import os


class Base:
	def __init__(self, path):
		if not os.path.exists(path):
			with open(path, 'w'):
				print('Файл базы данных создан!')
		self.conn = sqlite3.connect(path, check_same_thread=False)
		self.cur = self.conn.cursor()

	def init_tables(self):
		tables = [
			'users(vk_id integer, mode text)',
			'temp(user_id integer, name text, value text)'
		]

		for table in tables:
			print(f'check table <{table.split("(")[0]}>')
			self.cur.execute(f'create table if not exists {table};')

	def get_user(self, vk_id):
		data = [x for x in self.cur.execute(f'select * from users where vk_id={vk_id};')]
		if len(data) > 0:
			return data[0]
		else:
			self.cur.execute(f'insert into users(vk_id, mode) values({vk_id}, "start");')
			self.conn.commit()
			return [x for x in self.cur.execute(f'select * from users where vk_id={vk_id};')][0]

	def update_user_mode(self, vk_id, mode):
		self.cur.execute(f'update users set mode="{mode}" where vk_id={vk_id};')
		self.conn.commit()

	def add_temp_data(self, vk_id, name, value):
		self.cur.execute(f'insert into temp(user_id, name, value) values({vk_id}, "{name}", "{value}");')
		self.conn.commit()

	def get_user_temp(self, vk_id):
		return [{'name': x[1], 'value': x[2]} for x in self.cur.execute(
			f'select * from temp where user_id={vk_id}'
		)]

	def del_user_temp(self, vk_id):
		self.cur.execute(f'delete from temp where user_id={vk_id}')
		self.conn.commit()
