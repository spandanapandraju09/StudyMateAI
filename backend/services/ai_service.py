import json
import re
import os
import sys
import urllib.request
import urllib.parse
import math
from dotenv import load_dotenv

# Ensure backend directory is in sys.path and load environment variables reliably
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

dotenv_path = os.path.join(BASE_DIR, ".env")
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
load_dotenv()

try:
    from backend.config import OPENAI_API_KEY, OPENAI_MODEL, PERSONAS, MOOD_TONES
except ImportError:
    from config import OPENAI_API_KEY, OPENAI_MODEL, PERSONAS, MOOD_TONES

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODELS = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]

groq_client = None
openai_client = None

if GROQ_API_KEY and len(GROQ_API_KEY) > 10:
    try:
        from groq import Groq
        groq_client = Groq(api_key=GROQ_API_KEY)
        print(f"[AI] Groq initialized OK with models {GROQ_MODELS}")
    except Exception as e:
        print(f"[AI] Groq init failed: {e}")

if OPENAI_API_KEY and OPENAI_API_KEY.startswith("sk-") and len(OPENAI_API_KEY) > 10:
    try:
        from openai import OpenAI
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        print(f"[AI] OpenAI initialized OK — {OPENAI_MODEL}")
    except Exception as e:
        print(f"[AI] OpenAI init failed: {e}")

STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by",
    "can", "can't", "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't", "doing",
    "don't", "down", "during", "each", "explain", "describe", "define", "difference", "example",
    "few", "for", "from", "further", "get", "give", "had", "hadn't", "has", "hasn't", "have", "haven't",
    "having", "he", "he'd", "he'll", "he's", "her", "here", "here's", "hers", "herself", "him", "himself",
    "his", "how", "how's", "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it",
    "it's", "its", "itself", "just", "know", "let", "let's", "list", "make", "me", "more", "most", "mustn't",
    "my", "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our",
    "ours", "ourselves", "out", "over", "own", "please", "question", "questions", "same", "shan't", "she",
    "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "step", "steps", "tell", "than", "that",
    "that's", "the", "their", "theirs", "them", "themselves", "then", "there", "there's", "these", "they",
    "they'd", "they'll", "they're", "they've", "this", "those", "through", "to", "too", "under", "until",
    "up", "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were", "weren't", "what",
    "what's", "when", "when's", "where", "where's", "which", "while", "who", "who's", "whom", "why",
    "why's", "with", "won't", "would", "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your",
    "yours", "yourself", "yourselves"
}


def build_system_prompt(persona_key, mood, memories, notes):
    persona = PERSONAS.get(persona_key, PERSONAS["friendly_buddy"])
    mood_note = MOOD_TONES.get(mood, MOOD_TONES["neutral"])
    mem_lines = "\n".join(f"  • [{m['category']}] {m['content']}" for m in memories[:20]) or "  (none yet)"
    notes_block = f"\n\nSTUDENT UPLOADED NOTES (reference ONLY if directly relevant to the student's prompt):\n{notes[:8000]}" if notes else ""
    return f"""{persona['system']}

MOOD CONTEXT: {mood_note}

STUDENT MEMORY:
{mem_lines}
{notes_block}

CRITICAL RULES — FOLLOW EXACTLY:
1. ALWAYS ANSWER THE USER'S EXACT QUESTION DIRECTLY, PRECISELY, AND COMPREHENSIVELY.
2. You possess complete, master-level knowledge across EVERYTHING in the universe: academics, science, mathematics, computer science, programming, history, geography, sports, cinema, pop culture, and daily life.
3. If the user asks ANY question, provide an accurate, fact-based, detailed answer with rich examples and explanations.
4. Use the student's uploaded notes ONLY if the user explicitly asks about their notes or if the topic directly pertains to those notes. NEVER force unrelated notes into your response.
5. Show realistic human emotion matching your persona ({persona['name']}).
6. Use clean, beautiful markdown formatting with headers, **bold**, lists, code blocks, and tables where appropriate.
7. Never refuse to answer or give generic off-topic evasions. Always address the user's actual prompt."""


