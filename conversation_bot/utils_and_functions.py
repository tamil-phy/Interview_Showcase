import json
import pandas as pd
import yaml
from openai import OpenAI


################################### UTILS ##########################################
def get_response_from_openai(messages_list, tools, tool_choice):
    client = OpenAI(api_key='INSERT GPT KEY HERE')

    completion = client.chat.completions.create(
        model="gpt-4o",  #"gpt-3.5-turbo-0125",
        temperature=0.7,
        messages=messages_list,
        tools=tools,
        tool_choice=tool_choice
    )
    response = completion.choices[0].message
    return response


def call_func_with_response(result, available_functions):
    tool_calls = result.tool_calls
    message = []
    if tool_calls:
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)
            function_response = function_to_call(**function_args)

            return_response = {
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": function_name,
                "content": function_response,
            }

            message.append(return_response)
            return return_response, True
    else:
        return [{"role": "assistant"},
                {"content": str(result)}], False


def get_available_course_n_types():
    data_df = pd.read_csv('data/category_food.csv')
    category_df = data_df.drop_duplicates(subset=['category'])
    courses = dict(zip(category_df['category'], category_df['course_uuid']))

    available_courses = "\n" + "\n\n---\n".join(
        [
            f"Course Name: {course} \ncourse_uuid: {courses[course]}"
            for
            course in courses]
    )

    return available_courses, ['vegetarian', 'vegan', 'gluten free', 'non-vegetarian', 'others']


def get_available_menu_with_category():
    data_df = pd.read_csv('data/category_food.csv')
    data_df = data_df.astype(str)
    return data_df


def read_tools():
    available_tools = {}
    with open("tools.yaml") as stream:
        all_tools = yaml.safe_load(stream)
        for tool in all_tools:
            func_name = tool['function']['name']
            available_tools[func_name] = ""
        return all_tools, available_tools


################################### FUNCTIONS ##########################################

category_tools = [
    {
        "type": "function",
        "function": {
            "name": "find_food_category_explicit",
            "description": "Used to find the course of food",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Course of food",
                    },
                    "food_type": {
                        "type": "string",
                        "description": "Type of food",
                    },
                    "course_uuid": {
                        "type": "string",
                        "description": "course_uuid of the corresponding course name",
                    },

                },
                "required": ["category"],
            },
        },
    }
]


def find_food_category_explicit(**kwargs):
    category, food_type, course_uuid = kwargs.get('category'), kwargs.get('food_type'), kwargs.get('course_uuid')
    if category is not None:
        return {"response": {"category_name": str(category), "type": food_type, "course_uuid": course_uuid}}
    else:
        return {"response": {"category_name": "None", "type": "None", "course_uuid": "None"}}


def get_category_pages(**kwargs):
    category_of_food = kwargs.get('category_of_food')
    food_requested = kwargs.get('food_requested')
    quantity = kwargs.get('quantity') if kwargs.get('quantity') is not None else 1

    # if category_of_food is not None:
    #     return json.dumps({"response": {"category_name": str(category_of_food), "type": "None", "quantity": quantity,
    #                                     "food_requested": food_requested}})
    # else:
    if food_requested is not None or (food_requested is None and category_of_food is not None):
        course_options, types = get_available_course_n_types()
        print(course_options)
        message_list = [
            {
                "role": "system",
                "content": "You are a skilled waiter at a restaurant, and you need to match the requested course and "
                           "type of food from the menu."
            },
            {
                "role": "user",
                "content": f"The customer has requested {food_requested}, which is likely to be a {category_of_food}. The "
                           f"available course options in the menu are {course_options} (each with a unique course_uuid), "
                           f"and the available food types in the menu are {types}. Find the matching course option and food "
                           f"type from the menu to suggest to the customer. Ensure that both the course option and the food "
                           f"type are available in the menu. Provide the course option, the food type, and the corresponding "
                           f"course_uuid for the selected course option in your response."
            }
        ]
        response = get_response_from_openai(message_list, category_tools, {"type": "function", "function": {
            "name": "find_food_category_explicit"}})
        function_response, recursive = call_func_with_response(response,
                                                               {
                                                                   "find_food_category_explicit": find_food_category_explicit})
        function_response["content"]["response"]["quantity"] = quantity
        function_response["content"]["response"]["food_requested"] = food_requested
        return json.dumps(function_response["content"]["response"])
    else:
        return json.dumps(
            {"response": {"category_name": "None", "type": "None", "quantity": "None", "food_requested": "None"}})


def open_category_page(**kwargs):
    category_name, category_type = kwargs.get('category_name'), kwargs.get('category_type')
    return json.dumps({"response": {"category_name": str(category_name), "category_type": str(category_type)}})


def get_menu_of_category(category_name: str = None, categories=None, category_type=None, course_uuid=None):
    category_df = get_available_menu_with_category()
    available_categories_uuids = category_df['course_uuid'].unique().tolist()

    # Convert the category name and category keys to lowercase
    category_name_lower = category_name if category_name else None

    # Check if the category exists
    print(f"~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ {course_uuid} - {available_categories_uuids}")
    if course_uuid in available_categories_uuids:
        filtered_category_df = category_df[category_df['course_uuid'] == course_uuid]
        menu = filtered_category_df['food_item'].tolist()
        uuid_list = filtered_category_df['item_uuid'].tolist()
        price_list = filtered_category_df['price'].tolist()
    else:
        return json.dumps({"error": "Category not found"})

    # Format the menu
    menu_formatted = []
    for food, uuid, price in zip(menu, uuid_list, price_list):
        food_formatted = {
            "food_name": food,
            "name": food,
            "description": "Description not available",
            "price": price,  # Assuming price is not provided in the sample data
            "uuid": uuid
        }
        menu_formatted.append(food_formatted)

    menu_formatted_text = f"Menu of course '{category_name}':" + "\n" + "\n\n---\n".join(
        [
            f"{food['name']}:\nDescription: {food['description']} \nPrice: {food['price']} \nName: {food['food_name']} \nPrice: {food['price']} \nuuid: {food['uuid']}"
            for
            food in menu_formatted]
    )

    return json.dumps({"raw": menu_formatted, "formatted": menu_formatted_text})


def add_food_to_cart(
        category_name: str = None,
        food_name: str = None,
        quantity: int = 1,
        categories=None,
        uuid=None
):
    return json.dumps({
        "response": {
            "category_name": str(category_name),
            "food_name": str(food_name),
            "quantity": int(quantity),
            "uuid": int(uuid) if uuid is not None else 0
        }
    })


def remove_food_from_cart(
        category_name: str = None,
        food_name: str = None,
        quantity: int = None
):
    return json.dumps({
        "response": {
            "category_name": str(category_name),
            "food_name": str(food_name),
            "quantity": quantity
        }
    })


def dummy_function():
    return json.dumps({
        "response": {
            "action": "Corresponding function called"
        }
    })
