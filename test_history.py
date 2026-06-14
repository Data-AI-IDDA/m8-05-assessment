import sys
import os
sys.path.append(os.getcwd())
from llm_service import ChatService

service = ChatService()
print("1st:")
for chunk in service.stream("My favorite color is green."):
    print(chunk, end="")
print("\n---")
print("2nd:")
for chunk in service.stream("What is my favorite color?"):
    print(chunk, end="")
print("\n---")