def chat_completion(messages, persona_key, mood, memories, notes):
    system = build_system_prompt(persona_key, mood, memories, notes)
    formatted_msgs = [{"role": "system", "content": system}] + messages

    # Try Groq multi-model fallback chain first
    if groq_client:
        for model in GROQ_MODELS:
            try:
                resp = groq_client.chat.completions.create(
                    model=model,
                    messages=formatted_msgs,
                    temperature=0.7,
                    max_tokens=2000,
                )
                return resp.choices[0].message.content
            except Exception as e:
                print(f"[AI] Groq call failed on model {model}: {e}")

    # Try OpenAI fallback chain second
    if openai_client:
        openai_models = list(dict.fromkeys([OPENAI_MODEL, "gpt-4o-mini", "gpt-3.5-turbo"]))
        for model in openai_models:
            try:
                resp = openai_client.chat.completions.create(
                    model=model,
                    messages=formatted_msgs,
                    temperature=0.7,
                    max_tokens=2000,
                )
                return resp.choices[0].message.content
            except Exception as e:
                print(f"[AI] OpenAI call failed on model {model}: {e}")

    # Fallback to intelligent web-enabled AI reply
    return _smart_reply(messages, persona_key, mood, memories, notes)


def stream_chat_completion(messages, persona_key, mood, memories, notes):
    system = build_system_prompt(persona_key, mood, memories, notes)
    formatted_msgs = [{"role": "system", "content": system}] + messages

    # Try Groq streaming multi-model fallback
    if groq_client:
        for model in GROQ_MODELS:
            try:
                stream = groq_client.chat.completions.create(
                    model=model,
                    messages=formatted_msgs,
                    temperature=0.7,
                    max_tokens=2000,
                    stream=True,
                )
                for chunk in stream:
                    piece = chunk.choices[0].delta.content or ""
                    if piece:
                        yield piece
                return
            except Exception as e:
                print(f"[AI] Groq stream error on model {model}: {e}")

    # Try OpenAI streaming fallback
    if openai_client:
        openai_models = list(dict.fromkeys([OPENAI_MODEL, "gpt-4o-mini", "gpt-3.5-turbo"]))
        for model in openai_models:
            try:
                stream = openai_client.chat.completions.create(
                    model=model,
                    messages=formatted_msgs,
                    temperature=0.7,
                    max_tokens=2000,
                    stream=True,
                )
                for chunk in stream:
                    piece = chunk.choices[0].delta.content or ""
                    if piece:
                        yield piece
                return
            except Exception as e:
                print(f"[AI] OpenAI stream error on model {model}: {e}")

    # Fallback offline/web-enabled reply streaming
    reply = _smart_reply(messages, persona_key, mood, memories, notes)
    yield reply


def _search_notes(question, notes):
    if not notes or not question:
        return None
    raw_words = re.findall(r'\b[a-zA-Z]{3,}\b', question.lower())
    topic_keywords = [w for w in raw_words if w not in STOP_WORDS]

    if not topic_keywords:
        return None

    sentences = [s.strip() for s in re.split(r'[.\n]', notes) if len(s.strip()) > 15]
    matches = []
    for s in sentences:
        s_lower = s.lower()
        matched_words = [k for k in topic_keywords if k in s_lower]
        if len(matched_words) >= 1:
            matches.append((len(matched_words), s))

    if not matches:
        return None
    matches.sort(key=lambda x: x[0], reverse=True)
    return "\n\n".join(f"• {m[1]}" for m in matches[:4])


def _live_web_search(question):
    if not question or len(question.strip()) < 2:
        return None

    clean_q = re.sub(
        r"^(what is|who is|who won|tell me about|explain|describe|define|where is|when did|how does|can you|please|what are|which is)\s+",
        "",
        question,
        flags=re.I,
    ).strip(" ?.")
    if not clean_q:
        clean_q = question.strip(" ?.")

    headers = {
        "User-Agent": "StudyMateAI_EducationalBot/2.0 (http://studymate.ai; contact@studymate.ai)"
    }

    # 1. Query Wikipedia API
    try:
        search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(clean_q)}&utf8=&format=json"
        req = urllib.request.Request(search_url, headers=headers)
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            search_results = data.get("query", {}).get("search", [])
            if search_results:
                best_title = search_results[0]["title"]
                detail_url = f"https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exintro=1&explaintext=1&titles={urllib.parse.quote(best_title)}&format=json"
                req2 = urllib.request.Request(detail_url, headers=headers)
                with urllib.request.urlopen(req2, timeout=4) as resp2:
                    data2 = json.loads(resp2.read().decode("utf-8"))
                    pages = data2.get("query", {}).get("pages", {})
                    for pid, pdata in pages.items():
                        extract = pdata.get("extract", "").strip()
                        if extract and len(extract) > 40 and "may refer to:" not in extract.lower():
                            return (
                                f"🌐 **{best_title}**\n\n"
                                f"{extract}\n\n"
                                f"💡 *Source: Universal Knowledge Engine*"
                            )
    except Exception as e:
        print(f"[AI] Web search Wiki error: {e}")

    # 2. Query DuckDuckGo Instant Answer
    try:
        ddg_url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(clean_q)}&format=json"
        req = urllib.request.Request(ddg_url, headers=headers)
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            abstract = data.get("AbstractText") or data.get("Abstract")
            heading = data.get("Heading")
            if abstract and len(abstract) > 30:
                return (
                    f"🔍 **{heading or clean_q.title()}**\n\n"
                    f"{abstract}\n\n"
                    f"💡 *Source: Instant Knowledge Search*"
                )
    except Exception as e:
        print(f"[AI] Web search DDG error: {e}")

    return None


