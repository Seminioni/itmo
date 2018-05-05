import faker
import random
import multiprocessing

import constants
from cassandra.cluster import Cluster


PROCESS_NUMBER = 2


class CassandraFillerFakes(faker.providers.BaseProvider):
    def __init__(self, *args, **kwargs):
        super(CassandraFillerFakes, self)
        self.fake = faker.Faker()

    def register(self):
        return {
                'day': "'{}'".format(self.fake.date()),
                'user_id': 'uuid()',
                'device_type': "'{}'".format(random.choice(constants.DEVICE_TYPES)),
                'event_time': "'{} {}.123'".format(self.fake.date(), self.fake.time())
        }

    def user_activity(self):
        return {
                'user_id': 'uuid()',
                'event_type': "'{}'".format(random.choice(constants.EVENT_TYPES)),
                'device_type': "'{}'".format(random.choice(constants.DEVICE_TYPES)),
                'event_time': "dateOf(now())"
        }

    def enter_attempts(self):
        return {
                'day': "toDate(now())",
                'user_id': 'uuid()',
                'device_type': "'{}'".format(random.choice(constants.DEVICE_TYPES)),
                'event_time': "dateOf(now())"
        }


class CassandraFiller:
    def __init__(self):
        self.cluster = Cluster()
        self.session = self.cluster.connect(constants.KEYSPACE_NAME)
        self.faker = faker.Faker()
        self.faker.add_provider(CassandraFillerFakes)

    def _get_table_data(self, table):
        query = 'SELECT * FROM {}'.format(table)
        return self.session.execute(query)

    def get_user_activity(self):
        return self._get_table_data(constants.DB_USER_ACTIVITY)

    def get_register(self):
        return self._get_table_data(constants.DB_REGISTER)

    def get_enter_attempts_by_day(self):
        return self._get_table_data(constants.DB_ENTER_ATTEMPTS)

    def _insert_record(self, database, record, ttl=''):
        query = "INSERT INTO {}{} VALUES ({}) {};" \
            .format(database, constants.DATABASES_COLUMNS[database], record, ttl)
        # print(query)
        self.session.execute(query)

    def insert_register_record(self, data=None):
        if not data:
            data = self.faker.register()

        values = ''

        for key in data.keys():
            values += str(data[key])
            values += ', '
        self._insert_record(constants.DB_REGISTER, values[:-2])

    def insert_registers(self, records_number):
        for user_id in range(records_number):
            data = self.faker.register()
            self.insert_register_record(data)

    def insert_user_activity_record(self, data=None):
        if not data:
            data = self.faker.user_activity()

        ttl = ''
        values = ''

        for key in data.keys():
            values += str(data[key])
            values += ', '
        self._insert_record(constants.DB_USER_ACTIVITY, values[:-2], ttl)

    def insert_user_activities(self, records_number):
        for _ in range(records_number):
            data = self.faker.user_activity()
            self.insert_user_activity_record(data)

    def insert_enter_attempts_record(self, data=None):
        if not data:
            data = self.faker.enter_attempts()

        values = ''
        for key in data.keys():
            values += str(data[key])
            values += ', '
        self._insert_record(constants.DB_ENTER_ATTEMPTS, values[:-2])

    def insert_enter_attempts(self, records_number):
        for _ in range(records_number):
            data = self.faker.enter_attempts()
            self.insert_enter_attempts_record(data)

    def remove_registers_by_uuids(self, uuids):
        self.session.execute('DELETE FROM register WHERE user_id IN ({});'.format(uuids))

    def update_register_by_uuid(self, update_str,  uuids):
        self.session.execute('UPDATE register SET {} WHERE user_id IN ({});'.format(update_str, uuids))


def fill():
    filler = CassandraFiller()
    # activity = filler.get_register()
    # filler.insert_registers(200000)
    # filler.insert_user_activities(200000)
    filler.insert_enter_attempts(200)


def multiprocessing_fill():
    workers = []
    for i in range(PROCESS_NUMBER):
        workers.append(multiprocessing.Process(target=fill))

    for worker in workers:
        worker.start()

    for worker in workers:
        worker.join()


if __name__ == '__main__':
    filler = CassandraFiller()
    # activity = filler.get_register()
    # filler.insert_registers(20)
    # print(list(activity))
    # filler.insert_register({'day': "'2018-01-03'", #'toconstants.Date(now())',
    #                         'user_id': i,
    #                         'device_type': "'mobile'",
    #                         'event_time':  'dateOf(now())'})
    # multiprocessing_fill()
    # filler.insert_user_activities(200000)
    filler.insert_registers(200000)
    # filler.insert_enter_attempts(20002)
    # filler.remove_registers_by_uuids('bb1ed1ec-28b6-4b93-9ffa-e0e0d40d73da')
    # filler.update_register_by_uuid("device_type = 'mobile'", '834cd519-b58b-490d-bf3e-953da8cdc8de')
