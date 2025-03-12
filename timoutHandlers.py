from aiogram import Router
import datetime
from db import *
from middlewares import *
from text import *
import kb

from aiogram.exceptions import TelegramForbiddenError

router = Router()

TIME_FOR_ACCEPT_IN_MINUTES = 5
TIME_FOR_DONE_IN_MINUTES = 0.5
COORDINATOR_SEQUENCE = -1

def setup_scheduler(scheduler, bot):
    scheduler.add_job(garbage_lost_tasks, "interval", seconds=10, args=[bot])

def register_handlers(dp):
    dp.include_router(router)

async def garbage_lost_tasks(bot):
    global TIME_FOR_ACCEPT_IN_MINUTES, TIME_FOR_DONE_IN_MINUTES, COORDINATOR_SEQUENCE
    tasks = Task.select()
    coordinators = Users.select().where((Users.role == 'coordinator') & (Users.working_status == True))
    for coordinator in coordinators:
        print(coordinator.tg_username)
    COORDINATOR_SEQUENCE += 1
    hasCoordinator = False
    if len(coordinators) > 0:
        COORDINATOR_SEQUENCE %= len(coordinators)
        hasCoordinator = True

    COORDINATOR_SEQUENCE = 0
    
    current_time = datetime.datetime.now()
    for task in tasks:
        if task.datetimestamp_sent and (current_time - task.datetimestamp_sent).total_seconds()/60 > TIME_FOR_ACCEPT_IN_MINUTES:
            if task.scouts:
                scouts_messages = task.scouts
                index_list = scouts_messages.split()

                if hasCoordinator:
                    try:
                        sent_coordinator = await send2Coordinator_bot(bot, coordinators, COORDINATOR_SEQUENCE, task.msg_text, 
                                                errorText.coordinator_errors['no_time_accept'], 
                                                index_list[0], index_list[1])
                        
                        if sent_coordinator:
                            task.coord_id = coordinators[COORDINATOR_SEQUENCE].id
                            task.coord_msg = sent_coordinator.message_id
                            task.err_id = list(errorText.coordinator_errors.values()).index(errorText.coordinator_errors['no_time_accept'])
                            # COORDINATOR_SEQUENCE += 1
                            # COORDINATOR_SEQUENCE %= len(coordinators)
                    except TelegramForbiddenError:
                        await banned_from_coordinator(bot, coordinators[COORDINATOR_SEQUENCE].id, task)
                else:
                    await auto_cancel_task(bot, task)

                for i in range(0, len(index_list), 2):
                    try:
                        await bot.delete_message(chat_id=index_list[i], message_id=index_list[i+1])
                    except:
                        pass
                    try:
                        await send_msg(bot, index_list[i], errorText.no_time_accept_scout, None, None)
                    except:
                        try:
                            scout = Users.get(id=index_list[i])
                            await banned_from_scout(bot, scout, task)
                        except:
                            break

                task.datetimestamp_sent = None
                task.scouts = None
                task.save()
        
        if task.datetimestamp_accepted and (current_time - task.datetimestamp_accepted).total_seconds()/60 > TIME_FOR_DONE_IN_MINUTES:
            if hasCoordinator:
                try:
                    sent_coordinator = await send2Coordinator_bot(bot, coordinators, COORDINATOR_SEQUENCE, task.msg_text, 
                                            errorText.coordinator_errors['no_time_done'], 
                                            task.scoutfk.id, task.msg_id_scout)
                    
                    if sent_coordinator:
                        task.coord_id = coordinators[COORDINATOR_SEQUENCE].id
                        task.coord_msg = sent_coordinator.message_id
                        task.err_id = list(errorText.coordinator_errors.values()).index(errorText.coordinator_errors['no_time_done'])
                        task.datetimestamp_accepted = None
                        task.datetimestamp_sent = None
                        task.scouts = None
                        task.save()
                except TelegramForbiddenError:
                    await banned_from_coordinator(bot, coordinators[COORDINATOR_SEQUENCE].id, task)

                try:
                    await bot.delete_message(chat_id=task.scoutfk.id, message_id=task.msg_id_scout)
                except:
                    pass
                await send_msg(bot, task.scoutfk.id, errorText.no_time_done_scout, None, None)
                task.scoutfk = None
                task.msg_id_scout = None
                task.save()
            else:
                await auto_cancel_task(bot, task)