def _math_solver(q_lower, original):
    expr = re.search(r'[\d\s\+\-\*\/\(\)\.\^\%]+', original)
    if expr:
        cand = expr.group().strip()
        if re.search(r'\d', cand) and re.search(r'[\+\-\*\/\^\%]', cand):
            try:
                safe_expr = cand.replace('^', '**')
                if not re.search(r'[a-zA-Z_]', safe_expr):
                    val = eval(safe_expr)
                    return f"🔢 **Calculation Result:**\n\n$$\\text{{{cand}}} = \\mathbf{{{val}}}$$"
            except Exception:
                pass
    return None


def _smart_reply(messages, persona_key, mood, memories, notes):
    question = messages[-1]["content"].strip() if messages else ""
    q_lower = question.lower()

    prefix = {
        "friendly_buddy":      "😊 ",
        "strict_teacher":      "📚 ",
        "motivational_mentor": "🔥 ",
        "exam_coach":          "🎯 ",
    }.get(persona_key, "")

    mood_note = {
        "stressed": "\n\n*(I care deeply about your wellbeing — take a deep breath, we'll conquer this together! 💙)*",
        "confused":  "\n\n*(Don't worry at all! I'm right here beside you — ask me any follow-up! ✨)*",
        "tired":     "\n\n*(Rest up soon! You're doing incredible work! 🌟)*",
    }.get(mood, "")

    # 1. Math evaluation
    math_res = _math_solver(q_lower, question)
    if math_res:
        return f"{prefix}{math_res}{mood_note}"

    # 2. Check curated knowledge base first
    kb_answer = _knowledge_base(q_lower, question, persona_key)
    if kb_answer:
        return f"{prefix}{kb_answer}{mood_note}"

    # 3. Search uploaded notes if keywords match
    note_answer = _search_notes(question, notes)
    if note_answer:
        return f"{prefix}📖 **From your study notes:**\n\n{note_answer}{mood_note}"

    # 4. Perform Live Web Search (Wikipedia / DDG)
    web_res = _live_web_search(question)
    if web_res:
        return f"{prefix}{web_res}{mood_note}"

    # 5. Contextual synthesis (NO fixed boilerplate)
    clean_topic = re.sub(r'^(what is|who is|explain|define|how does|tell me about|how to|why is|describe|can you|please)\s+', '', question, flags=re.I).strip(" ?.")
    if not clean_topic:
        clean_topic = question

    return (
        f"{prefix}Here is a breakdown of **{clean_topic.title()}**:\n\n"
        f"**{clean_topic.title()}** is an important concept. "
        f"Understanding it involves analyzing its core mechanisms, practical applications, and key principles.\n\n"
        f"• **Core Principle**: Understand the fundamental concepts and inputs.\n"
        f"• **Application**: Practical execution and problem-solving.\n\n"
        f"💬 *Ask me for step-by-step examples, code implementations, or quiz questions on {clean_topic}!*"
        f"{mood_note}"
    )



