import asyncio
import os
import logging
from typing import Literal

from dotenv import load_dotenv
from openai import AsyncOpenAI

logging.basicConfig(filename="openai.log", level=logging.WARNING, encoding="utf-8",
                    format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %H:%M:%S')

logger = logging.getLogger("main")
logger.setLevel(logging.INFO)

load_dotenv(dotenv_path=".env.local")
openai = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
)

GPT = "gpt-4-turbo-preview"

instructions = {
    "anbudInstructions": """
Du er en anbudsassistent som skal hjelpe et IT konsulentselskap med å skrive anbud.
Du skal være en hjelpsom og hyggelig assistent som er flink til å skrive dokumenter.
Du skal ikke bruke unødvendig fancy ord.
Du skal ikke gjenta spørsmålet i svaret.
Du skal skrive et svar til dokumentet eller dokumentene som er lastet opp.
""",

    "oppsummeringInstructions": """
Du er en anbudsassistent som skal hjelpe et IT konsulentselskap med å oppsummere dokumenter.
Du skal være en hjelpsom og hyggelig assistent som er flink til å oppsummere dokumenter.
Du skal ikke bruke unødvendig fancy ord.
Du skal ikke gjenta spørsmålet i svaret.
Du skal gi grundige svar, med forklaringer.
"""
}


async def tellMeAJoke() -> None:
    completion = await openai.chat.completions.create(
        model=GPT,
        messages=[
            {
                "role": "system",
                "content": "You are a very funny guy."
            },
            {
                "role": "user",
                "content": "Tell me an unfunny joke."
            }
        ]
    )
    print(completion.choices[0].message.content)


async def createAssistant(key: Literal["anbudInstructions", "oppsummeringInstructions"]):
    name = "Anbudsassistent"
    assistant = await openai.beta.assistants.create(model=GPT,
                                                    name=name,
                                                    description="Anbudsassistent",
                                                    instructions=instructions[key],
                                                    tools=[{"type": "retrieval"}])
    logger.info("---------------------------")
    logger.info(f"Assistant '{name}' created: '{assistant.id}' using {GPT}")
    logger.info(f"With instructions: {instructions[key]}")
    logger.info("---------------------------")
    print(f"Assistant created: {assistant.id}")
    return assistant


async def getAssistants() -> list:
    assistants = await openai.beta.assistants.list()
    return assistants.data


async def uploadFile(assistant_id: str, file) -> None:
    logger.info(f"Uploading file '{file}' to assistant {assistant_id}")
    # Upload a file to OpenAI
    file = await openai.files.create(
        file=open(file, "rb"),
        purpose="assistants",
    )

    logger.debug(f"File created: {file}")

    # Add the uploaded file to the assistant
    await openai.beta.assistants.files.create(assistant_id, file_id=file.id)
    logger.debug("File uploaded to assistant")
    print("File uploaded to assistant")


async def deleteAssistant(assistant_id: str) -> None:
    logger.debug(f"Deleting assistant {assistant_id}")
    await openai.beta.assistants.delete(assistant_id)
    logger.debug("Assistant deleted")


async def clearAssistants() -> None:
    assistants = await getAssistants()
    for assistant in assistants:
        await deleteAssistant(assistant.id)


async def createThread():
    logger.debug("Creating thread")
    thread = await openai.beta.threads.create()
    logger.info(f"Thread created: {thread.id}")
    print(f"Thread created: {thread.id}")
    return thread


async def deleteThread(thread_id: str) -> None:
    logger.debug(f"Deleting thread {thread_id}")
    await openai.beta.threads.delete(thread_id)
    logger.debug("Thread deleted")


async def sendMessage(thread_id: str, assistant_id: str, content: str):
    logger.debug(f"Sending message '{content}' to thread {thread_id} with assistant {assistant_id}")
    logger.info(f"> {content}")
    # Create a message with a file
    await openai.beta.threads.messages.create(
        thread_id,
        role="user",
        content=content,
    )

    logger.debug("Message sent")

    # Create a run with the previously created message
    run = await openai.beta.threads.runs.create(thread_id, assistant_id=assistant_id)

    logger.debug("Run created")

    await waitForRunToComplete(run.id, thread_id)

    # Fetch all messages of the thread
    messages = await openai.beta.threads.messages.list(thread_id)

    logger.debug(f"Messages: {messages}")

    response = messages.data[0].content[0].text.value
    print(response)
    logger.info(f"GPT\n{response}")


async def waitForRunToComplete(run_id: str, thread_id: str) -> None:
    # Check the status of the run
    runStatus = await openai.beta.threads.runs.retrieve(run_id, thread_id=thread_id)
    print(runStatus.status)  # In progress

    while runStatus.status != "completed":
        await asyncio.sleep(1)
        runStatus = await openai.beta.threads.runs.retrieve(run_id, thread_id=thread_id)

        # Check for failed, cancelled, or expired status
        if runStatus.status in ["failed", "cancelled", "expired"]:
            print(f"Run status is '{runStatus.status}'. Unable to complete the request.")
            break  # Exit the loop if the status indicates a failure or cancellation


async def main() -> None:
    assistant = None
    thread = None
    while True:
        print("1. Tell me a joke")
        print("2. Create assistant")
        print("3. Create thread")
        print("4. Upload file")
        print("5. Send single message")
        print("6. Chat in thread")
        print("7. List assistants")
        print("8. Clear assistants")
        print("0. Exit")

        choice = input("Choice: ")

        if choice == "1":
            await tellMeAJoke()
        elif choice == "2":
            print("1. Anbud")
            print("2. Oppsummering")
            choice = input("Choice: ")
            if choice == "1":
                assistant = await createAssistant("anbudInstructions")
            elif choice == "2":
                assistant = await createAssistant("oppsummeringInstructions")
            else:
                print("Invalid choice")
        elif choice == "3":
            thread = await createThread()
        elif choice == "4":
            if assistant is None:
                print("You need to create an assistant first")
                continue

            file_path = input("File path: ")
            try:
                await uploadFile(assistant.id, file_path)
            except FileNotFoundError:
                print("File not found")
        elif choice == "5":
            if assistant is None:
                print("You need to create an assistant first")
                continue
            if thread is None:
                print("You need to create a thread first")
                continue

            message = input("> ")
            await sendMessage(thread.id, assistant.id, message)
        elif choice == "6":
            if assistant is None:
                print("You need to create an assistant first")
                continue
            if thread is None:
                print("You need to create a thread first")
                continue

            print("Type 'exit' to exit")
            while True:
                message = input("> ")
                if message == "exit":
                    break
                await sendMessage(thread.id, assistant.id, message)
        elif choice == "7":
            assistants = await getAssistants()
            for assistant in assistants:
                print(f"{assistant.id}: {assistant.name}")
        elif choice == "8":
            print("Clearing assistants...")
            await clearAssistants()
            assistant = None
            thread = None
        elif choice == "0":
            print("Cleaning up...")
            if assistant is not None:
                await deleteAssistant(assistant.id)
            if thread is not None:
                await deleteThread(thread.id)

            logger.info("""
---------------------------
Session ended
---------------------------""")
            break
        else:
            print("Invalid choice")


asyncio.run(main())
