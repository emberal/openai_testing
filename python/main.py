import asyncio
import os

from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv(dotenv_path=".env.local")
openai = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
)

assistantId = "asst_MFPQ5CAGRV7GFD9IwKojZMLS"

GPT = "gpt-4-turbo-preview"

assistantInstructions = """
Du er en anbudsassistent som skal hjelpe et IT konsulentselskap med å skrive anbud og oppsummerere dokumenter.
Du skal være en hjelpsom og hyggelig assistent som er flink til å skrive og oppsummere dokumenter.
Du skal ikke bruke unødvendig fancy ord.
"""


async def chat() -> None:
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
    print(completion.choices[0])


async def createAssistant():
    assistant = await openai.beta.assistants.create(model=GPT,
                                                    name="Anbudsassistent",
                                                    description="Anbudsassistent",
                                                    instructions=assistantInstructions,
                                                    tools=[{"type": "retrieval"}])
    print(f"Assistant created: {assistant.id}")
    return assistant


async def uploadFile(assistant_id: str, file) -> None:
    # Upload a file to OpenAI
    file = await openai.files.create(
        file=open(file, "rb"),
        purpose="assistants",
    )

    # Add the uploaded file to the assistant
    await openai.beta.assistants.files.create(assistant_id, file_id=file.id)
    print("File uploaded to assistant")


async def deleteAssistant(assistant_id: str) -> None:
    await openai.beta.assistants.delete(assistant_id)


async def createThread():
    thread = await openai.beta.threads.create()
    print(f"Thread created: {thread.id}")
    return thread


async def deleteThread(thread_id: str) -> None:
    await openai.beta.threads.delete(thread_id)


async def sendMessage(thread_id: str, assistant_id: str, content: str):
    # Create a message with a file
    await openai.beta.threads.messages.create(
        thread_id,
        role="user",
        content=content,
    )

    print("Message created")

    # Create a run with the previously created message
    run = await openai.beta.threads.runs.create(thread_id, assistant_id=assistant_id)

    print("Run created")

    await waitForRunToComplete(run.id, thread_id)

    # Fetch all messages of the thread
    messages = await openai.beta.threads.messages.list(thread_id)

    print(messages.data[0].content[0].text.value)


# https://medium.com/@ralfelfving/learn-how-to-programatically-upload-files-using-openai-assistants-api-322cb5e6d2fd
async def summarizeFile() -> None:
    # Create a new thread
    thread = await createThread()

    # Create a message with a file
    message = await openai.beta.threads.messages.create(
        thread.id,
        role="user",
        content="Summarize the introduction of the file \"ai_tender_assitant_paper.pdf\"",
        # file_ids=[fileId] # We could also use a file id here instead of writing the name of the file in the content
    )

    print("Message created")

    # Create a run with the previously created message
    run = await openai.beta.threads.runs.create(thread.id, assistant_id=assistantId)

    print("Run created")

    await waitForRunToComplete(run.id, thread.id)

    # Fetch all messages of the thread
    messages = await openai.beta.threads.messages.list(thread.id)

    print(messages.data[0].content)

    # Delete the thread
    await openai.beta.threads.delete(thread.id)


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
        print("1. Chat")
        print("2. Create assistant")
        print("3. Create thread")
        print("4. Send message")
        print("5. Upload file")
        print("6. Summarize file")
        print("7. Exit")

        choice = input("Choice: ")

        if choice == "1":
            await chat()
        elif choice == "2":
            assistant = await createAssistant()
        elif choice == "3":
            thread = await createThread()
        elif choice == "4":
            if assistant is None:
                print("You need to create an assistant first")
                continue
            if thread is None:
                print("You need to create a thread first")
                continue

            message = input("> ")
            await sendMessage(thread.id, assistant.id, message)
        elif choice == "5":
            if assistant is None:
                print("You need to create an assistant first")
                continue

            file_path = input("File path: ")
            await uploadFile(assistant.id, file_path)
        elif choice == "6":
            await summarizeFile()
        elif choice == "7":
            print("Cleaning up...")
            if assistant is not None:
                await deleteAssistant(assistant.id)
            if thread is not None:
                await deleteThread(thread.id)
            break
        else:
            print("Invalid choice")


asyncio.run(main())