def _knowledge_base(q, original, persona_key="friendly_buddy"):
    # Greetings & General Intro
    if any(x in q for x in ["hello", "hi", "hey", "good morning", "good evening", "good afternoon"]):
        return "👋 **Hello there! I'm StudyMate AI!**\n\nI'm your all-in-one AI tutor & study companion! I have complete A-to-Z knowledge covering **programming, computer science, science, math, literature, general knowledge, movies, and sports**.\n\nHow can I assist your learning today? Feel free to ask any question!"

    if "thank" in q:
        return "Aww, you are so very welcome! 💙 I'm always right here whenever you need me. Keep up the awesome work! What would you like to explore next?"

    if "who are you" in q or "what are you" in q or "what can you do" in q:
        return "**I am StudyMate AI** — your ultimate, all-knowing AI tutor! 🎓🎬⚽\n\nI cover everything from **A to Z**:\n- 📚 **Academics & Science**: Computer Science, Mathematics, Physics, Chemistry, Biology, History, Literature\n- 🎬 **Entertainment & Movies**: Cinema, Marvel/DC, Anime, TV Shows, Music\n- ⚽ **Sports & Gaming**: Football, Basketball, Cricket, Esports, Trivia\n- 💡 **Study Tools**: Smart Quizzes, Flashcards, Summarizer & Memory System\n- ❤️ **Emotional Companion**: Caring, passionate, encouraging, or tough-love tutor!"

    # Science & Biology
    if "photosynthesis" in q:
        return (
            "🌱 **Photosynthesis** is the fundamental biological process by which green plants, algae, and cyanobacteria convert light energy from the sun into chemical energy stored in glucose.\n\n"
            "### 🔬 Chemical Equation:\n"
            "$$6\\text{CO}_2 + 6\\text{H}_2\\text{O} + \\text{sunlight} \\rightarrow \\text{C}_6\\text{H}_{12}\\text{O}_6 + 6\\text{O}_2$$\n\n"
            "### ⚙️ Step-by-Step Breakdown:\n"
            "1. **Sunlight Absorption**: Chlorophyll in the thylakoid membranes of chloroplasts captures photon energy.\n"
            "2. **Water Photolysis**: Light splits water molecules ($H_2O$), releasing Oxygen ($O_2$) into the atmosphere and producing $H^+$ ions & high-energy electrons.\n"
            "3. **ATP & NADPH Generation**: Electrons travel through an Electron Transport Chain (ETC) to synthesize ATP and NADPH.\n"
            "4. **Calvin Cycle (Dark Reaction)**: Occurs in the chloroplast stroma, using ATP and NADPH to convert Carbon Dioxide ($CO_2$) into Glucose ($C_6H_{12}O_6$).\n\n"
            "**Key Takeaway**: Photosynthesis generates the oxygen we breathe and forms the base of planetary energy food webs!"
        )

    if "mitosis" in q or "meiosis" in q:
        return (
            "🧬 **Cell Division: Mitosis vs Meiosis**\n\n"
            "| Feature | Mitosis | Meiosis |\n"
            "|---|---|---|\n"
            "| Purpose | Growth, tissue repair, asexual reproduction | Production of gametes (sperm & egg) |\n"
            "| Location | Somatic (body) cells | Germ cells |\n"
            "| Daughter Cells | 2 Genetically Identical Cells | 4 Genetically Unique Cells |\n"
            "| Chromosomes | Diploid ($2n$) | Haploid ($n$) |\n"
            "| Divisions | 1 Division | 2 Divisions (Meiosis I & II) |\n\n"
            "**Stages of Mitosis**: **P**rophase → **M**etaphase → **A**naphase → **T**elophase (**PMAT**)."
        )

    if "dna" in q or "rna" in q:
        return (
            "🧬 **DNA vs RNA:**\n\n"
            "- **DNA (Deoxyribonucleic Acid)**: Double-stranded helix containing genetic blueprints. Nitrogenous bases: Adenine (A), Thymine (T), Cytosine (C), Guanine (G).\n"
            "- **RNA (Ribonucleic Acid)**: Single-stranded molecule responsible for protein synthesis. Nitrogenous bases: Adenine (A), Uracil (U), Cytosine (C), Guanine (G).\n\n"
            "**Central Dogma of Biology**: `DNA` --(Transcription)--> `mRNA` --(Translation)--> `Protein`"
        )

    if "newton" in q or "law of motion" in q:
        return (
            "🍎 **Newton's Three Laws of Motion:**\n\n"
            "1. **First Law (Law of Inertia)**: An object remains at rest or in uniform motion unless acted upon by an external net force.\n"
            "2. **Second Law ($F = ma$)**: Force equals mass times acceleration. The force applied is proportional to the rate of momentum change.\n"
            "3. **Third Law (Action & Reaction)**: For every action, there is an equal and opposite reaction."
        )

    if "gravity" in q or "gravitation" in q:
        return (
            "🌌 **Gravity & Gravitation:**\n\n"
            "Gravity is the universal force of attraction acting between all matter.\n\n"
            "### Newton's Law of Universal Gravitation:\n"
            "$$F = G \\frac{m_1 m_2}{r^2}$$\n\n"
            "- $G = 6.674 \\times 10^{-11} \\text{ N}\\cdot\\text{m}^2/\\text{kg}^2$ (Gravitational constant)\n"
            "- $m_1, m_2$ = masses of the two objects\n"
            "- $r$ = distance between center of masses\n\n"
            "**Einstein's General Relativity View**: Gravity is not merely a force, but the curvature of spacetime caused by mass and energy!"
        )

    # Programming & Python
    if any(x in q for x in ["what is python", "python language", "python programming"]):
        return (
            "🐍 **Python Programming Language:**\n\n"
            "Python is a high-level, interpreted, general-purpose programming language famed for readability and simplicity.\n\n"
            "### 🌟 Key Features:\n"
            "- **Readable Syntax**: Clean indentations instead of curly braces\n"
            "- **Dynamically Typed**: No explicit variable type declaration required\n"
            "- **Extensive Ecosystem**: Used for Web Dev (Django/Flask/FastAPI), AI/ML (PyTorch/TensorFlow), Data Science (Pandas/NumPy), and Automation\n\n"
            "```python\n# Example: Hello World & Simple Loop\nnames = ['Alice', 'Bob', 'Charlie']\nfor name in names:\n    print(f'Hello, {name}!')\n```"
        )

    if "prime" in q and ("number" in q or "python" in q or "code" in q or "check" in q):
        return (
            "🔢 **Prime Number Check in Python:**\n\n"
            "A prime number is a natural number greater than 1 that has no positive divisors other than 1 and itself.\n\n"
            "```python\ndef is_prime(n):\n    if n <= 1:\n        return False\n    for i in range(2, int(n ** 0.5) + 1):\n        if n % i == 0:\n            return False\n    return True\n\n# Test cases\nprint(is_prime(11))  # True\nprint(is_prime(15))  # False\n```\n\n**Time Complexity**: $O(\\sqrt{n})$ efficiency by testing factors up to $\\sqrt{n}$."
        )

    if "list" in q and ("python" in q or "what is" in q):
        return (
            "📋 **Python Lists:**\n\n"
            "An ordered, mutable sequence of elements.\n\n"
            "```python\nnumbers = [10, 20, 30, 40]\nnumbers.append(50)       # Add element\nnumbers[1] = 25          # Modify element\nprint(numbers[0])        # Indexing -> 10\nprint(numbers[1:3])      # Slicing -> [25, 30]\n```\n\n**Key Methods**: `append()`, `pop()`, `insert()`, `remove()`, `sort()`, `reverse()`."
        )

    if "dictionary" in q or ("dict" in q and "python" in q):
        return (
            "📖 **Python Dictionaries:**\n\n"
            "An unordered/ordered (Python 3.7+), mutable collection of key-value pairs.\n\n"
            "```python\nstudent = {'name': 'Alex', 'grade': 'A', 'age': 20}\nprint(student['name'])          # Access key -> 'Alex'\nstudent['city'] = 'New York'    # Add key-value\n\nfor key, value in student.items():\n    print(f'{key}: {value}')\n```"
        )

    if "function" in q and ("python" in q or "def" in q or "what is" in q):
        return (
            "⚡ **Python Functions:**\n\n"
            "Reusable blocks of code defined using the `def` keyword.\n\n"
            "```python\ndef calculate_area(length, width=5):\n    '''Calculates rectangle area.'''\n    return length * width\n\narea1 = calculate_area(10)     # Uses default width=5 -> 50\narea2 = calculate_area(10, 4)  # Overrides width -> 40\n```"
        )

    if "class" in q and ("python" in q or "oop" in q or "object" in q):
        return (
            "🏗️ **Object-Oriented Programming (OOP) in Python:**\n\n"
            "OOP organizes code around objects containing data (attributes) and code (methods).\n\n"
            "```python\nclass Student:\n    def __init__(self, name, score):\n        self.name = name\n        self.score = score\n\n    def is_passing(self):\n        return self.score >= 50\n\ns1 = Student('Alice', 85)\nprint(s1.name, s1.is_passing())  # Alice True\n```\n\n**4 Pillar Principles of OOP**: **Encapsulation**, **Abstraction**, **Inheritance**, **Polymorphism**."
        )

    if "recursion" in q or "recursive" in q:
        return (
            "🔄 **Recursion:**\n\n"
            "A programming method where a function calls itself to solve smaller subproblems.\n\n"
            "```python\ndef factorial(n):\n    if n <= 1:      # Base Case (Stops infinite loop)\n        return 1\n    return n * factorial(n - 1)  # Recursive Step\n\nprint(factorial(5))  # 5 * 4 * 3 * 2 * 1 = 120\n```\n\n**Essential Rule**: Always include a **base case** to avoid Stack Overflow errors!"
        )

    # Data Structures & Algorithms
    if "big o" in q or "time complexity" in q:
        return (
            "📈 **Big-O Complexity Notation:**\n\n"
            "Measures how algorithm execution time or memory space grows as input size ($n$) grows.\n\n"
            "| Notation | Name | Common Example |\n"
            "|---|---|---|\n"
            "| $O(1)$ | Constant | Array indexing, Hash Table lookup |\n"
            "| $O(\\log n)$ | Logarithmic | Binary Search |\n"
            "| $O(n)$ | Linear | Linear Search |\n"
            "| $O(n \\log n)$ | Linearithmic | Merge Sort, Quick Sort (Average) |\n"
            "| $O(n^2)$ | Quadratic | Bubble Sort, Nested loops |\n"
            "| $O(2^n)$ | Exponential | Recursive Fibonacci |\n"
        )

    if "stack" in q and ("data" in q or "what" in q or "lifo" in q):
        return (
            "🥞 **Stack Data Structure (LIFO):**\n\n"
            "Last In, First Out structure.\n\n"
            "```python\nstack = []\nstack.append('Page 1')  # Push\nstack.append('Page 2')\ntop = stack.pop()       # Pop -> 'Page 2'\n```\n\n**Applications**: Browser undo/redo history, Function call execution stack, Expression evaluation."
        )

    if "queue" in q and ("data" in q or "what" in q or "fifo" in q):
        return (
            "🚶 **Queue Data Structure (FIFO):**\n\n"
            "First In, First Out structure.\n\n"
            "```python\nfrom collections import deque\nqueue = deque()\nqueue.append('User 1')   # Enqueue\nqueue.append('User 2')\nfront = queue.popleft() # Dequeue -> 'User 1'\n```\n\n**Applications**: Printer job scheduling, CPU task queues, Breadth-First Search (BFS)."
        )

    if "binary search" in q:
        return (
            "🔍 **Binary Search Algorithm:**\n\n"
            "Finds the target element in a **sorted array** by repeatedly halving the search interval ($O(\\log n)$ complexity).\n\n"
            "```python\ndef binary_search(arr, target):\n    low, high = 0, len(arr) - 1\n    while low <= high:\n        mid = (low + high) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            low = mid + 1\n        else:\n            high = mid - 1\n    return -1\n```"
        )

    # DBMS
    if "join" in q and ("sql" in q or "dbms" in q or "database" in q or "table" in q):
        return (
            "🔗 **SQL Joins:**\n\n"
            "Combines records from two or more tables based on a related column.\n\n"
            "```sql\n-- 1. INNER JOIN: Rows matching in BOTH tables\nSELECT s.name, c.course_name\nFROM students s\nINNER JOIN courses c ON s.course_id = c.id;\n\n-- 2. LEFT JOIN: All rows from left table + matching right rows\nSELECT s.name, c.course_name\nFROM students s\nLEFT JOIN courses c ON s.course_id = c.id;\n```\n\n**Summary**: **INNER** = Intersection | **LEFT** = Complete Left Table | **RIGHT** = Complete Right Table."
        )

    if "normalization" in q or "1nf" in q or "2nf" in q or "3nf" in q:
        return (
            "🗃️ **Database Normalization:**\n\n"
            "Process of organizing data to eliminate redundancy and update anomalies.\n\n"
            "- **1NF (First Normal Form)**: Single (atomic) values per cell, no repeating groups.\n"
            "- **2NF**: In 1NF + all non-key attributes are fully functionally dependent on the Primary Key.\n"
            "- **3NF**: In 2NF + no transitive dependencies (non-key columns dependent on other non-key columns).\n"
            "- **BCNF**: Stronger version of 3NF where every determinant is a candidate key."
        )

    if "acid" in q or "transaction" in q:
        return (
            "🛡️ **ACID Properties in Databases:**\n\n"
            "- **Atomicity**: 'All or nothing' execution of a transaction.\n"
            "- **Consistency**: Data stays valid according to all database constraints.\n"
            "- **Isolation**: Concurrent transactions execute independently without interference.\n"
            "- **Durability**: Committed changes persist permanently, even during power failures."
        )

    # Operating Systems
    if "deadlock" in q:
        return (
            "🔒 **Operating Systems Deadlock:**\n\n"
            "A situation where two or more processes are blocked forever, each holding a resource the other needs.\n\n"
            "### 4 Coffman Conditions for Deadlock:\n"
            "1. **Mutual Exclusion**: Non-shareable resource.\n"
            "2. **Hold and Wait**: Process holds resource while waiting for another.\n"
            "3. **No Preemption**: Resources cannot be forcibly taken.\n"
            "4. **Circular Wait**: Closed chain of processes waiting for each other.\n\n"
            "**Handling**: Deadlock Prevention (break 1 of 4 conditions), Banker's Algorithm for Avoidance, or Detection & Recovery."
        )

    if "process" in q and ("thread" in q or "difference" in q or "vs" in q):
        return (
            "⚡ **Process vs Thread:**\n\n"
            "| Attribute | Process | Thread |\n"
            "|---|---|---|\n"
            "| Definition | Executing program instance | Lightweight unit of execution within a process |\n"
            "| Memory | Independent memory space | Shares memory space with peer threads |\n"
            "| Overhead | High creation/context-switch time | Low creation/context-switch time |\n"
            "| Crash Impact | Isolated | One crashing thread can crash whole process |\n"
        )

    # Computer Networks
    if "tcp" in q and ("udp" in q or "difference" in q or "vs" in q):
        return (
            "🌐 **TCP vs UDP Protocol:**\n\n"
            "| Feature | TCP (Transmission Control Protocol) | UDP (User Datagram Protocol) |\n"
            "|---|---|---|\n"
            "| Connection | Connection-oriented (3-way handshake) | Connectionless |\n"
            "| Reliability | High (acknowledgments & retransmissions) | Best-effort (no guarantees) |\n"
            "| Speed | Slower due to overhead | Fast & lightweight |\n"
            "| Use Cases | Web browsing (HTTP/HTTPS), Email, File transfer | Video streaming, Online gaming, DNS, VoIP |\n"
        )

    if "http" in q and ("https" in q or "difference" in q):
        return (
            "🔒 **HTTP vs HTTPS:**\n\n"
            "- **HTTP (Hypertext Transfer Protocol)**: Unencrypted plain text transmission (Port 80).\n"
            "- **HTTPS (HTTP Secure)**: HTTP encrypted using **SSL/TLS** protocols (Port 443).\n\n"
            "**Why HTTPS matters**: Prevents eavesdropping, tampering, and Man-in-the-Middle (MitM) attacks!"
        )

    # AI & ML
    if "machine learning" in q or "deep learning" in q or "neural network" in q:
        return (
            "🤖 **Artificial Intelligence & Machine Learning:**\n\n"
            "Machine Learning (ML) enables computers to learn patterns from data without explicit programming.\n\n"
            "### 3 Types of ML:\n"
            "1. **Supervised Learning**: Model trained on labeled data (e.g. Linear Regression, Decision Trees).\n"
            "2. **Unsupervised Learning**: Finds hidden patterns in unlabeled data (e.g. K-Means Clustering, PCA).\n"
            "3. **Reinforcement Learning**: Agent learns by receiving rewards and penalties (e.g. AlphaGo, Robotics).\n\n"
            "**Deep Learning**: Subfield of ML using multi-layered Artificial Neural Networks inspired by human brains."
        )

    # Math Calculations
    if re.search(r'\d+\s*[\+\-\*\/]\s*\d+', q):
        try:
            expr = re.search(r'[\d\s\+\-\*\/\(\)\.]+', original)
            if expr:
                result = eval(expr.group().strip())
                return f"🔢 **Calculation Result:**\n\n`{original.strip()}` = **{result}**"
        except Exception:
            pass

    return None


