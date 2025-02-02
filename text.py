class infoText:
    hello = 'Привет! Я зарегистрировал тебя. Дождись, пока руководство выдаст тебе роль внутри бота!\nДля проверки своей роли снова воспользуйся /start'
    admin = 'Вы админ бота!'
    sScout = 'Вы СИТ!'
    scout = 'Вы скаут!'
    boss = 'Вы босс!'
    coordinator = 'Вы координатор!'
    admin_tag_change = 'Введите @тег пользователя, права которого вы хотите изменить.'
    coordinator_tag_deligate = '\n\n<b>Отправьте @Тэг скаута!</b>'
    option = 'Выберите опцию по кнопкам ниже'
    load_map = 'Отправьте JSON файл зон, сгенерированный с Яндекс карт\nСсылка: https://yandex.ru/map-constructor'
    success_load = 'Новые данные успешно загружены в базу данных.'
    optional_caption = "Вы можете (опционально) отправить поясняющий текст для скаута. Если не нужно - отправьте '.'"
    choose_ao = 'Выбирете административную область (АО) для выхода на слот.'
    leaved = 'Вы вышли со слота(ов).'

    def found_tag_answer(tag, user_id):
        return f"ID пользователя {tag} найден: {user_id}. Теперь укажите его роль ('Администратор', 'Координатор', 'Скаут', 'Босс', 'СИТ', 'non-role')."
    
    def updated_role_admin(role):
        return f"Пользователь обновлен с ролью: {role}."
    
    def updated_role_user(role):
        return f"🎉 Вам обновили роль, ваша роль {role}"
    
    def scout_accepted(id_task):
        return f"Ваше задание #{id_task} принято в работу."

    def photo_prove(id_task):
        return f"\n<b>Отправьте фото-подтверждение (можно добавить и текст)📋\n#{id_task}</b>"
    def entered_slot(zone_msg):
        return f"Вы вышли на слот {zone_msg}"
    
    def task_scout_done(task_id):
        return f"Ваши результаты по заданию #{task_id} отправлены координатору ✅"

class msgStatusText:
    def first_stage(task_text, string_coords, task_id):
        return (f"Ваше сообщение\n{'-'*30}\n<i>{task_text.replace(string_coords, '<code>'+string_coords+'</code>')}</i>\n{'-'*30}\nотправлено скаутам на зоне!\n\n"
                f"<b>Номер задания: #{task_id}\n</b>"
                f"<b>Статус принято:       ❌❌❌</b>\n<b>Статус выполнено:\t❌❌❌</b>")
    
    def second_stage(task_text, string_coords, task_id):
        return (f"Ваше сообщение\n{'-'*30}\n<i>{task_text.replace(string_coords, '<code>'+string_coords+'</code>')}</i>\n{'-'*30}\nотправлено скаутам на зоне!\n\n"
                f"<b>Номер задания: #{task_id}\n</b>"
                f"<b>Статус принято:       ✅✅✅</b>\n<b>Статус выполнено:\t❌❌❌</b>")
    
    def third_stage(task_text, string_coords, task_id):
        return (f"Ваше сообщение\n{'-'*30}\n<i>{task_text.replace(string_coords, '<code>'+string_coords+'</code>')}</i>\n{'-'*30}\nотправлено скаутам на зоне!\n\n"
                f"<b>Номер задания: #{task_id}</b>\n"
                f"<b>Статус принято:       ✅✅✅</b>\n<b>Статус выполнено:\t✅✅✅</b>")

class errorText:
    non_role = '⚠️ Вы пока ещё не получили роль.'
    no_rights = '🚫 Вы не имеете прав на это действие!'
    not_scout = '🚫 Вы не скаут.'
    tag_err = "⚠️ Тег должен начинаться с '@'. Попробуйте снова."
    no_user_by_tag = '⚠️ Не удалось найти пользователя с таким тегом. Убедитесь, что тег указан верно'
    invalid_role = '⚠️ Неверная роль. Укажите одну из: администратор, координатор, скаут или non-role.'
    already_in_use = '⚠️ Это задание уже было взято в работу другим скаутом (или вами).'

    update_db_warning = '⚠️ Было сделано обновление зон, войдите на слот еще раз!'
    invalid_ao = '⚠️ Вы выбрали несуществующую АО! Пользуйтесь клавиатурой'
    invalid_zone = '⚠️ Вы выбрали зону не из списка, попробуйте еще раз.'
    not_entered = '⚠️ Вы еще не вышли на слот.'
    no_zones = '⚠️ В данный момент в базе данных нет зон'
    no_description = '⚠️ Есть зона без описания, перепроверьте файл!'
    no_ao = '⚠️ Есть зона без деления на АО (должна быть запятая), перепроверьте файл!'
    no_photo = '⚠️ Вы не прикрепили фото, пожалуйста прикрепите фото.'

    failed_json = '⚠️ Не удалось декодировать файл как JSON. Пожалуйста, убедитесь, что файл имеет корректный формат GeoJSON.'
    failed_load = '⚠️ Не удалось загрузить файл.'
    no_geoJSON = '⚠️ Пожалуйста, отправьте файл в формате GeoJSON.'

    no_photo_or_text = '⚠️ Нет текста или фото.'
    unknown_point = '⚠️ Точка не принадлежит ни одной зоне!'
    no_coordinates = '⚠️ Это сообщение не содержит координат. Формат: 11.1111, 22.2222'
    scout_leaved = '⚠️ Скаут бросил это задание!'
    no_active_coordinator = '⚠️ В настоящее время нет активных координаторов, вы не можете покинуть слот!'
    scout_have_tasks = '⚠️ У вас есть активные, невыполненные задачи! Вы уверены, что уходите?'

    def fatal_load(e):
        return f"⚠️ Произошла ошибка при обработке данных: {str(e)}"
    
    def no_active_scout(zone_name):
        return f"⚠️ На зоне {zone_name} нет ни одного активного скаута в данный момент времени."
    
