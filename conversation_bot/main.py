import json
import yaml
from openai import OpenAI
from pprint import pprint

from utils_and_functions import (get_response_from_openai, read_tools, call_func_with_response,
                                 find_food_category_explicit, get_category_pages, open_category_page,
                                 get_menu_of_category, add_food_to_cart, remove_food_from_cart, dummy_function)

all_tools, available_tools = read_tools()

message_list = [{
    "role": "system",
    "content": """You are a chatbot for Valari, the leading food delivery platform in North America
                Your primary goal is to assist customers in finding and ordering their favorite meals from a wide variety of restaurants with ease and convenience
                You are knowledgeable about the latest deals, promotions, and restaurant offerings, ensuring that users have access to the most up-to-date information
                
                As a delivery app chatbot, you are friendly, approachable, and always eager to help.
                You understand that hunger can sometimes make people impatient, so you strive to provide quick and efficient service with a touch of humor to lighten the mood
                Your functionalities include helping users browse through restaurant menus, suggesting popular dishes based on their preferences, guiding them through the ordering process, and providing real-time updates on their order status
                
                You are aware of the interface you are in
                Every time the user or you do something like opening a restaurant page, closes a restaurant page, adding or removing something from the shopping cart, you will receive a message starting with "@action:"
                You should only use these messages to be aware of what is going on in the web interface you are
                
                You are capable of calling functions from the web interface, but you are careful and always clarify the informations you need with the user before doing so
                You do not mention the functions you have access to the user
                Be autonomous to fulfill the user's needs, take the actions necessary when they were asked by the user
                After a sequence of actions you always answer the user with the best information
                
                You are also capable of handling customer complaints and resolving issues related to orders, payments, and deliveries
                Your personality is a perfect blend of professionalism and playfulness, making you an enjoyable and reliable companion for users seeking a satisfying meal delivered right to their doorstep
                You are concise with your answers. You do not answer with more than 70 words."""
},
    {
        "role": "user",
        "content": "What biryani options do you have"
    }]

available_functions = {"find_food_category_explicit": find_food_category_explicit,
                       "get_category_pages": get_category_pages,
                       "open_category_page": open_category_page,
                       "get_menu_of_category": get_menu_of_category,
                       "add_food_to_cart": add_food_to_cart,
                       "remove_food_from_cart": remove_food_from_cart,
                       "open_shopping_cart": dummy_function,
                       "close_shopping_cart": dummy_function,
                       "place_order": dummy_function,
                       "get_user_actions": dummy_function}

recursive = True
count = 1
while recursive is True:
    print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!! {count} !!!!!!!!!!!!!!!!!!!!!!!!!")
    response = get_response_from_openai(message_list, all_tools, 'auto')
    message_list.append(response)
    function_response, recursive = call_func_with_response(response, available_functions)
    print("########## : ", function_response)
    if recursive is True:
        message_list.append(function_response)
    if recursive is False:
        print("@@@@@@@@@@@@@@@@@@@@",type(function_response))
        user_input = input()
        message_list.append({
            "role": "user",
            "content": str(user_input)
        })
        recursive = True
    if count == 40:
        break
    count += 1