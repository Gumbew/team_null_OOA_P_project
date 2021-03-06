from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, InlineQueryHandler, ConversationHandler
import logging
import os

from commands import start, ask_user_info, get_name, get_age, get_sex, get_height, get_weight, show_info, fallback, \
    request_update, specify_update, update_name, update_age, update_height, update_weight,  restart, remove_user, \
    unknown, show_help_info, create_menu, find_meal, add_menu, check_recipes, view_menus, view_specified_type_menu, \
    view_specified_menu, remove_recipe, delete_menu, delete_specified_type_menu, delete_specified_menu

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

TOKEN = os.environ.get("TOKEN")

updater = Updater(token=TOKEN, use_context=True)
dispatcher = updater.dispatcher

help_handler = CommandHandler('help', show_help_info)
dispatcher.add_handler(help_handler)

start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

get_person_info_handler = CommandHandler("show", show_info)
dispatcher.add_handler(get_person_info_handler)

ask_user_info_handler = ConversationHandler(
    entry_points=[
        CommandHandler("register", ask_user_info)
    ],
    states={
        "get_name": [MessageHandler(Filters.text & (~Filters.command), get_name)],
        "get_age": [MessageHandler(Filters.text & (~Filters.command), get_age)],
        "get_sex": [MessageHandler(Filters.text & (~Filters.command), get_sex)],
        "get_height": [MessageHandler(Filters.text & (~Filters.command), get_height)],
        "get_weight": [MessageHandler(Filters.text & (~Filters.command), get_weight)],
    },
    fallbacks=[MessageHandler(Filters.command, fallback)],
)
dispatcher.add_handler(ask_user_info_handler)

update_info_handler = ConversationHandler(
    entry_points=[
        CommandHandler("update", request_update)
    ],
    states={
        "specify_update": [MessageHandler(Filters.text, specify_update)],
        "update_name": [MessageHandler(Filters.text, update_name)],
        "update_age": [MessageHandler(Filters.text, update_age)],
        "update_height": [MessageHandler(Filters.text, update_height)],
        "update_weight": [MessageHandler(Filters.text, update_weight)]
    },
    fallbacks=[
        MessageHandler(Filters.command, fallback)
    ]
)
dispatcher.add_handler(update_info_handler)

remove_user_handler = ConversationHandler(
    entry_points=[
        CommandHandler("restart", restart)
    ],
    states={
        "restart": [MessageHandler(Filters.text, remove_user)]
    },
    fallbacks=[
        MessageHandler(Filters.command, fallback)
    ]
)
dispatcher.add_handler(remove_user_handler)

add_menu_handler = ConversationHandler(
    entry_points=[
        CommandHandler('add', add_menu)
    ],
    states={
        "create": [MessageHandler(Filters.text, create_menu)]
    },
    fallbacks=[
        MessageHandler(Filters.command, fallback)
    ]
)
dispatcher.add_handler(add_menu_handler)

find_meal_handler = CommandHandler('find', find_meal)
dispatcher.add_handler(find_meal_handler)

check_recipes_handler = CommandHandler('check', check_recipes)
dispatcher.add_handler(check_recipes_handler)

view_menus_handler = ConversationHandler(
    entry_points=[
        CommandHandler('view', view_menus)
    ],
    states={
        "view_type": [MessageHandler(Filters.text, view_specified_type_menu)],
        "view_menu": [MessageHandler(Filters.text, view_specified_menu)]
    },
    fallbacks=[
        MessageHandler(Filters.command, fallback)
    ]
)
dispatcher.add_handler(view_menus_handler)

remove_recipe_handler = CommandHandler('remove', remove_recipe)
dispatcher.add_handler(remove_recipe_handler)

delete_menu_handler = ConversationHandler(
    entry_points=[
        CommandHandler('delete', delete_menu)
    ],
    states={
        "delete_type": [MessageHandler(Filters.text, delete_specified_type_menu)],
        "delete_menu": [MessageHandler(Filters.text, delete_specified_menu)]
    },
    fallbacks=[
        MessageHandler(Filters.command, fallback)
    ]
)
dispatcher.add_handler(delete_menu_handler)

# should always be last of the handlers in the code
unknown_handler = MessageHandler(Filters.text, unknown)
dispatcher.add_handler(unknown_handler)

updater.start_polling()
updater.idle()