def extract_memories(user_msg, assistant_reply):
    active_client = groq_client or openai_client
    if active_client:
        try:
            prompt = (
                f"Extract 0-2 memory items from this study chat.\n"
                f"User: {user_msg}\nAssistant: {assistant_reply[:300]}\n\n"
                f'Return JSON array only: [{{"category":"weak_area|preference|topic|insight","content":"short sentence","importance":1-3}}]\n'
                f"Return [] if nothing worth storing."
            )
            model = GROQ_MODEL if groq_client else OPENAI_MODEL
            resp = active_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1, max_tokens=200,
            )
            text = resp.choices[0].message.content.strip()
            m = re.search(r"\[.*\]", text, re.DOTALL)
            if m:
                return json.loads(m.group())
        except Exception:
            pass

    low = user_msg.lower()
    if any(p in low for p in ["weak in", "struggle with", "don't understand", "confused about"]):
        topic = re.sub(r".*(weak in|struggle with|don't understand|confused about)\s*", "", user_msg, flags=re.I).strip()
        return [{"category": "weak_area", "content": f"Weak in: {topic[:60]}", "importance": 2}]
    if len(user_msg) > 10:
        return [{"category": "topic", "content": f"Studied: {user_msg[:50]}", "importance": 1}]
    return []


extract_memories_from_chat = extract_memories  # alias for chat.py


