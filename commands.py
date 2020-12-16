from telegram import InlineQueryResultArticle, InputTextMessageContent, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ConversationHandler
from telegram.keyboardbutton import KeyboardButton
import re
from pymongo import MongoClient
from utils.elastic_utils import ElasticClient
from time import sleep

elastic_client = ElasticClient()

mongo_client = MongoClient('localhost', 27017)
db = mongo_client['ooa']
# db['users'].drop()
collection = db['users']

button = KeyboardButton(text="Male")
button2 = KeyboardButton(text="Female")

sex_markup = ReplyKeyboardMarkup([[button, button2]], one_time_keyboard=True, resize_keyboard=True)

button = KeyboardButton(text="Name")
button2 = KeyboardButton(text="Age")
button3 = KeyboardButton(text="Height")
button4 = KeyboardButton(text="Weight")

update_markup = ReplyKeyboardMarkup([[button, button2], [button3, button4]], one_time_keyboard=True,
                                    resize_keyboard=True)

button = KeyboardButton(text="Yes")
button2 = KeyboardButton(text="No")

remove_user_markup = ReplyKeyboardMarkup([[button, button2]], one_time_keyboard=True, resize_keyboard=True)

button = KeyboardButton(text="Daily")
button2 = KeyboardButton(text="Weekly")

menu_types_markup = ReplyKeyboardMarkup([[button, button2]], one_time_keyboard=True, resize_keyboard=True)

remove_markup = ReplyKeyboardRemove()

clock_emoji = u'\U0001F550'
menu_option = ""

person = {}

help_list = """
/start - start a bot
/register - create your profile
/show - check your profile information
/update - update your profile information
/restart - remove your profile to create a new one
/help - see help information
/find <recipe name> - find recipes by entered name
"""


def show_help_info(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=f"Here is the list of available commands:\n{help_list}")


def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=f"Hello, this is EatHealthyBot. I cannot do much right now, sorry.\n"
                                  f"However, here is the list of commands that you may use:\n{help_list}")


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
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Cool! Please let me know if you are male or female:",
                                 reply_markup=sex_markup)
    return "get_sex"


def get_sex(update, context):
    sex = update.message.text
    if sex not in ("Male", "Female"):
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Please choose one from the options below:")
        return "get_sex"

    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Great! Please also provide me with your height (in cm):",
                             reply_markup=remove_markup)
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
    return ConversationHandler.END


def calc_calories(person):
    if person["sex"] == "Male":
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


def insert_user(update, context):
    # add user to DB
    person["telegram_user_id"] = update.effective_user.id
    person["_id"] = collection.find().count() + 1
    person["calories"] = calc_calories(person)
    person["menus"] = {
        "daily": [],
        "weekly": []
    }
    person["recipes"] = []
    collection.insert_one(person)
    context.bot.send_message(chat_id=update.effective_chat.id, text=f" Enter /show to see your info!")


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
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"Exiting as registration is not complete. "
                                                                    f"Please enter /register to fill out your info.")
    return ConversationHandler.END


def ask_user_info(update, context):
    if collection.find_one({"telegram_user_id": update.effective_user.id}):
        context.bot.send_message(chat_id=update.effective_chat.id, text="You are already registered!")
        return ConversationHandler.END
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Let's start with the name!")
        return "get_name"


def request_update(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="What do you want to update?",
                             reply_markup=update_markup)
    return "specify_update"


def specify_update(update, context):
    field = update.message.text
    if field == "Name":
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Please enter your new, updated name:",
                                 reply_markup=remove_markup)
        return "update_name"
    elif field == "Age":
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Please enter your new, updated age:",
                                 reply_markup=remove_markup)
        return "update_age"
    elif field == "Height":
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Please enter your new, updated height:",
                                 reply_markup=remove_markup)
        return "update_height"
    elif field == "Weight":
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Please enter your new, updated weight:",
                                 reply_markup=remove_markup)
        return "update_weight"
    else:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Please choose what to update by pressing the button",
                                 reply_markup=update_markup)
        return "specify_update"


def update_calories(update, context):
    person = collection.find_one({"telegram_user_id": update.effective_user.id})
    collection.find_one_and_update({"telegram_user_id": update.effective_user.id},
                                   {"$set": {"calories": calc_calories(person)}})


def update_name(update, context):
    collection.find_one_and_update({"telegram_user_id": update.effective_user.id},
                                   {"$set": {"name": update.message.text}})
    update_calories(update, context)
    context.bot.send_message(chat_id=update.effective_chat.id, text="Updated successfully!")
    show_info(update, context)
    return ConversationHandler.END


def update_age(update, context):
    collection.find_one_and_update({"telegram_user_id": update.effective_user.id},
                                   {"$set": {"age": update.message.text}})
    update_calories(update, context)
    context.bot.send_message(chat_id=update.effective_chat.id, text="Updated successfully!")
    show_info(update, context)
    return ConversationHandler.END


