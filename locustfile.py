from datetime import datetime, timedelta
from locust import HttpUser, task, constant

"""Нагрузочное тестирование back-end сервисов платформы doc-crm.
    Выполняется на тестовых пользователях врача и пацента. """


class C:
    """
    Доступа для входа тестового пользователя и другие служебные переменные
    для корректного выполнения запросов нагрухочного тестирования.
    """

    USER = "test123@mail.ru"
    PASSWORD = 'mutabor123'
    TOKEN = None
    DOC_TOKEN = 'c58cea7ef6e89ca39f9401edb12d241d'
    PACIENT_TOKEN = 'e405b6a0007bcb86824d3bf5ef762b66'
    DIALOG_ID = None
    SCHEDULE_ID = None
    CONS_TOKEN = None


IS_STARTED, STOP_ALL = False, False


def headers():
    return {'Authorization': C.TOKEN}


class ClientTesting(HttpUser):
    """
    Класс для тестирования.
    - wait_time опеределяет задержку между запросами пользователей.
    - task(w) декоратор, который установит задачу для тестирования, где w - ее вес (частота запросов)
    """

    host = 'https://doc-crm.net/api/v3'
    wait_time = constant(5)

    def started(self) -> bool:
        global IS_STARTED, STOP_ALL
        if STOP_ALL:
            self.stop()
        if not IS_STARTED:
            IS_STARTED = True
            return False
        else:
            return True

    def on_start(self):
        """
        Авторизация, запись пациента на прием и новая консудльтацию.
        Инициализация служебных переменных.
        """
        if self.started():
            return

        # вход
        a = self.client.post("/signin", json={
            "login": C.USER,
            "password": C.PASSWORD
        })
        if a.ok:
            if not C.TOKEN:
                C.TOKEN = a.json()['data']['token']
            print('login success')
        else:
            print('login error', a.json())
            self.stop(force=True)

        # новое расписание врача
        now = datetime.now() + timedelta(hours=3)
        print(now)
        test_user_id = 34
        a = self.client.post(f"/user/{test_user_id}/schedule", json={
            "date": [
                f"{str(now.date())}T{int(now.hour)}:00:00.000Z"
            ]
        }, headers=headers())
        if a.ok:
            if not C.SCHEDULE_ID:
                C.SCHEDULE_ID = a.json()['data'][0]['id']
            print('schedule created')
        else:
            print('schedule error', a.json())
            self.stop(force=True)

        # новая консультация и диалог врача с пациентом
        a = self.client.post("/consultation", json={"doc_token": C.DOC_TOKEN,
                                                    "session_uid": "123",
                                                    "platform": 1,
                                                    "reason": "Причина тест",
                                                    "schedule_id": C.SCHEDULE_ID,
                                                    "patient_token": C.PACIENT_TOKEN,
                                                    "first_name": "name",
                                                    "middle_name": "middle",
                                                    "age": 25,
                                                    "phone": "+79155006631"
                                                    }, headers=headers())
        if a.ok:
            a = a.json()
            if not C.DIALOG_ID:
                C.DIALOG_ID = a['data']['dialog_id']
                C.PACIENT_TOKEN = a['data']['patient_token']
                C.CONS_TOKEN = a['data']['cons_token']
            print('consultation created')
        else:
            print('consultation error', a.json())
            self.stop(force=True)

    @task(5)
    def check_token(self):
        self.client.post('/session/check-token', json={'token': C.TOKEN}, headers=headers())

    @task(2)
    def doctor(self):
        self.client.get(f'/doctor?token={C.DOC_TOKEN}')

    @task(5)
    def schedule(self):
        self.client.get(f'/schedule?doc_token={C.DOC_TOKEN}')

    @task(1)
    def new_schedule(self):
        self.client.post("/schedule", json={
            "date": [
                f"{str(datetime.now().date())}T18:00:00.000Z"
            ]
        }, headers=headers())

    @task(1)
    def post_consultation(self):
        self.client.post("/consultation", json={"doc_token": C.DOC_TOKEN,
                                                "session_uid": "123",
                                                "platform": 1,
                                                "reason": "Причина тест",
                                                "schedule_id": C.SCHEDULE_ID,
                                                "patient_token": C.PACIENT_TOKEN,
                                                "first_name": "name",
                                                "middle_name": "middle",
                                                "age": 25,
                                                "phone": "+79155006631"
                                                }, headers=headers())

    @task(1)
    def consultation_check(self):
        self.client.post('/consultation/check', json={
            "doc_token": C.DOC_TOKEN,
            "patient_token": C.PACIENT_TOKEN
        }, headers=headers())

    @task(1)
    def consultation_info(self):
        self.client.get(f'/consultation/info?token={C.CONS_TOKEN}', headers=headers())

    @task(1)
    def consultation(self):
        self.client.get(f'/consultation/1', headers=headers())

    @task(2)
    def doctor_info(self):
        self.client.get(f'/doctor?token={C.DOC_TOKEN}', headers=headers())

    @task(1)
    def services(self):
        self.client.get('/catalog/service', headers=headers())

    @task(20)
    def create_mess(self):
        self.client.post(f'/dialog/{C.DIALOG_ID}/message', json={
            "_type": "text",
            "data": {
                "text": "Высоконагрузочное текстирование - сообщение"
            }
        }, headers=headers())

    @task(1)
    def login(self):
        self.client.post("/signin", json={
            "login": C.USER,
            "password": C.PASSWORD
        })
