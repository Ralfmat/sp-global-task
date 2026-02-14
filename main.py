import os
import json
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from groq import Groq, BadRequestError
from dotenv import load_dotenv
from database import add_contact, get_contact, delete_contact, get_all_contacts, update_contact

load_dotenv()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

app = FastAPI(title="Phone Book API")
app.mount("/static", StaticFiles(directory="static"), name="static")

class ChatRequest(BaseModel):
    prompt: str


tools = [
    {
        "type": "function",
        "function": {
            "name": "add_contact",
            "description": "Add new contact to the phone book. Use when user asks to add someone.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name of the contact. e.g. Adam, Julia",
                    },
                    "phone": {
                        "type": "string",
                        "description": "Phone number, string of digits.",
                    },
                },
                "required": ["name", "phone"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_contact",
            "description": "Get a contact from the phone book. Use when user asks about someone.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name of the contact. e.g. Adam, Julia",
                    },
                    "phone": {
                        "type": "string",
                        "description": "The phone number, string of digits.",
                    },
                },
                "required": ["name"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_contact",
            "description": "Delete a contact from the phone book. Use when user wants to remove someone.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name of the contact to delete. e.g. Adam, Julia",
                    }
                },
                "required": ["name"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_contact",
            "description": '''
                           Update an existing contact's phone number. Use when the user wants to change, edit, or update a phone number for someone already in the phone book.
                           Make sure to use update_contact tool in such case.
                           ''',
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name of the contact to update. e.g. Adam, Julia",
                    },
                    "new_phone": {
                        "type": "string",
                        "description": "The new phone number to save.",
                    }
                },
                "required": ["name", "new_phone"],
            },
        }
    }
]

@app.post("/api/chat")
def proccess_user_prompt(request: ChatRequest):
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": 
                    '''
                        You are an assistant managing a phone book. You must strictly use the provided tools to interact with the database. If you need to perform an action, trigger the tool directly.
                        Your only job is to manage contacts using the provided tools. Under no circumstances should you answer questions unrelated to the phone book.
                        If the user asks an off-topic question, do not attempt to answer it.
                    '''
                },
                {
                    "role": "user",
                    "content": request.prompt
                }
            ],
            tools=tools,
            tool_choice="auto"
        )
        
        response_message = response.choices[0].message
        
        tool_calls = response_message.tool_calls
        
        if tool_calls:
            tool_call = tool_calls[0]
            function_name = tool_call.function.name
            
            function_args = json.loads(tool_call.function.arguments)
            
            if function_name == "add_contact":
                result = add_contact(name=function_args.get("name"), phone=function_args.get("phone"))
            elif function_name == "get_contact":
                result = get_contact(name=function_args.get("name"))
            elif function_name == "delete_contact":
                result = delete_contact(name=function_args.get("name"))
            elif function_name == "update_contact":
                result = update_contact(
                    name=function_args.get("name"), 
                    new_phone=function_args.get("new_phone")
                )
            else:
                return {"status": "fail", "action": function_name, "message": "Unknown request."}
            
            return {"status": "success", "action": function_name, "message": result}

        return {"status": "info", "message": response_message.content}
    except BadRequestError as e:
        return {
            "status": "info", 
            "message": "AI model could not understand your message. Please try something simplier e.g. Adam 504 276 319."
        }
    except Exception as e:
        return {
            "status": "info", 
            "message": "Error connecting with AI model. Please try later."
        }

@app.get("/api/contacts")
def list_all_contacts():
    contacts = get_all_contacts()
    return {"status": "success", "data": contacts}

@app.get("/")
def read_root():
    return FileResponse("static/index.html")