def update_height(update, context):
    collection.find_one_and_update({"telegram_user_id": update.effective_user.id},
                                   {"$set": {"height": update.message.text}})
    update_calories(update, context)
    context.bot.send_message(chat_id=update.effective_chat.id, text="Updated successfully!")
    show_info(update, context)
    return ConversationHandler.END


def update_weight(update, context):
    collection.find_one_and_update({"telegram_user_id": update.effective_user.id},
                                   {"$set": {"weight": update.message.text}})
    update_calories(update, context)
    context.bot.send_message(chat_id=update.effective_chat.id, text="Updated successfully!")
    show_info(update, context)
    return ConversationHandler.END


def restart(update, context):
    person = collection.find_one({"telegram_user_id": update.effective_user.id})
    if person:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Are you sure you want to remove your user profile?",
                                 reply_markup=remove_user_markup)
        return "restart"
    else:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="It looks like you do not have a profile yet! To create it, "
                                      "please enter /register .")
        return ConversationHandler.END


def remove_user(update, context):
    if update.message.text.lower() == "yes":
        person = collection.find_one({"telegram_user_id": update.effective_user.id})
        collection.remove(person)
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Done! To register new profile, please enter /register .",
                                 reply_markup=remove_markup)
    elif update.message.text.lower() == "no":
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Ok :) profile is not removed.",
                                 reply_markup=remove_markup)
    else:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Did not understand that. Please choose Yes or No option.")
        return "restart"
    return ConversationHandler.END


def get_shortened_recipe_info(index, recipe):
    recipe_info = f"""
*{index}*

*{re.escape(recipe["name"].capitalize())}*

{clock_emoji}"""
    recipe_info += f""" {recipe['minutes']} minutes"""
    recipe_info += """

*Nutrition*: """
    recipe_info += re.escape(f"{round(recipe['meal_nutrition'])} calories")
    recipe_info += f"\n"

    return recipe_info


def get_recipe_info(index, recipe):
    recipe_info = f"""
*{index}*

*{re.escape(recipe["name"].capitalize())}*

{clock_emoji}"""
    recipe_info += f""" {recipe["minutes"]} minutes

*Ingredients*:"""
    for ingredient in recipe["ingredients"].strip('][').split("', '"):
        recipe_info += re.escape(f"""
        - {ingredient.strip("'")}""")
    recipe_info += """

*Nutrition*: """
    recipe_info += re.escape(f"{round(recipe['meal_nutrition'])} calories")
    recipe_info += """

*Steps*:"""
    for step in recipe["steps"].strip('][').split("', '"):
        recipe_info += re.escape(f"""
        - {step.strip("'").capitalize().replace('"', '')}""")
    recipe_info += f"\n"
    return recipe_info


def get_menu_info(days, menu, func):
    response = []
    global menu_option
    for day in range(days):
        result = ""
        if menu_option == "weekly":
            if day == 0:
                day_name = "Monday"
            elif day == 1:
                day_name = "Tuesday"
            elif day == 2:
                day_name = "Wednesday"
            elif day == 3:
                day_name = "Thursday"
            elif day == 4:
                day_name = "Friday"
            elif day == 5:
                day_name = "Saturday"
            else:
                day_name = "Sunday"
            # context.bot.send_message(chat_id=update.effective_chat.id,
            #                          text=f"*Menu for {day_name}:*",
            #                          parse_mode="MarkdownV2")
            result += f"""
    *Menu for {day_name}:*          
                """

        index = "Breakfast"
        for meal in menu:
            # context.bot.send_message(chat_id=update.effective_chat.id,
            #                          text=get_shortened_recipe_info(index, meal),
            #                          parse_mode="MarkdownV2")
            result += f"""
    {func(index, meal)}
                """
            # sleep(1)
            if index == "Breakfast":
                index = "Dinner"
            elif index == "Dinner":
                index = "Supper"
            else:
                index = "Breakfast"
        response.append(result)
    return response


def add_menu(update, context):
    person = collection.find_one({"telegram_user_id": update.effective_user.id})
    if person:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Do you want to create menu for a day or for a week?",
                                 reply_markup=menu_types_markup)
        return "create"
    else:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="There is no profile for the menu! Enter /register to create one.")
        return ConversationHandler.END


def create_menu(update, context):
    global menu_option
    menu_option = update.message.text.lower()
    if menu_option == "daily":
        days = 1
    elif menu_option == "weekly":
        days = 7
    else:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Please press the button - Daily or Weekly :)",
                                 reply_markup=menu_types_markup)
        return "create"
    person = collection.find_one({"telegram_user_id": update.effective_user.id})
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="You successfully added a menu!")

    menu = elastic_client.get_daily_menu(person["calories"])
    person["menus"][menu_option.lower()].append(menu)
    collection.find_one_and_update({"telegram_user_id": update.effective_user.id},
                                   {"$set": {
                                       "menus": person["menus"]
                                   }})

    for meal in get_menu_info(days, menu, get_shortened_recipe_info):
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=meal,
                                 parse_mode="MarkdownV2")

    return ConversationHandler.END


