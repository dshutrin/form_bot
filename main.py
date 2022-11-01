import vk_api
import utils
from vk_api.longpoll import VkEventType, VkLongPoll
from config import token
from base import Base
from classes import User
import config


class MyLongPoll(VkLongPoll):
	def listen(self):
		while True:
			try:
				for event in self.check():
					yield event
			except Exception as error:
				print(error)


class Bot:
	def __init__(self):
		self.vk_session = vk_api.VkApi(token=token)
		self.longpoll = MyLongPoll(self.vk_session)
		self.base = Base('data.db')
		self.base.init_tables()

		self.user_start_key = utils.get_vk_keyboard([
			[('Подать заявку на вступление в СКБ', 'зеленый')]
		])
		self.choice_key = utils.get_vk_keyboard([
			[('Да', 'зеленый'), ('Нет', 'синий')],
			[('Отменить', 'красный')]
		])
		self.confirm_key = utils.get_vk_keyboard([
			[('Отправить заявку', 'зеленый'), ('Отменить', 'синий')]
		])
		self.back_key = utils.get_vk_keyboard([
			[('Отменить', 'красный')]
		])
		self.clear_key = utils.get_vk_keyboard([])

	def sender(self, user_id, text, key):
		self.vk_session.method('messages.send', {'user_id': user_id, 'message': text, 'random_id': 0, 'keyboard': key})

	def get_name(self, vk_id):
		data = self.vk_session.method('users.get', {'user_id': vk_id})[0]['first_name']
		return data

	def start(self):
		for event in self.longpoll.listen():
			if event.type == VkEventType.MESSAGE_NEW and event.to_me:

				user_id = event.user_id
				msg = event.message
				user = User(self.base.get_user(user_id))

				if msg == 'Начать':
					self.base.update_user_mode(user.vk_id, 'start')
					self.sender(user.vk_id, f'Привет, {self.get_name(user.vk_id)}!\nВыбери действие:', self.user_start_key)

				else:
					if user.mode == 'start':
						if msg == 'Подать заявку на вступление в СКБ':
							self.sender(user.vk_id, 'Ваше имя и фамилия совпадают с данными VK?', self.choice_key)
							self.base.update_user_mode(user.vk_id, 'confirm_vk_data')

					elif user.mode == 'confirm_vk_data':
						if msg == 'Да':
							user_name = self.get_name(user.vk_id)
							user_surname = self.vk_session.method('users.get', {'user_id': user.vk_id})[0]['last_name']

							self.base.add_temp_data(user.vk_id, 'name', user_name)
							self.base.add_temp_data(user.vk_id, 'surname', user_surname)

							self.sender(
								user.vk_id,
								'Введите название вашей группы\nЕсли её нет - так и напишите!',
								self.back_key
							)
							self.base.update_user_mode(user.vk_id, 'get_group_name')

						elif msg == 'Нет':
							self.sender(user.vk_id, 'Введите своё имя:', self.back_key)
							self.base.update_user_mode(user.vk_id, 'input_name')

						elif msg == 'Отменить':
							self.base.del_user_temp(user.vk_id)
							self.base.update_user_mode(user.vk_id, 'start')
							self.sender(user.vk_id, f'Привет, {self.get_name(user.vk_id)}!\nВыбери действие:', self.user_start_key)

					elif user.mode == 'input_name':
						if msg == 'Отменить':
							self.base.del_user_temp(user.vk_id)
							self.base.update_user_mode(user.vk_id, 'start')
							self.sender(user.vk_id, f'Привет, {self.get_name(user.vk_id)}!\nВыбери действие:', self.user_start_key)

						else:
							self.base.add_temp_data(user.vk_id, 'name', msg)
							self.sender(user.vk_id, 'Введите свою фамилию:', self.back_key)
							self.base.update_user_mode(user.vk_id, 'input_surname')

					elif user.mode == 'input_surname':
						if msg == 'Отменить':
							self.base.del_user_temp(user.vk_id)
							self.base.update_user_mode(user.vk_id, 'start')
							self.sender(user.vk_id, f'Привет, {self.get_name(user.vk_id)}!\nВыбери действие:', self.user_start_key)

						else:
							self.base.add_temp_data(user.vk_id, 'surname', msg)
							self.sender(
								user.vk_id,
								'Введите название вашей группы\nЕсли её нет - так и напишите!',
								self.back_key
							)
							self.base.update_user_mode(user.vk_id, 'get_group_name')

					elif user.mode == 'get_group_name':
						if msg == 'Отменить':
							self.base.del_user_temp(user.vk_id)
							self.base.update_user_mode(user.vk_id, 'start')
							self.sender(user.vk_id, f'Привет, {self.get_name(user.vk_id)}!\nВыбери действие:', self.user_start_key)

						else:
							self.base.add_temp_data(user.vk_id, 'group', msg)
							self.sender(
								user.vk_id,
								'Введите свой номер телефона (8xxxxxxxxxx):',
								self.back_key
							)
							self.base.update_user_mode(user.vk_id, 'get_phone')

					elif user.mode == 'get_phone':
						if msg == 'Отменить':
							self.base.del_user_temp(user.vk_id)
							self.base.update_user_mode(user.vk_id, 'start')
							self.sender(user.vk_id, f'Привет, {self.get_name(user.vk_id)}!\nВыбери действие:', self.user_start_key)

						else:
							if len(msg) == 11 and msg.isdigit():
								self.base.add_temp_data(user.vk_id, 'phone', msg)
								self.sender(user.vk_id, 'Укажите, какими навыками вы владеете, и чем хотели-бы занимать в СКБ:', self.back_key)
								self.base.update_user_mode(user.vk_id, 'get_comment')
							else:
								self.sender(user.vk_id, 'Номер телефона должен состоять из 11 цифр!', self.back_key)

					elif user.mode == 'get_comment':
						if msg == 'Отменить':
							self.base.del_user_temp(user.vk_id)
							self.base.update_user_mode(user.vk_id, 'start')
							self.sender(user.vk_id, f'Привет, {self.get_name(user.vk_id)}!\nВыбери действие:', self.user_start_key)

						else:
							self.base.add_temp_data(user.vk_id, 'comment', msg)
							data = self.base.get_user_temp(user.vk_id)

							name = [x for x in data if x['name'] == 'name'][0]['value']
							surname = [x for x in data if x['name'] == 'surname'][0]['value']
							group = [x for x in data if x['name'] == 'group'][0]['value']
							phone = [x for x in data if x['name'] == 'phone'][0]['value']
							comment = [x for x in data if x['name'] == 'comment'][0]['value']

							out_form = f'Новая заявка на вступление в СКБ!\nКандидат: '\
								f'[id{user.vk_id}|{name} {surname}]\nГруппа: {group}\nНомер телефона: {phone}\n'\
								f'Комментарий кандидата (увлечения):\n{comment}'
							self.sender(
								user.vk_id,
								f'Проверьте правильность вашей заявки:\n\n{out_form}',
								self.confirm_key
							)
							self.base.update_user_mode(user.vk_id, 'confirm_form')

					elif user.mode == 'confirm_form':
						if msg == 'Отменить':
							self.base.del_user_temp(user.vk_id)
							self.base.update_user_mode(user.vk_id, 'start')
							self.sender(user.vk_id, f'Привет, {self.get_name(user.vk_id)}!\nВыбери действие:', self.user_start_key)

						elif msg == 'Отправить заявку':
							data = self.base.get_user_temp(user.vk_id)
							print(data)

							name = [x for x in data if x['name'] == 'name'][0]['value']
							surname = [x for x in data if x['name'] == 'surname'][0]['value']
							group = [x for x in data if x['name'] == 'group'][0]['value']
							phone = [x for x in data if x['name'] == 'phone'][0]['value']
							comment = [x for x in data if x['name'] == 'comment'][0]['value']

							out_form = f'Новая заявка на вступление в СКБ!\nКандидат: '\
								f'[id{user.vk_id}|{name} {surname}]\nГруппа: {group}\nНомер телефона: {phone}\n'\
								f'Комментарий кандидата (увлечения):\n{comment}'
							self.sender(
								config.ADMIN_ID,
								out_form,
								self.clear_key
							)
							self.sender(
								user.vk_id,
								'Ваша заявка отправлена администрации СКБ ФКТ!\nВ ближайшее время с вами свяжутся!',
								self.clear_key
							)
							self.base.update_user_mode(user.vk_id, 'start')
							self.base.del_user_temp(user.vk_id)


if __name__ == '__main__':
	Bot().start()
