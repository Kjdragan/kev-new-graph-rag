Embeddings

Note: Introducing our first Gemini embedding model, available now to developers
as gemini-embedding-exp-03-07 in the API. The Gemini API supports several
embedding models that generate embeddings for words, phrases, code, and
sentences. The resulting embeddings can then be used for tasks such as semantic
search, text classification, and clustering, among many others.

What are embeddings? Embeddings are numerical representations of text (or other
media formats) that capture relationships between inputs. Text embeddings work
by converting text into arrays of floating point numbers, called vectors. These
vectors are designed to capture the meaning of the text. The length of the
embedding array is called the vector's dimensionality. A passage of text might
be represented by a vector containing hundreds of dimensions.

Embeddings capture semantic meaning and context, which results in text with
similar meanings having "closer" embeddings. For example, the sentence "I took
my dog to the vet" and "I took my cat to the vet" would have embeddings that are
close to each other in the vector space.

You can use embeddings to compare different texts and understand how they
relate. For example, if the embeddings of the text "cat" and "dog" are close
together you can infer that these words are similar in meaning, context, or
both. This enables a variety of common AI use cases.

Before you begin Before calling the Gemini API, ensure you have your SDK of
choice installed, and a Gemini API key configured and ready to use.

Generate embeddings Use the embedContent method to generate text embeddings:

Python JavaScript Go REST

from google import genai

client = genai.Client(api_key="GEMINI_API_KEY")

result = client.models.embed_content( model="gemini-embedding-exp-03-07",
contents="What is the meaning of life?")

print(result.embeddings) You can also generate embeddings for multiple chunks at
once by passing them in as a list of strings.

Task types When building Retrieval Augmented Generation (RAG) systems, a common
design is to use text embeddings to perform a similarity search. In some cases
this can lead to degraded quality, because questions and their answers are not
semantically similar. For example, a question like "Why is the sky blue?" and
its answer "The scattering of sunlight causes the blue color," have distinctly
different meanings as statements, which means that a RAG system won't
automatically recognize their relation.

Task types enable you to generate optimized embeddings for specific tasks,
saving you time and cost and improving performance.

Python JavaScript REST

from google import genai from google.genai import types

client = genai.Client(api_key="GEMINI_API_KEY")

result = client.models.embed_content( model="gemini-embedding-exp-03-07",
contents="What is the meaning of life?",
config=types.EmbedContentConfig(task_type="SEMANTIC_SIMILARITY") )
print(result.embeddings) Supported task types Task type	Description
SEMANTIC_SIMILARITY	Used to generate embeddings that are optimized to assess
text similarity. CLASSIFICATION	Used to generate embeddings that are optimized
to classify texts according to preset labels. CLUSTERING	Used to generate
embeddings that are optimized to cluster texts based on their similarities.
RETRIEVAL_DOCUMENT, RETRIEVAL_QUERY, QUESTION_ANSWERING, and
FACT_VERIFICATION	Used to generate embeddings that are optimized for document
search or information retrieval. CODE_RETRIEVAL_QUERY	Used to retrieve a code
block based on a natural language query, such as sort an array or reverse a
linked list. Embeddings of the code blocks are computed using
RETRIEVAL_DOCUMENT. Use cases Text embeddings are used in a variety of common AI
use cases, such as:

Information retrieval: You can use embeddings to retrieve semantically similar
text given a piece of input text.

Document search tutorialtask

Clustering: Comparing groups of embeddings can help identify hidden trends.

Embedding clustering tutorialbubble_chart

Vector database: As you take different embedding use cases to production, it is
common to store embeddings in a vector database.

Vector database tutorialbolt

Classification: You can train a model using embeddings to classify documents
into categories.

Classification tutorialtoken

Embedding models The Gemini API offers three models that generate text
embeddings:

gemini-embedding-exp-03-07 text-embedding-004 embedding-001