def find_meal(update, context):
    recipe_name = " ".join(context.args)
    found_recipes = elastic_client.recipe_fuzzy_search_by_name(recipe_name)
    person = collection.find_one({"telegram_user_id": update.effective_user.id})
    person["recipes"].append({
        "keyword": recipe_name,
        "results": found_recipes
    })
    collection.find_one_and_update({"telegram_user_id": update.effective_user.id},
                                   {"$set": {"recipes": person["recipes"]}})
    response = f"*Found {len(found_recipes)} recipes*\!"
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=response,
                             parse_mode="MarkdownV2")
    sleep(1)
    for index, recipe in enumerate(found_recipes):
        response = get_shortened_recipe_info(str(index+1), recipe)
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=response,
                                 parse_mode="MarkdownV2")
        sleep(1)
    # for i in range(0, len(response), 4096):
    #     context.bot.send_message(chat_id=update.effective_chat.id,
    #                              text=response[i:i+4096])


def check_recipes(update, context):
    person = collection.find_one({"telegram_user_id": update.effective_user.id})
    response = ""
    if person:
        if context.args:
            specified_recipe_name = " ".join(context.args)
            correct_name = False
            found_recipes = person["recipes"]
            for recipe in found_recipes:
                if specified_recipe_name == recipe['keyword']:
                    correct_name = True
                    response += f"Here are the recipes you searched for *{specified_recipe_name}*:"
                    context.bot.send_message(chat_id=update.effective_chat.id,
                                             text=response,
                                             parse_mode="MarkdownV2")
                    for index, result in enumerate(recipe['results']):
                        response = get_recipe_info(str(index+1), result)
                        context.bot.send_message(chat_id=update.effective_chat.id,
                                                 text=response,
                                                 parse_mode="MarkdownV2")
            if not correct_name:
                response = f"Did not found {specified_recipe_name}" \
                           f" amongst the names you used\. \n\nHere are the correct ones:"
                for recipe in found_recipes:
                    response += f"\n\t\- *{recipe['keyword']}*"
                context.bot.send_message(chat_id=update.effective_chat.id,
                                         text=response,
                                         parse_mode="MarkdownV2")
        else:
            response += "Here are keywords you used for recipe search:"
            found_recipes = person["recipes"]
            for recipe in found_recipes:
                response += f"\n\t\- *{recipe['keyword']}*"

            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=response,
                                     parse_mode="MarkdownV2")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Looks you do not have a profile yet! Please enter /register to create one.")


def view_menus(update, context):
    person = collection.find_one({"telegram_user_id": update.effective_user.id})
    if person:
        menus = person["menus"]
        daily_menus = len(menus["daily"])
        weekly_menus = len(menus["weekly"])
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=f"Here are the menus you have: {daily_menus} daily and {weekly_menus} weekly "
                                      f"ones! Which one do you want to view?",
                                 reply_markup=menu_types_markup)
        return "view_type"
    else:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Looks you do not have a profile yet! Please enter /register to create one.")
        return ConversationHandler.END


def view_specified_type_menu(update, context):
    global menu_option
    person = collection.find_one({"telegram_user_id": update.effective_user.id})
    menu_option = update.message.text.lower()
    if menu_option in ["daily", "weekly"]:
        menus_length = len(person['menus'][menu_option])
        if menus_length == 0:
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text="Looks like there are no menus here! Add one using /add command.")
            return ConversationHandler.END
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=f"Please enter number (from 1 to {menus_length}) - "
                                      f"which of the {menu_option} menus to display:")
        return "view_menu"
    else:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Please press the button - Daily or Weekly :)",
                                 reply_markup=menu_types_markup)


def view_specified_menu(update, context):
    global menu_option
    reply = update.message.text
    try:
        index = int(reply) - 1
        person = collection.find_one({"telegram_user_id": update.effective_user.id})
        menus = person["menus"][menu_option]
        if 0 <= index <= len(menus):
            days = 7 if menu_option == "weekly" else 1
            for day_menu in get_menu_info(days, menus[index], get_recipe_info):
                sleep(1)
                try:
                    context.bot.send_message(chat_id=update.effective_chat.id,
                                             text=day_menu,
                                             parse_mode="MarkdownV2")
                except Exception as e:
                    for i in range(0, len(day_menu), 4096):
                        context.bot.send_message(chat_id=update.effective_chat.id,
                                                 text=day_menu[i:i+4096],
                                                 parse_mode="MarkdownV2")
            return ConversationHandler.END
        else:
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text="Seems like incorrect number! Please enter it again.")
            return "view_menu"
    except ValueError as e:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Seems like incorrect number! Please enter it again.")
        return "view_menu"


def unknown(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I did not understand that message.")
