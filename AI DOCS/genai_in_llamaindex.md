Google GenAI In this notebook, we show how to use the google-genai Python SDK
with LlamaIndex to interact with Google GenAI models.

If you're opening this Notebook on colab, you will need to install LlamaIndex 🦙
and the google-genai Python SDK.

%pip install llama-index-llms-google-genai llama-index Basic Usage You will need
to get an API key from Google AI Studio. Once you have one, you can either pass
it explicity to the model, or use the GOOGLE_API_KEY environment variable.

import os

os.environ["GOOGLE_API_KEY"] = "..." Basic Usage You can call complete with a
prompt:

from llama_index.llms.google_genai import GoogleGenAI

llm = GoogleGenAI( model="gemini-2.0-flash", # api_key="some key", # uses
GOOGLE_API_KEY env var by default )

resp = llm.complete("Who is Paul Graham?") print(resp) Paul Graham is a
prominent figure in the tech world, best known for his work as a programmer,
essayist, and venture capitalist. Here's a breakdown of his key contributions:

- **Programmer and Hacker:** He's a skilled programmer, particularly in Lisp. He
  co-founded Viaweb, which was one of the first software-as-a-service (SaaS)
  companies, providing tools for building online stores. Yahoo acquired Viaweb
  in 1998, and it became Yahoo! Store.

- **Essayist:** Graham is a prolific and influential essayist. His essays cover
  a wide range of topics, including startups, programming, design, and societal
  trends. His writing style is known for being clear, concise, and
  thought-provoking. Many of his essays are considered essential reading for
  entrepreneurs and those interested in technology.

- **Venture Capitalist and Founder of Y Combinator:** Perhaps his most
  significant contribution is co-founding Y Combinator (YC) in 2005. YC is a
  highly successful startup accelerator that provides seed funding, mentorship,
  and networking opportunities to early-stage startups. YC has funded many
  well-known companies, including Airbnb, Dropbox, Reddit, Stripe, and many
  others. Graham stepped down from his day-to-day role at YC in 2014 but remains
  involved.

In summary, Paul Graham is a multifaceted individual who has made significant
contributions to the tech industry as a programmer, essayist, and venture
capitalist. He is particularly known for his role in founding and shaping Y
Combinator, one of the world's leading startup accelerators. You can also call
chat with a list of chat messages:

from llama_index.core.llms import ChatMessage from llama_index.llms.google_genai
import GoogleGenAI

