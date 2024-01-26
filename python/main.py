import os
import asyncio
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env.local")
openai = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
)

# TODO create new assistant
assistantId = "asst_hHOLmUPe8L9ujLkDXkEHlNwx"


async def chat():
    completion = await openai.chat.completions.create(
        model="gpt-4-1106-preview",
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


async def createFile():
    # Upload a file to OpenAI
    file = await openai.files.create(
        file=open("../USE OF ARTIFICIAL INTELLIGENCE TO PREDICT THE ACCURACY OF PRE-TENDER BUILDING COST ESTIMATE.pdf",
                  "rb"),
        purpose="assistants",
    )

    # Add the uploaded file to the assitant
    assistant = await openai.beta.assistants.files.create(assistantId, file_id=file.id)
    print(assistant)


# https://medium.com/@ralfelfving/learn-how-to-programatically-upload-files-using-openai-assistants-api-322cb5e6d2fd
async def summarizeFile():
    fileId = "file-gzvWWoV6JJ8KXOUc8hNB6e8J"

    # Create a new thread
    thread = await openai.beta.threads.create()

    # Create a message with a file
    message = await openai.beta.threads.messages.create(
        thread.id,
        role="user",
        content="Summarize the introduction",
        file_ids=[fileId]
    )

    print("Message created")

    # Create a run with the previously created message
    run = await openai.beta.threads.runs.create(thread.id, assistant_id=assistantId)

    print("Run created")

    # Check the status of the run
    runStatus = await openai.beta.threads.runs.retrieve(run.id, thread_id=thread.id)
    print(runStatus.status)  # In progress

    # Wait for the run to complete or fail
    while runStatus.status != "completed":
        await asyncio.sleep(1)
        runStatus = await openai.beta.threads.runs.retrieve(run.id, thread_id=thread.id)

        # Check for failed, cancelled, or expired status
        if runStatus.status in ["failed", "cancelled", "expired"]:
            print(f"Run status is '{runStatus.status}'. Unable to complete the request.")
            break  # Exit the loop if the status indicates a failure or cancellation

    # Fetch all messages of the thread
    messages = await openai.beta.threads.messages.list(thread.id)

    print(messages.data[0].content)

    # Delete the thread
    await openai.beta.threads.delete(thread.id)


async def main() -> None:
    await summarizeFile()


asyncio.run(main())
