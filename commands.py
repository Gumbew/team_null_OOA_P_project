from telegram import InlineQueryResultArticle, InputTextMessageContent, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ConversationHandler
from telegram.keyboardbutton import KeyboardButton
import re
import pymongo
from pymongo import MongoClient

client = MongoClient('localhost', 27017)
db = client['ooa']
db['users'].drop()
collection = db['users']


def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Hello, this is EatHealthyBot. I cannot do much right now, sorry.")


def echo(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)


def caps(update, context):
    text_caps = ' '.join(context.args).upper()
    context.bot.send_message(chat_id=update.effective_chat.id, text=text_caps)


def inline_caps(update, context):
    query = update.inline_query.query
    if not query:
        return
    results = [InlineQueryResultArticle(
        id=query.upper(),
        title=query.upper(),
        input_message_content=InputTextMessageContent(query.upper())
    )]
    context.bot.answer_inline_query(update.inline_query.id, results)


person = {}


def get_name(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"Hello, {update.message.text}! How old are you?")
    person["name"] = update.message.text
    return "get_age"


def get_age(update, context):
    ages = re.findall(r"\d{1,3}", update.message.text)
    if not ages:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=f"Please enter your age as a number:")
        return "get_age"
    if len(ages) > 1:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=f"Not sure which one of these is your age: {', '.join(ages)}. "
                                      f"Please enter the valid one:")
        return "get_age"
    else:
        if 0 < int(ages[0]) < 120:
            person["age"] = ages[0]
        else:
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=f"Are you sure your age is {ages[0]}? "
                                          f"Please double-check and enter your age once again:")
            return "get_age"
        button = KeyboardButton(text="Male", callback_data="Male")
        button2 = KeyboardButton(text="Female", callback_data="Female")
        markup = ReplyKeyboardMarkup([[button, button2]], one_time_keyboard=True)
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Cool! Please let me know if you are male or female:",
                                 reply_markup=markup)

    return "get_sex"


def get_sex(update, context):
    sex = update.message.text
    if sex not in ("Male", "Female"):
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Please choose one from the options below:")
        return "get_sex"

    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Great! Please also provide me with your height (in cm):")
    person["sex"] = sex
    return "get_height"


def get_height(update, context):
    heights = re.findall(r"\d{2,3}", update.message.text)
    if not heights:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=f"Please enter your height as a number:")
        return "get_height"
    if len(heights) > 1:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=f"Not sure which one of these is your height: {', '.join(heights)}. "
                                      f"Please enter the valid one:")
        return "get_height"
    else:
        # 55 to 272
        if 55 <= int(heights[0]) <= 272:
            person["height"] = heights[0]
        else:
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=f"Are you sure your height is {heights[0]}? "
                                          f"Please double-check and enter your height once again:")
            return "get_height"
    context.bot.send_message(chat_id=update.effective_chat.id, text="Last, but not the least - your weight (in kg):")
    return "get_weight"


def get_weight(update, context):
    weights = re.findall(r"\d{2,3}", update.message.text)
    if not weights:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=f"Please enter your weight as a number:")
        return "get_weight"
    if len(weights) > 1:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=f"Not sure which one of these is your weight: {', '.join(weights)}. "
                                      f"Please enter the valid one:")
        return "get_weight"
    else:
        # 10 to 442
        if 10 <= int(weights[0]) <= 442:
            person["weight"] = weights[0]
        else:
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=f"Are you sure your weight is {weights[0]}? "
                                          f"Please double-check and enter your weight once again:")
            return "get_weight"

    context.bot.send_message(chat_id=update.effective_chat.id, text="Thank you!")
    insert_user(update, context)


def insert_user(update, context):
    def calc_calories():
        if person["sex"] == "M":
            k_1 = 88.36
            k_2 = 13.4
            k_3 = 4.8
            k_4 = 5.7
        else:
            k_1 = 447.6
            k_2 = 9.2
            k_3 = 3.1
            k_4 = 4.3
        calories = 1.2 * (k_1 + k_2 * int(person["weight"]) + k_3 * int(person["height"]) - k_4 * int(person["age"]))
        return int(round(calories, -2))

    # add user to DB
    person["telegram_user_id"] = update.effective_user.id
    person["_id"] = collection.find().count() + 1
    person["calories"] = calc_calories()
    collection.insert_one(person)
    context.bot.send_message(chat_id=update.effective_chat.id, text=f" Enter /show to see your info!")
    return ConversationHandler.END


def show_info(update, context):
    person = collection.find_one({"telegram_user_id": update.effective_user.id})
    if person:
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"""
    Here is your information:

Name - {person["name"]}
Sex - {person["sex"]}
Age - {person["age"]}
Height - {person["height"]}
Weight - {person["weight"]}

Daily norm of calories - {person["calories"]}
""")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"No info found!")


def fallback(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"Exiting")
    return ConversationHandler.END


def ask_user_info(update, context):
    if collection.find_one({"telegram_user_id": update.effective_user.id}):
        context.bot.send_message(chat_id=update.effective_chat.id, text="You are already registered!")
        return ConversationHandler.END
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Let's start with the name!")
        return "get_name"


def register(update, context):
    # check if user is registered
    if collection.find_one({"telegram_user_id": update.effective_user.id}):
        context.bot.send_message(chat_id=update.effective_chat.id, text="You are already registered!")
    else:
        ask_user_info(update, context)


def update_info(update, context):
    pass


def unknown(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I did not understand that command.")