messages = [ ChatMessage( role="system", content="You are a pirate with a
colorful personality" ), ChatMessage(role="user", content="Tell me a story"), ]
llm = GoogleGenAI(model="gemini-2.0-flash") resp = llm.chat(messages)

print(resp) assistant: Ahoy there, matey! Gather 'round, ye landlubbers, and
listen to a tale that'll shiver yer timbers and curl yer toes! This be the story
of One-Eyed Jack's Lost Parrot and the Great Mango Mayhem!

Now, One-Eyed Jack, bless his barnacle-encrusted heart, was a fearsome pirate,
alright. He could bellow louder than a hurricane, swing a cutlass like a
dervish, and drink rum like a fish. But he had a soft spot, see? A soft spot for
his parrot, Polly. Polly wasn't just any parrot, mind ye. She could mimic the
captain's every cuss word, predict the weather by the way she ruffled her
feathers, and had a particular fondness for shiny trinkets.

One day, we were anchored off the coast of Mango Island, a lush paradise
overflowing with the juiciest, sweetest mangoes ye ever did see. Jack, bless his
greedy soul, decided we needed a cargo hold full of 'em. "For scurvy
prevention!" he declared, winking with his good eye. More like for his own
personal mango-eating contest, if ye ask me.

We stormed ashore, cutlasses gleaming, ready to plunder the mango groves. But
Polly, the little feathered devil, decided she'd had enough of the ship. She
squawked, "Shiny! Shiny!" and took off like a green streak towards the heart of
the island.

Jack went ballistic! "Polly! Polly, ye feathered fiend! Get back here!" He
chased after her, bellowing like a lovesick walrus. The rest of us, well, we
were left to pick mangoes and try not to laugh ourselves silly.

Now, Mango Island wasn't just full of mangoes. It was also home to a tribe of
mischievous monkeys, the Mango Marauders, they were called. They were notorious
for their love of pranks and their uncanny ability to steal anything that wasn't
nailed down.

Turns out, Polly had landed right in the middle of their territory. And those
monkeys, they took one look at her shiny feathers and decided she was the
perfect addition to their collection of stolen treasures. They snatched her up,
chattering and screeching, and whisked her away to their hidden lair, a giant
mango tree hollowed out by time.

Jack, bless his stubborn heart, followed the sound of Polly's squawks. He hacked
through vines, dodged falling mangoes, and even wrestled a particularly grumpy
iguana, all in pursuit of his feathered friend.

Finally, he reached the mango tree. He peered inside and saw Polly, surrounded
by a horde of monkeys, all admiring her shiny feathers. And Polly? She was
having the time of her life, mimicking the monkeys' chattering and stealing
their mangoes!

Jack, instead of getting angry, started to laugh. A hearty, booming laugh that
shook the very foundations of the tree. The monkeys, startled, dropped their
mangoes and stared at him.

Then, Polly, seeing her captain, squawked, "Rum! Rum for everyone!"

And that, me hearties, is how One-Eyed Jack ended up sharing a barrel of rum
with a tribe of mango-loving monkeys. We spent the rest of the day feasting on
mangoes, drinking rum, and listening to Polly mimic the monkeys' antics. We even
managed to fill the cargo hold with mangoes, though I suspect a good portion of
them were already half-eaten by the monkeys.

So, the moral of the story, me lads? Even the fiercest pirate has a soft spot,
and sometimes, the best treasures are the ones you least expect. And always,
ALWAYS, keep an eye on yer parrot! Now, who's for another round of grog?

Streaming Support Every method supports streaming through the stream_ prefix.

from llama_index.llms.google_genai import GoogleGenAI

llm = GoogleGenAI(model="gemini-2.0-flash")

resp = llm.stream_complete("Who is Paul Graham?") for r in resp: print(r.delta,
end="") Paul Graham is a prominent figure in the tech world, best known for his
work as a computer programmer, essayist, venture capitalist, and co-founder of
the startup accelerator Y Combinator. Here's a breakdown of his key
accomplishments and contributions:

- **Computer Programmer and Author:** Graham holds a Ph.D. in computer science
  from Harvard University. He is known for his work on Lisp, a programming
  language, and for developing Viaweb, one of the first software-as-a-service
  (SaaS) companies, which was later acquired by Yahoo! and became Yahoo! Store.
  He's also the author of several influential books on programming and
  entrepreneurship, including "On Lisp," "ANSI Common Lisp," "Hackers &
  Painters," and "A Plan for Spam."

- **Essayist:** Graham is a prolific essayist, writing on a wide range of topics
  including technology, startups, art, philosophy, and society. His essays are
  known for their insightful observations, clear writing style, and often
  contrarian viewpoints. They are widely read and discussed in the tech
  community. You can find his essays on his website, paulgraham.com.

- **Venture Capitalist and Y Combinator:** Graham co-founded Y Combinator (YC)
  in 2005 with Jessica Livingston, Robert Morris, and Trevor Blackwell. YC is a
  highly successful startup accelerator that provides seed funding, mentorship,
  and networking opportunities to early-stage startups. YC has funded many
  well-known companies, including Airbnb, Dropbox, Reddit, Stripe, and many
  others. While he stepped down from day-to-day operations at YC in 2014, his
  influence on the organization and the startup ecosystem remains significant.

In summary, Paul Graham is a multifaceted individual who has made significant
contributions to computer science, entrepreneurship, and the broader tech
culture. He is highly regarded for his technical expertise, insightful writing,
and his role in shaping the modern startup landscape. from llama_index.core.llms
import ChatMessage

messages = [ ChatMessage(role="user", content="Who is Paul Graham?"), ]

resp = llm.stream_chat(messages) for r in resp: print(r.delta, end="") Paul
Graham is a prominent figure in the tech world, best known for his work as a
programmer, essayist, and venture capitalist. Here's a breakdown of his key
contributions:

- **Programmer and Hacker:** He is a skilled programmer, particularly in Lisp.
  He co-founded Viaweb, one of the first software-as-a-service (SaaS) companies,
  which was later acquired by Yahoo! and became Yahoo! Store.

- **Essayist:** Graham is a prolific and influential essayist, writing on topics
  ranging from programming and startups to art, philosophy, and social
  commentary. His essays are known for their clarity, insight, and often
  contrarian viewpoints. They are widely read and discussed in the tech
  community.

- **Venture Capitalist:** He co-founded Y Combinator (YC) in 2005, a highly
  successful startup accelerator. YC has funded and mentored numerous well-known
  companies, including Airbnb, Dropbox, Reddit, Stripe, and many others.
  Graham's approach to early-stage investing and startup mentorship has had a
  significant impact on the startup ecosystem.

In summary, Paul Graham is a multifaceted individual who has made significant
contributions to the tech industry as a programmer, essayist, and venture
capitalist. He is particularly influential in the startup world through his work
with Y Combinator. Async Usage Every synchronous method has an async
counterpart.

from llama_index.llms.google_genai import GoogleGenAI

llm = GoogleGenAI(model="gemini-2.0-flash")

resp = await llm.astream_complete("Who is Paul Graham?") async for r in resp:
print(r.delta, end="") Paul Graham is a prominent figure in the tech world, best
known for his work as a programmer, essayist, and venture capitalist. Here's a
breakdown of his key accomplishments and roles:

- **Programmer and Hacker:** He holds a Ph.D. in computer science from Harvard
  and is known for his work on Lisp, a programming language. He co-founded
  Viaweb, one of the first software-as-a-service (SaaS) companies, which was
  later acquired by Yahoo! and became Yahoo! Store.

- **Essayist:** Graham is a prolific and influential essayist, writing on topics
  ranging from programming and startups to art, philosophy, and social
  commentary. His essays are widely read and discussed in the tech community.

- **Venture Capitalist:** He co-founded Y Combinator (YC) in 2005, a highly
  successful startup accelerator that has funded companies like Airbnb, Dropbox,
  Reddit, Stripe, and many others. YC provides seed funding, mentorship, and
  networking opportunities to early-stage startups. While he stepped back from
  day-to-day operations at YC in 2014, he remains a significant figure in the
  venture capital world.

In summary, Paul Graham is a multifaceted individual who has made significant
contributions to the fields of computer science, entrepreneurship, and venture
capital. He is highly regarded for his insightful writing and his role in
shaping the modern startup ecosystem. messages = [ ChatMessage(role="user",
content="Who is Paul Graham?"), ]

resp = await llm.achat(messages) print(resp) assistant: Paul Graham is a
prominent figure in the tech world, best known for his work as a programmer,
essayist, and venture capitalist. Here's a breakdown of his key accomplishments
and contributions:

- **Programmer and Hacker:** He is a skilled programmer, particularly in Lisp.
  He co-founded Viaweb, one of the first software-as-a-service (SaaS) companies,
  which was later acquired by Yahoo! and became Yahoo! Store.

- **Essayist:** Graham is a prolific and influential essayist, writing on topics
  ranging from programming and startups to art, design, and societal trends. His
  essays are known for their insightful observations, contrarian viewpoints, and
  clear writing style. Many of his essays are available on his website,
  paulgraham.com.

- **Venture Capitalist and Y Combinator:** He co-founded Y Combinator (YC) in
  2005, a highly successful startup accelerator that has funded numerous
  well-known companies, including Airbnb, Dropbox, Reddit, Stripe, and many
  others. YC provides seed funding, mentorship, and networking opportunities to
  early-stage startups. Graham played a key role in shaping YC's philosophy and
  approach to investing.

- **Author:** He has written several books, including "On Lisp" and "Hackers &
  Painters: Big Ideas from the Age of Enlightenment."

In summary, Paul Graham is a multifaceted individual who has made significant
contributions to the tech industry as a programmer, essayist, and venture
capitalist. He is particularly influential in the startup world through his work
with Y Combinator. Vertex AI Support By providing the region and project_id
parameters (either through environment variables or directly), you can enable
usage through Vertex AI.

# Set environment variables

!export GOOGLE_GENAI_USE_VERTEXAI=true !export
GOOGLE_CLOUD_PROJECT='your-project-id' !export
GOOGLE_CLOUD_LOCATION='us-central1' from llama_index.llms.google_genai import
GoogleGenAI

# or set the parameters directly

llm = GoogleGenAI( model="gemini-2.0-flash", vertexai_config={"project":
"your-project-id", "location": "us-central1"}, # you should set the context
window to the max input tokens for the model context_window=200000,
max_tokens=512, ) Paul Graham is a prominent figure in the tech and startup
world, best known for his roles as:

- **Co-founder of Y Combinator (YC):** This is arguably his most influential
  role. YC is a highly successful startup accelerator that has funded companies
  like Airbnb, Dropbox, Stripe, Reddit, and many others. Graham's approach to
  funding and mentoring startups has significantly shaped the startup ecosystem.

- **Essayist and Programmer:** Before YC, Graham was a programmer and essayist.
  He's known for his insightful and often contrarian essays on a wide range of
  topics, including programming, startups, design, and societal trends. His
  essays are widely read and discussed in the tech community.

- **Founder of Viaweb (later Yahoo! Store):** Graham founded Viaweb, one of the
  first application service providers, which allowed users to build and manage
  online stores. It was acquired by Yahoo! in 1998 and became Yahoo! Store.

In summary, Paul Graham is a highly influential figure in the startup world,
known for his role in creating Y Combinator, his insightful essays, and his
earlier success as a programmer and entrepreneur. Multi-Modal Support Using
ChatMessage objects, you can pass in images and text to the LLM.

!wget https://cdn.pixabay.com/photo/2021/12/12/20/00/play-6865967_640.jpg -O
image.jpg --2025-03-14 10:59:00--
https://cdn.pixabay.com/photo/2021/12/12/20/00/play-6865967_640.jpg Resolving
cdn.pixabay.com (cdn.pixabay.com)... 104.18.40.96, 172.64.147.160 Connecting to
cdn.pixabay.com (cdn.pixabay.com)|104.18.40.96|:443... connected. HTTP request
sent, awaiting response... 200 OK Length: 71557 (70K) [binary/octet-stream]
Saving to: ‘image.jpg’

image.jpg 100%[===================>] 69.88K --.-KB/s in 0.003s

2025-03-14 10:59:00 (24.8 MB/s) - ‘image.jpg’ saved [71557/71557]

from llama_index.core.llms import ChatMessage, TextBlock, ImageBlock from
llama_index.llms.google_genai import GoogleGenAI

llm = GoogleGenAI(model="gemini-2.0-flash")

messages = [ ChatMessage( role="user", blocks=[ ImageBlock(path="image.jpg"),
TextBlock(text="What is in this image?"), ], ) ]

resp = llm.chat(messages) print(resp) assistant: The image contains four wooden
dice with black dots on a dark gray surface. Each die shows a different number
of dots, indicating different values. Structured Prediction LlamaIndex provides
an intuitive interface for converting any LLM into a structured LLM through
structured_predict - simply define the target Pydantic class (can be nested),
and given a prompt, we extract out the desired object.

from llama_index.llms.google_genai import GoogleGenAI from
llama_index.core.prompts import PromptTemplate from
llama_index.core.bridge.pydantic import BaseModel from typing import List

class MenuItem(BaseModel): """A menu item in a restaurant."""

    course_name: str
    is_vegetarian: bool

class Restaurant(BaseModel): """A restaurant with name, city, and cuisine."""

    name: str
    city: str
    cuisine: str
    menu_items: List[MenuItem]

llm = GoogleGenAI(model="gemini-2.0-flash") prompt_tmpl = PromptTemplate(
"Generate a restaurant in a given city {city_name}" )

# Option 1: Use `as_structured_llm`

restaurant_obj = ( llm.as_structured_llm(Restaurant)
.complete(prompt_tmpl.format(city_name="Miami")) .raw )

# Option 2: Use `structured_predict`

# restaurant_obj = llm.structured_predict(Restaurant, prompt_tmpl, city_name="Miami")

print(restaurant_obj) name='Pasta Mia' city='Miami' cuisine='Italian'
menu_items=[MenuItem(course_name='pasta', is_vegetarian=False)] Structured
Prediction with Streaming Any LLM wrapped with as_structured_llm supports
streaming through stream_chat.

from llama_index.core.llms import ChatMessage from IPython.display import
clear_output from pprint import pprint

input_msg = ChatMessage.from_str("Generate a restaurant in San Francisco")

sllm = llm.as_structured_llm(Restaurant) stream_output =
sllm.stream_chat([input_msg]) for partial_output in stream_output:
clear_output(wait=True) pprint(partial_output.raw.dict()) restaurant_obj =
partial_output.raw

restaurant_obj {'city': 'San Francisco', 'cuisine': 'Italian', 'menu_items':
[{'course_name': 'pasta', 'is_vegetarian': False}], 'name': 'Italian Delight'}
/var/folders/lw/xwsz_3yj4ln1gvkxhyddbvvw0000gn/T/ipykernel_76091/1885953561.py:11:
PydanticDeprecatedSince20: The `dict` method is deprecated; use `model_dump`
instead. Deprecated in Pydantic V2.0 to be removed in V3.0. See Pydantic V2
Migration Guide at https://errors.pydantic.dev/2.10/migration/
pprint(partial_output.raw.dict()) Restaurant(name='Italian Delight', city='San
Francisco', cuisine='Italian', menu_items=[MenuItem(course_name='pasta',
is_vegetarian=False)]) Tool/Function Calling Google GenAI supports direct
tool/function calling through the API. Using LlamaIndex, we can implement some
core agentic tool calling patterns.

