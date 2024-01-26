const OpenAI = require("openai");
const fs = require("fs")

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
const assistantId = "asst_hHOLmUPe8L9ujLkDXkEHlNwx"

async function chat() {
    const completion = await openai.chat.completions.create({
        model: "gpt-4-1106-preview",
        messages: [
            {
                role: "system",
                content: "You are a very funny guy."
            },
            {
                role: "user",
                content: "Tell me a unfunny joke."
            }
        ]
    })
    console.log(completion.choices[0])
}

async function createFile() {
    // Upload a file to OpenAI
    const file = await openai.files.create({
        file: fs.createReadStream("longFile.pdf"),
        purpose: "assistants"
    })

    // Add the uploaded file to the assitant
    const assistant = await openai.beta.assistants.files.create(assistantId, {
        file_id: file.id
    })
    console.log(assistant)
}

// https://medium.com/@ralfelfving/learn-how-to-programatically-upload-files-using-openai-assistants-api-322cb5e6d2fd
async function summarizeFile() {
    const fileId = "file-gzvWWoV6JJ8KXOUc8hNB6e8J"

    // Create a new thread
    const thread = await openai.beta.threads.create()

    // Create a message with a file
    const message = await openai.beta.threads.messages.create(thread.id, {
        role: "user",
        content: "Summarize the introduction",
        file_ids: [fileId]
    })

    console.log("Message created")

    // Create a run with the previously created message
    const run = await openai.beta.threads.runs.create(thread.id, {
        assistant_id: assistantId,
    })

    console.log("Run created")

    // Check the status of the run
    let runStatus = await openai.beta.threads.runs.retrieve(thread.id, run.id)
    console.log(runStatus.status); // In progress

    // Wait for the run to complete or fail
    while (runStatus.status !== "completed") {
        await new Promise((resolve) => setTimeout(resolve, 1000));
        runStatus = await openai.beta.threads.runs.retrieve(
            thread.id,
            run.id
        );

        // Check for failed, cancelled, or expired status
        if (["failed", "cancelled", "expired"].includes(runStatus.status)) {
            console.log(
                `Run status is '${ runStatus.status }'. Unable to complete the request.`
            );
            break; // Exit the loop if the status indicates a failure or cancellation
        }
    }

    // Fetch all messages of the thread
    const messages = await openai.beta.threads.messages.list(thread.id);

    console.log(messages.data[0].content)

    // Delete the thread
    await openai.beta.threads.del(thread.id)
}

async function getThread() {
    const thread = await openai.beta.threads.retrieve("thread-1k1zQKk1X0c9J5yX")
    console.log(thread)
}

void summarizeFile()