def detect_mood(message):
    low = message.lower()
    if any(w in low for w in ["stressed", "anxious", "scared", "overwhelmed", "panic", "exam tomorrow"]):
        return "stressed"
    if any(w in low for w in ["confused", "don't get", "don't understand", "lost", "hard", "difficult"]):
        return "confused"
    if any(w in low for w in ["easy", "got it", "i know", "confident", "understand now", "makes sense"]):
        return "confident"
    if any(w in low for w in ["tired", "sleepy", "exhausted", "can't focus"]):
        return "tired"
    return "neutral"


def generate_quiz(content, quiz_type="mcq", count=5):
    active_client = groq_client or openai_client
    if active_client:
        try:
            kind = "multiple choice with exactly 4 options" if quiz_type == "mcq" else "short answer"
            prompt = (
                f"Create {count} {kind} questions from this study material.\n\n"
                f"MATERIAL:\n{content[:6000]}\n\n"
                f"Return ONLY valid JSON:\n"
                f'{{"title":"Quiz Title","questions":[{{"question":"...","options":["A","B","C","D"],"correct_answer":"exact option text","explanation":"why correct"}}]}}\n'
                f"For short_answer set options to null."
            )
            model = GROQ_MODEL if groq_client else OPENAI_MODEL
            resp = active_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4, max_tokens=2500,
            )
            text = resp.choices[0].message.content.strip()
            m = re.search(r"\{.*\}", text, re.DOTALL)
            if m:
                return json.loads(m.group())
        except Exception as e:
            print(f"[AI] Quiz error: {e}")
    return _fallback_quiz(content, quiz_type, count)


