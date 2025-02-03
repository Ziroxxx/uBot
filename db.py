from peewee import *

database = PostgresqlDatabase('urentDB', **{'host': 'localhost', 'port': 5432, 'user': 'postgres', 'password': 'klopa228'})

class UnknownField(object):
    def __init__(self, *_, **__): pass

class BaseModel(Model):
    class Meta:
        database = database

class Zone(BaseModel):
    name = TextField()
    status = TextField()
    ao = TextField()

    class Meta:
        table_name = 'zone'

class Coordinate(BaseModel):
    latitude = DoubleField()
    longitude = DoubleField()
    zonefk = ForeignKeyField(column_name='zonefk', field='id', model=Zone)

    class Meta:
        table_name = 'coordinate'

class Users(BaseModel):
    id = BigAutoField()
    role = TextField()
    tg_username = TextField()
    working_status = BooleanField(null=True)

    class Meta:
        table_name = 'users'

class Task(BaseModel):
    admin_chat = BigIntegerField()
    msg_id_scout = BigIntegerField(null=True)
    msg_status = BigIntegerField(null=True)
    msg_text = TextField(null=True)
    coord_id = BigIntegerField(null=True)
    coord_msg = BigIntegerField(null=True)
    scoutfk = ForeignKeyField(column_name='scoutfk', field='id', model=Users, null=True)

    class Meta:
        table_name = 'task'

class Mm(BaseModel):
    zonefk = ForeignKeyField(column_name='zonefk', field = 'id', model=Zone)
    scoutfk = ForeignKeyField(column_name='scoutfk', field='id', model=Users)

    class Meta:
        table_name = 'mm'

class boss_task(BaseModel):
    id_boss = BigIntegerField()
    id_msg = BigIntegerField()
    id_task = ForeignKeyField(column_name='id_task', field='id', model=Task)

    class Meta:
        table_name = 'boss_task'

