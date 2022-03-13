import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import random
import datetime
from requests import get
import re
import logging

logging.basicConfig(
    filename='example.log',
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
)


class VkBot:
    def __init__(self, token: str, group_id: str):
        self.token = token
        self.group_id = group_id
        self.vk_session = vk_api.VkApi(
            token=self.token,
        )
        long_poll = VkBotLongPoll(self.vk_session, group_id=self.group_id)

        self.vk = None
        self.user = None
        self.last_message = None

        self.run(long_poll)

    def run(self, long_poll: VkBotLongPoll):
        for event in long_poll.listen():
            if event.type == VkBotEventType.MESSAGE_NEW:
                print(event)
                print('Новое сообщение: ')
                print('Для меня от:', event.obj.message['from_id'])
                print('Текст:', event.obj.message['text'])
                self.vk = self.vk_session.get_api()
                self.user = self.vk.users.get(user_id=event.obj.message['from_id'])
                print(self.user)
                self.text_message = re.sub(r'[^\w\s]', '', event.obj.message['text'].lower())
                if self.send_salutation_message() or \
                        self.send_help_message() or \
                        self.send_time_message() or \
                        self.send_wiki_message() or \
                        self.send_last_message():
                    self.user = None
                    self.vk = None
                    continue

    def missed(self, name) -> bool:
        if self.user is None or self.vk is None:
            logging.warning(name)
            return True
        return False

    def send_last_message(self) -> bool:
        if self.missed('send_last_message'):
            return False
        message = f'Извините, {self.user[0]["first_name"]}, я вас не понимаю('
        self.vk.messages.send(user_id=self.user[0]['id'],
                              message=message,
                              random_id=random.randint(0, 2 ** 64))
        return True

    def send_salutation_message(self) -> bool:
        if self.missed('send_salutation_message'):
            return False
        if {'привет', "хай", 'дарова', "даров", 'q', 'ку'} & set(self.text_message.split()):
            current_message = f"Привет, {self.user[0]['first_name']}"
            current_message += '\nЕсли хотите узнать больше о функционале введите:\n'
            current_message += '"Помощь" или "Help"'
            self.vk.messages.send(user_id=self.user[0]['id'],
                                  message=current_message,
                                  random_id=random.randint(0, 2 ** 64))
            if 'city' in self.user[0]:
                self.vk.messages.send(user_id=self.user[0]['id'],
                                      message=f"Кстати, как ты поживаешь в {self.user[0]['city']}?",
                                      random_id=random.randint(0, 2 ** 64))
            return True
        return False

    def send_help_message(self) -> bool:
        if self.missed('send_help_message'):
            return False
        if 'help' in self.text_message \
                or 'помощь' in self.text_message:
            help_message = 'Так же у нас есть функция времени!! просто попросите сказать время!!'
            help_message += 'Вы так же можете у нас про что-нибудь спросить, к примеру\n'
            help_message += 'Что такое Цитрус? (нужно соблюдать формат Что такое ...)'
            self.vk.messages.send(user_id=self.user[0]['id'],
                                  message=help_message,
                                  random_id=random.randint(0, 2 ** 64))
            return True
        return False

    def send_time_message(self) -> bool:
        if self.missed('send_time_message'):
            return False
        message = ''
        for i in ['время', 'число', 'дата', 'день']:
            if i in self.text_message:
                message = str(datetime.datetime.now())
                message += '\n Вот лови, а то у тебя же нет блин часов под руками гений.'
        if message == '':
            return False
        self.vk.messages.send(user_id=self.user[0]['id'],
                              message=message,
                              random_id=random.randint(0, 2 ** 64))
        return True

    def send_wiki_message(self) -> bool:
        if self.missed('send_wiki_message'):
            return False
        if 'что такое' in self.text_message:
            wiki_ans = "Информацию которую вы могли иметь ввиду: \n"
            word = self.text_message.split()[-1]
            wiki_response = \
                'https://ru.wikipedia.org/w/api.php?action=opensearch&search={}&prop=info&format=json'.format(
                    word)
            response = get(url=wiki_response)
            if response.status_code == 200:
                response = response.json()
                for i, j in zip(response[1], response[3]):
                    wiki_ans += str(i) + ' : ' + str(j) + '\n'
            else:
                wiki_ans = 'Неправильный запрос!'
            self.vk.messages.send(user_id=self.user[0]['id'],
                                  message=f"{wiki_ans}",
                                  random_id=random.randint(0, 2 ** 64))
            return True
        return False


if __name__ == '__main__':
    bot = VkBot(
        token='',
        group_id='211537007',
    )
