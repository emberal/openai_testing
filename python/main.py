import asyncio
import json
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
    "default": """
You are a helpful assistant.
""",
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
Du skal skrive om blant annet:
- Hva ønsker kunden å få ut av prosjektet?
- Hva skal utvikles?
- Hvilke krav har kunden?
- Frister
- Budsjett
- Hvilke kompetanse trenger kunden?
- Andre ting som er relevant for prosjektet
""",
    "kompatetanseMatriseInstructions": """
Du skal lage en kompetansematrise for et IT konsulentselskap. 
Kompetansematrisen skal inneholde en kolonne for kategori (kan være systemutvikler, testutvikler, scrummaster, 
arkitekt eller annet), navn på konsulent, og en kort beskrivelse av kompetansen og relevant erfaring.
Du skal gi svaret i form av strukturert JSON.
Du skal ikke gjennta spørsmålet i svaret.
Du skal ikke bruke unødvendig fancy ord.
Du skal velge riktig kategori basert på en oppsummering av en anbudskonkurranse.
"""
}

konkurranse_oppsummering = """- **Bilag 1 til 11**: Dekker alt fra oppdragsgivers kravspesifikasjon, leverandørens 
tjenestebeskrivelse, plan for etableringsfasen, tjenestenivå med standardiserte kompensasjoner, administrative 
bestemmelser, økonomiske aspekter, til databehandleravtalen【19†source】. **Kjernepunkter i krav og spesifikasjoner 
inkluderer:** - **Bærekraft og effektivisering**: Renholdstjenesten skal benytte bærekraftig og effektiviserende 
teknologi, samle renholdsplaner i et digitalt system og gjøre dem tilgjengelige for renholdspersonell. Systemet skal 
støtte delt renholdsareal på ca. 160.000 m^2 konsentrert i videregående skoler og idrettshaller【19†source】. - 
**Opsjoner for utvidet bruk**: Det er inkludert opsjoner for ytterligere bruk av systemet, som dekker behovet til 
Fylkeshuset AS og eksterne renholdsleverandører, samt integrasjon med ulike sluttbrukeres booking av rom【19†source】. 
- **Funksjonalitet**: Systemet skal tilby en rekke funksjoner som tegningsbasert planleggingsverktøy, 
mobil grensesnitt, nettbasert løsning for ledere og support på norsk. Videre kreves det universell utforming og 
støtte for å håndtere et stort antall samtidige brukere【23†source. - **Brukervennlighet**: Renholdspersonell skal 
kunne dokumentere arbeid, melde avvik, og oppdragsgiver skal kunne administrere brukere, definere ekstraoppgaver og 
kommunisere bestillinger og meldinger gjennom systemet. Det vektlegges at systemet støtter offline-funksjonalitet og 
er brukervennlig både for ledere og renholdere【23†source】. - **Brukerstøtte og stabilitet**: Support skal være 
norsk-talende og kunne varsle om kjente feil i systemet samt planlagt nedetid. Beskrivelse av brukerstøtteapparatet, 
inkludert tilgjengelighet, antall supportmedarbeidere og gjennomsnittlig svartid er nødvendig【27†source】. - 
**Personvern og sikkerhet**: Det legges vekt på databeskyttelse og informasjonssikkerhet. Blant annet må leverandøren 
ha et styringssystem for informasjonssikkerhet som møter gjeldende personvernregler, og det skal være klare rutiner 
for revisjon og tilsyn samt protokoller for hvordan personopplysninger håndteres ved avtalens opphør. 
Kontaktinformasjon for varsling om sikkerhetsbrudd eller andre relevante henvendelser er også nevnt【45†source】.

Dokumentets detaljerte natur gjenspeiler oppdragsgivers intensjon om å sikre en omfattende og kvalitetssikret løsning 
som imøtekommer organisasjonens nåværende og fremtidige behov på en bærekraftig, brukervennlig, og sikker måte."""


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


async def kompetansematrise(konsulent_data: str) -> None:
    logger.info("Creating kompetansematrise with test consultant data")
    stream = await openai.chat.completions.create(
        model=GPT,
        messages=[
            {
                "role": "system",
                "content": instructions["kompatetanseMatriseInstructions"]
            },
            {
                "role": "user",
                "content": konsulent_data
            }
        ],
        response_format={"type": "json_object"},
        stream=True
    )
    logger.info("Kompetansematrise data:\n")
    result = ""
    async for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            response = chunk.choices[0].delta.content
            result += response
            print(response, end="")
    logger.info(result)
    print()


async def createAssistant(
        key: Literal["default", "anbudInstructions", "oppsummeringInstructions", "kompatetanseMatriseInstructions"]
):
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
    logger.info("""
---------------------------
Session started
---------------------------""")
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
        print("9. Kompentansematrise test")
        print("0. Exit")

        choice = input("Choice: ")

        if choice == "1":
            await tellMeAJoke()
        elif choice == "2":
            inst = selectInstruction()
            if inst is not None:
                assistant = await createAssistant(inst)
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
        elif choice == "9":
            consultants = getKonsulenter()
            await kompetansematrise("{" + f"\"oppsummering\":\"{konkurranse_oppsummering}\",{consultants[1:]}")
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


def getKonsulenter() -> str:
    with open("konsulenter.json") as file:
        data = json.load(file)
    return json.dumps(data)  # Serialize to string


def selectInstruction() -> (
        Literal["default", "anbudInstructions", "oppsummeringInstructions", "kompatetanseMatriseInstructions"] | None
):
    print("1. Anbud")
    print("2. Oppsummering")
    print("3. Kompetansematrise")
    print("0: Default")
    choice = input("Choice: ")
    if choice == "1":
        return "anbudInstructions"
    elif choice == "2":
        return "oppsummeringInstructions"
    elif choice == "3":
        return "kompatetanseMatriseInstructions"
    elif choice == "0":
        return "default"
    else:
        print("Invalid choice")
        return None


asyncio.run(main())