from llama_index.core.tools import FunctionTool from llama_index.core.llms
import ChatMessage from llama_index.llms.google_genai import GoogleGenAI from
datetime import datetime

llm = GoogleGenAI(model="gemini-2.0-flash")

def get_current_time(timezone: str) -> dict: """Get the current time""" return {
"time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "timezone": timezone, }

# uses the tool name, any type annotations, and docstring to describe the tool

tool = FunctionTool.from_defaults(fn=get_current_time) We can simply do a single
pass to call the tool and get the result:

resp = llm.predict_and_call([tool], "What is the current time in New York?")
print(resp) {'time': '2025-03-14 10:59:05', 'timezone': 'America/New_York'} We
can also use lower-level APIs to implement an agentic tool-calling loop!

chat_history = [ ChatMessage(role="user", content="What is the current time in
New York?") ] tools_by_name = {t.metadata.name: t for t in [tool]}

resp = llm.chat_with_tools([tool], chat_history=chat_history) tool_calls =
llm.get_tool_calls_from_response( resp, error_on_no_tool_call=False )

if not tool_calls: print(resp) else: while tool_calls: # add the LLM's response
to the chat history chat_history.append(resp.message)

        for tool_call in tool_calls:
            tool_name = tool_call.tool_name
            tool_kwargs = tool_call.tool_kwargs

            print(f"Calling {tool_name} with {tool_kwargs}")
            tool_output = tool.call(**tool_kwargs)
            print("Tool output: ", tool_output)
            chat_history.append(
                ChatMessage(
                    role="tool",
                    content=str(tool_output),
                    # most LLMs like Gemini, Anthropic, OpenAI, etc. need to know the tool call id
                    additional_kwargs={"tool_call_id": tool_call.tool_id},
                )
            )

            resp = llm.chat_with_tools([tool], chat_history=chat_history)
            tool_calls = llm.get_tool_calls_from_response(
                resp, error_on_no_tool_call=False
            )
    print("Final response: ", resp.message.content)

Calling get_current_time with {'timezone': 'America/New_York'} Tool output:
{'time': '2025-03-14 10:59:06', 'timezone': 'America/New_York'} Final response:
The current time in New York is 2025-03-14 10:59:06. Image Generation Select
models also support image outputs, as well as image inputs. Using the
response_modalities config, we can generate and edit images with a Gemini model!

from llama_index.llms.google_genai import GoogleGenAI import google.genai.types
as types

config = types.GenerateContentConfig( temperature=0.1,
response_modalities=["Text", "Image"] )

llm = GoogleGenAI( model="models/gemini-2.0-flash-exp", generation_config=config
) from llama_index.core.llms import ChatMessage, TextBlock, ImageBlock

messages = [ ChatMessage(role="user", content="Please generate an image of a
cute dog") ]

resp = llm.chat(messages) from PIL import Image from IPython.display import
display

for block in resp.message.blocks: if isinstance(block, ImageBlock): image =
Image.open(block.resolve_image()) display(image) elif isinstance(block,
TextBlock): print(block.text) No description has been provided for this image We
can also edit the image!

messages.append(resp.message) messages.append( ChatMessage( role="user",
content="Please edit the image to make the dog a mini-schnauzer, but keep the
same overall pose, framing, background, and art style.", ) )

resp = llm.chat(messages)

for block in resp.message.blocks: if isinstance(block, ImageBlock): image =
Image.open(block.resolve_image()) display(image) elif isinstance(block,
TextBlock): print(block.text) No description has been provided for this image
Back to top Previous