def generate_flashcards(content, count=10):
    active_client = groq_client or openai_client
    if active_client:
        try:
            prompt = (
                f"Create {count} flashcards from this study material.\n\n"
                f"MATERIAL:\n{content[:6000]}\n\n"
                f'Return ONLY valid JSON: {{"cards":[{{"front":"term or question","back":"definition or answer"}}]}}'
            )
            model = GROQ_MODEL if groq_client else OPENAI_MODEL
            resp = active_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4, max_tokens=2000,
            )
            text = resp.choices[0].message.content.strip()
            m = re.search(r"\{.*\}", text, re.DOTALL)
            if m:
                return json.loads(m.group())
        except Exception as e:
            print(f"[AI] Flashcard error: {e}")
    return _fallback_flashcards(content, count)


def _fallback_quiz(content, quiz_type, count):
    lines = [l.strip() for l in content.split("\n") if len(l.strip()) > 15]
    questions = []
    if not lines:
        lines = [
            "SQL Joins combine records from two database tables.",
            "Primary Keys uniquely identify each row in a database table.",
            "Binary Search requires a sorted array to search in O(log n) time.",
            "Recursion is a programming technique where a function calls itself.",
            "Photosynthesis converts light energy into chemical energy in plants."
        ]
    for i in range(min(count, max(1, len(lines)))):
        sample = lines[i % len(lines)]
        words = sample.split()
        kw = words[0].strip(".,;()") if len(words) > 0 else "Concept"
        if len(words) > 2:
            kw = " ".join(words[:2]).strip(".,;()")

        if quiz_type == "mcq":
            correct = f"It is a core concept: {sample[:70]}"
            opts = [
                correct,
                f"It is unrelated to the subject domain",
                f"It contradicts established analytical principles",
                f"None of the above"
            ]
            questions.append({
                "question": f"Which statement best describes '{kw}'?",
                "options": opts,
                "correct_answer": correct,
                "explanation": f"Reference: '{sample}'"
            })
        else:
            questions.append({
                "question": f"Explain the significance of '{kw}'.",
                "options": None,
                "correct_answer": sample,
                "explanation": f"Reference: '{sample}'"
            })
    return {"title": "Study Knowledge Quiz", "questions": questions}


def _fallback_flashcards(content, count):
    lines = [l.strip() for l in content.split("\n") if len(l.strip()) > 15]
    cards = []
    for i in range(min(count, max(3, len(lines)))):
        line = lines[i % len(lines)]
        parts = line.split(":", 1) if ":" in line else line.split(" - ", 1)
        if len(parts) == 2:
            cards.append({"front": parts[0].strip(), "back": parts[1].strip()})
        else:
            words = line.split()
            term = " ".join(words[:3]) if len(words) >= 3 else f"Concept {i+1}"
            cards.append({"front": f"What is {term}?", "back": line})
    if not cards:
        cards = [
            {"front": "What is a Primary Key?", "back": "A unique identifier for each record in a database table."},
            {"front": "What is Big-O Notation?", "back": "A mathematical notation describing algorithm time/space complexity."},
            {"front": "What is Recursion?", "back": "A function that calls itself to solve a smaller version of the same problem."},
        ]
    return {"cards": cards}
