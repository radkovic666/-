import random
import ctypes
import shutil
import re
import time
import os
import ollama
from gtts import gTTS
import pygame
from io import BytesIO
import hashlib
from nltk.stem import WordNetLemmatizer
import socket
import json

ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 3)

# Initialize NLTK components
lemmatizer = WordNetLemmatizer()
try:
    from nltk.corpus import wordnet
except:
    import nltk
    nltk.download('wordnet')
    nltk.download('omw-1.4')
    from nltk.corpus import wordnet

SOUND_TOGGLE_FILE = "sound_config.json"
FORCE_NETWORK_OFF = False
QUESTION_HISTORY_FILE = "question_history.json"
QUESTIONS_FILE = "questions.json"
FACT_CHECK_CACHE = {}

def load_history():
    try:
        with open(QUESTION_HISTORY_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()

QUESTION_HISTORY = load_history()

def save_history():
    with open(QUESTION_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(list(QUESTION_HISTORY), f, ensure_ascii=False)

def load_generated_questions():
    try:
        with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

GENERATED_QUESTIONS = load_generated_questions()

def save_generated_questions():
    with open(QUESTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(GENERATED_QUESTIONS, f, ensure_ascii=False, indent=2)

# Game Constants
НАГРАДИ = [
    "100 лева", "200 лева", "300 лева", "400 лева", "500 лева",
    "1000 лева", "1500 лева", "2000 лева", "3000 лева", "5000 лева",
    "10000 лева", "20000 лева", "30000 лева", "50000 лева", "100000 лева"
]

НИВА_НА_ТРУДНОСТ = {
    "100 лева": "основно ниво",
    "200 лева": "основно ниво",
    "300 лева": "основно ниво", 
    "400 лева": "контекстуално разбиране",
    "500 лева": "контекстуално разбиране",
    "1000 лева": "междинно аналитично",
    "1500 лева": "междинно аналитично",
    "2000 лева": "комплексни връзки", 
    "3000 лева": "комплексни връзки",
    "5000 лева": "специфична експертиза",
    "10000 лева": "специфична експертиза",
    "20000 лева": "критичен анализ",
    "30000 лева": "критичен анализ",
    "50000 лева": "мултидисциплинарно",
    "100000 лева": "научно изследователско"
}

ЗАЩИТНИ_НИВА = ["500 лева", "5000 лева"]
КАТЕГОРИИ = [
    "История на великите империи", 
    "Географски загадки и световни чудеса", 
    "Наука и природа: От атома до галактиката", 
    "Спортни легенди и епични моменти", 
    "Технологии на бъдещето", 
    "Литературни шедьоври и авторски тайни", 
    "Световна кухня: От улична храна до мишлен", 
    "Митология и легенди: Богове и герои", 
    "Видеоигри: От ретро до eSports", 
    "Музика през десетилетията: От класика до K-pop", 
    "Космос и астрономия: Тайните на Вселената", 
    "Гатанки и пъзели: Изпитай мозъка си", 
    "Известни цитати: Мъдростта на великите", 
    "Странни закони по света: Невероятно, но истинско", 
    "Световни рекорди: От най-странното до най-впечатляващото", 
    "Изкуство и култура: Шедьоври и революции", 
    "Мода и стил: От Виван до метавселената", 
    "Философия: Великите мислители и идеи", 
    "Психология: Тайните на човешкия ум", 
    "Медии и журналистика: От печат до дигитална ера", 
    "Здраве и фитнес: Науката зад доброто самочувствие", 
    "История на изкуствата: От пещерите до NFT", 
    "Фантастика и научна фантастика: Светове извън въображението", 
    "Религии и вярвания: Тайните на духовното", 
    "Изобретения и открития: От колелото до квантовия компютър", 
    "Социални мрежи: От Friendster до TikTok", 
    "Животни и животински свят: От динозаврите до ДНК", 
    "Архитектура и строителство: От пирамидите до небостъргачите", 
    "Кино и телевизионни сериали: От класики до стрийминг", 
    "Биографии на известни личности: От гении до революционери", 
    "Екологични проблеми и устойчиво развитие: Спасяване на планетата", 
    "Водни ресурси и океани: Тайните на синьото", 
    "Транспорт и инфраструктура: От конските каруци до хиперлупа", 
    "Празници и тържества по света: Традиции и култури", 
    "История на модата: От корсети до виртуални дрехи", 
    "Научни теории и открития: От Айнщайн до Хигс", 
    "Класическа музика: От Моцарт до оркестри в метавселената", 
    "Хора и култури по света: Разнообразие и традиции", 
    "Археология и древни цивилизации: От Египет до Мая", 
    "Световни икономики: От златото до криптото", 
    "Математика и логика: Загадки и теории", 
    "Криптозоология: Митове и легенди за същества", 
    "Урбани легенди: Градски истории и мистерии", 
    "Български традиции и забележителности", 
    "Съвременна България: Иновации и култура", 
    "Екстремни спортове: От сноуборд до бейсджампинг", 
    "Дигитални технологии: От интернет до изкуствен интелект", 
    "Космически изследвания: От Луната до Марс", 
    "Глобални предизвикателства: Климат и устойчивост", 
    "Забавна наука: Експерименти и феномени"
]

ПОМОЩНИЦИ = {
    "1": "50:50",
    "2": "Обади се на приятел",
    "3": "Помощ от публиката"
}

СТОП_ДУМИ = {}

LATIN_TO_BG_SPEECH = {
    'A': 'А',
    'B': 'Бе',
    'C': 'Це',
    'D': 'Де'
}

CYRILLIC_TO_LATIN = {
    'А': 'A',
    'Б': 'B',
    'В': 'C',
    'Г': 'D',
    'A': 'A',
    'B': 'B',
    'C': 'C',
    'D': 'D'
}

USE_TTS = True

def print_centered(text):
    terminal_width = shutil.get_terminal_size().columns
    padding = (terminal_width - len(text)) // 2
    print(' ' * padding + text)

def check_internet():
    global FORCE_NETWORK_OFF
    if FORCE_NETWORK_OFF:
        return False
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False

def говори(текст):
    global USE_TTS
    
    if not USE_TTS or not check_internet():
        return
    
    try:
        tts = gTTS(text=текст, lang='bg')
        audio_buffer = BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        
        if not pygame.mixer.get_init():
            pygame.mixer.init()
            
        pygame.mixer.music.load(audio_buffer)
        pygame.mixer.music.play()
        
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
            
    except Exception as e:
        USE_TTS = False

def load_sound_config():
    global USE_TTS, FORCE_NETWORK_OFF
    try:
        with open(SOUND_TOGGLE_FILE, "r") as f:
            config = json.load(f)
            USE_TTS = config.get("tts_enabled", check_internet())
            FORCE_NETWORK_OFF = config.get("force_network_off", False)
    except:
        USE_TTS = check_internet()
        FORCE_NETWORK_OFF = False

def save_sound_config():
    with open(SOUND_TOGGLE_FILE, "w") as f:
        json.dump({
            "tts_enabled": USE_TTS,
            "force_network_off": FORCE_NETWORK_OFF
        }, f)

def normalize_text(text):
    text = re.sub(r'[^\w\s]', '', text.lower())
    words = re.findall(r'\w+', text)
    cleaned = [lemmatizer.lemmatize(w) for w in words if w not in СТОП_ДУМИ]
    return ' '.join(sorted(cleaned))

def get_temperature(difficulty):
    if difficulty == "основно ниво":
        return max(0.3, 0.5 - (random.random() * 0.1))
    elif difficulty == "контекстуално разбиране":
        return max(0.25, 0.45 - (random.random() * 0.1))
    elif difficulty == "междинно аналитично":
        return max(0.2, 0.4 - (random.random() * 0.1))
    elif difficulty == "комплексни връзки":
        return max(0.18, 0.38 - (random.random() * 0.1))
    elif difficulty == "специфична експертиза":
        return max(0.15, 0.35 - (random.random() * 0.1))
    elif difficulty == "критичен анализ":
        return max(0.12, 0.32 - (random.random() * 0.1))
    elif difficulty == "мултидисциплинарно":
        return max(0.1, 0.3 - (random.random() * 0.1))
    elif difficulty == "научно изследователско":
        return max(0.08, 0.28 - (random.random() * 0.1))
    else:
        return 0.3  # Default temperature

def нормализирай_въпрос(въпрос, отговори):
    q_norm = normalize_text(въпрос)
    a_norm = ' '.join(sorted(normalize_text(a) for a in отговори.values()))
    return q_norm + a_norm

def verify_fact(question, correct_answer):
    cache_key = f"{question}|{correct_answer}"
    if cache_key in FACT_CHECK_CACHE:
        return FACT_CHECK_CACHE[cache_key]
    
    FACT_CHECK_CACHE[cache_key] = random.random() > 0.1
    return FACT_CHECK_CACHE[cache_key]

def генерирай_въпрос(трудност, категория):
    заявка = f"""
Създай прецизно формулиран въпрос за „Стани Богат“ от категория {категория} със следни характеристики:
- Сложност: {трудност}
- Избягвай уводни думи съдържащи категория и трудност.

Критерии за трудност:
► Основно ниво: Директни факти
► Контекстуално разбиране: Изисква интерпретация
► Междинно аналитично: Сравняване на концепции
► Комплексни връзки: Връзки между различни области
► Специфична експертиза: Знания извън общата култура
► Критичен анализ: Противоречиви мнения
► Мултидисциплинарно: Интеграция на концепции
► Научно изследователско: Последни открития

Пример:
[Генериран въпрос...]
A) [Отговор различен от B,C и D]
B) [Отговор различен от A,C и D] 
C) [Отговор различен от A,B и D]
D) [Верен отговор различен от A,B и C]
Отговор: D
"""

    отговор = ollama.chat(
        model="todorov/bggpt:latest",
        messages=[{"role": "user", "content": заявка}],
        options={
    'temperature': get_temperature(трудност),  # Dynamic temperature based on difficulty
    'num_predict': 96,
    'top_k': 30,
    'top_p': 0.4,
    'repeat_penalty': 1.1,
    'seed': int(time.time() * 1000) % 100000
        }
    )
    
    съдържание = отговор['message']['content']
    съвпадение = re.search(
        r"(.*?)\nA\) (.*?)\nB\) (.*?)\nC\) (.*?)\nD\) (.*?)\nОтговор: ?([A-D])",
        съдържание,
        re.DOTALL
    )
    
    if съвпадение:
        верен = CYRILLIC_TO_LATIN.get(съвпадение.group(6).strip().upper(), съвпадение.group(6).strip().upper())
        верен = верен[0] if isinstance(верен, tuple) else верен
        
        question_data = {
            "въпрос": съвпадение.group(1).strip(),
            "отговори": {
                "A": съвпадение.group(2).strip(),
                "B": съвпадение.group(3).strip(),
                "C": съвпадение.group(4).strip(),
                "D": съвпадение.group(5).strip()
            },
            "верен": верен,
            "категория": категория,
            "трудност": трудност,
            "награда": None
        }
        
        fingerprint = hashlib.md5(
            нормализирай_въпрос(question_data['въпрос'], question_data['отговори']).encode()
        ).hexdigest()
        
        question_data['fingerprint'] = fingerprint
        return question_data
    return None

def validate_question(q_data):
    global GENERATED_QUESTIONS
    
    fingerprint = q_data['fingerprint']
    existing_fingerprints = {q['fingerprint'] for q in GENERATED_QUESTIONS}
    
    if fingerprint in QUESTION_HISTORY or fingerprint in existing_fingerprints:
        return False
        
    correct = q_data['верен']
    if correct not in ["A","B","C","D"]:
        return False
        
    if not verify_fact(q_data['въпрос'], q_data['отговори'][correct]):
        return False
        
    q_words = set(normalize_text(q_data['въпрос']).split())
    a_words = set(normalize_text(q_data['отговори'][correct]).split())
    if len(q_words & a_words) > 2:
        return False
        
    QUESTION_HISTORY.add(fingerprint)
    save_history()
    
    GENERATED_QUESTIONS.append(q_data)
    save_generated_questions()
    
    return True

def предварителни_въпроси():
    shuffled_categories = random.sample(КАТЕГОРИИ, len(КАТЕГОРИИ))
    backup_cats = КАТЕГОРИИ * 2
    used_combinations = set()

    print_centered("\nНастанете се удобно, играта ще започне всеки момент...")
    
    for i, награда in enumerate(НАГРАДИ):
        трудност = НИВА_НА_ТРУДНОСТ[награда]
        question_generated = False
        attempts = 0
        
        while not question_generated and attempts < 50:
            if attempts < len(shuffled_categories) * 2:
                current_category = shuffled_categories[(i + attempts) % len(shuffled_categories)]
            else:
                current_category = random.choice(backup_cats)
            
            if (current_category, трудност) in used_combinations:
                attempts += 1
                continue
                
            used_combinations.add((current_category, трудност))
            
            for gen_attempt in range(10):
                въпрос = генерирай_въпрос(трудност, current_category)
                if въпрос and validate_question(въпрос):
                    въпрос['награда'] = награда
                    yield въпрос
                    question_generated = True
                    break
                else:
                    alt_tрудност = random.choice(list(НИВА_НА_ТРУДНОСТ.values()))
                    въпрос = генерирай_въпрос(alt_tрудност, current_category)
                    if въпрос and validate_question(въпрос):
                        въпрос['награда'] = награда
                        въпрос['трудност'] = трудност
                        yield въпрос
                        question_generated = True
                        break
            
            attempts += 1
            
        if not question_generated:
            continue

    print()

def използвай_помощник(налични_помощници, верен_отговор, отговори, трудност):
    if not налични_помощници:
        return

    while True:
        print("\nЖокерите с които разполагате:")
        for номер, помощник in налични_помощници.items():
            print(f"{номер}) {помощник}")

        избор = input("Въведете жокер 1), 2) или 3) (или Enter за отказ): ").strip()
        if избор == '':
            break

        if избор in налични_помощници:
            използван = налични_помощници.pop(избор)

            if използван == "50:50":
                грешни = [к for к in отговори if к != верен_отговор]
                random.shuffle(грешни)
                за_премахване = грешни[:2]
                for к in за_премахване:
                    del отговори[к]
                говори("Избрахте жокер петдесет на петдесет. Оставащите отговори са: ")
                for к, т in отговори.items():
                    bg_letter = LATIN_TO_BG_SPEECH.get(к, к)
                    говори(f"{bg_letter}) {т}")
                return
                
            elif използван == "Обади се на приятел":
                bg_letter = LATIN_TO_BG_SPEECH.get(верен_отговор, верен_отговор)
                print(f"\nМисля, че верният отговор е {отговори[верен_отговор]}")
                говори(f"Вашият приятел предложи {bg_letter} като верен отговор")

            elif използван == "Помощ от публиката":
                difficulty_probs = {
                    "основно ниво": 90, "контекстуално разбиране": 68, "междинно аналитично": 59,
                    "комплексни връзки": 42, "специфична експертиза": 35, "критичен анализ": 28,
                    "мултидисциплинарно": 20, "научно изследователско": 12
                }
                
                base_prob = difficulty_probs.get(трудност, 50)
                remaining = 100 - base_prob
                wrong_answers = [k for k in отговори if k != верен_отговор]
                
                percentages = {верен_отговор: base_prob}
                weights = [random.random() for _ in wrong_answers]
                total_weight = sum(weights) or 1
                
                for i, key in enumerate(wrong_answers):
                    percentages[key] = round((weights[i]/total_weight) * remaining, 1)
                
                total = sum(percentages.values())
                if total != 100:
                    percentages[верен_отговор] += round(100 - total, 1)
                
                print("\nРезултати от публиката:")
                for key in ['A', 'B', 'C', 'D']:
                    if key in отговори:
                        print(f"{key}) {percentages.get(key, 0)}%")
                    else:
                        print(f"{key}) ---")
                
                говори("Резултати от публиката:")
                for key in ['A', 'B', 'C', 'D']:
                    if key in отговори and key in percentages:
                        bg_letter = LATIN_TO_BG_SPEECH.get(key, key)
                        говори(f"{bg_letter}) {percentages[key]} процента")
            print("\nИграта ще продължи след секунди...")
            time.sleep(3)    
            break
        else:
            print(f"Невалиден избор, опитайте отново.")

def display_question(въпрос, текуща_награда, отговори, speak=True):
    # Load the frame template
    with open('frame.txt', 'r', encoding='utf-8') as f:
        frame = [line.rstrip('\n') for line in f]

    # Display the question in the frame
    line_idx, start, end = (9, 85, 135)
    max_length = end - start
    question_text = въпрос['въпрос']

    if len(question_text) > max_length:
        # Split the question into two parts
        mid = len(question_text) // 2
        part1 = question_text[:mid]
        part2 = question_text[mid:]

        # Center and pad each part
        part1_chars = list(part1.center(max_length).ljust(max_length))
        part2_chars = list(part2.center(max_length).ljust(max_length))

        # Update the frame with the first part of the question
        question_line = list(frame[line_idx])
        question_line[start:end] = part1_chars
        frame[line_idx] = ''.join(question_line)

        # Update the frame with the second part of the question (on the next line)
        question_line = list(frame[line_idx + 1])  # Use the next line
        question_line[start:end] = part2_chars
        frame[line_idx + 1] = ''.join(question_line)
    else:
        # If the question fits in one line, center and pad it
        question_chars = list(question_text.center(max_length).ljust(max_length))
        question_line = list(frame[line_idx])
        question_line[start:end] = question_chars
        frame[line_idx] = ''.join(question_line)

    # Show initial frame with question
    os.system('cls' if os.name == 'nt' else 'clear')
    print_centered(f"Въпрос за {текуща_награда}")
    print_centered("=" * (len(текуща_награда) + 10))
    print()
    print('\n'.join(frame))

    # TTS for the question
    if speak and USE_TTS:
        говори(f"Въпрос за {текуща_награда}")
        говори(въпрос['въпрос'])

    # Define answer positions
    answer_positions = [
        ('A', 20, 35, 90),
        ('B', 20, 150, 180),
        ('C', 30, 35, 90),
        ('D', 30, 150, 180)
    ]

    # Update answers in the frame
    for key, line_idx, start, end in answer_positions:
        if key in отговори:  # Only process existing answers
            answer_line = list(frame[line_idx])
            answer_text = f"{key}) {отговори[key]}"
            answer_chars = list(answer_text.ljust(end - start - 1))
            answer_line[start:end] = answer_chars
            frame[line_idx] = ''.join(answer_line)

            # Redraw the frame
            os.system('cls' if os.name == 'nt' else 'clear')
            print_centered(f"Въпрос за {текуща_награда}")
            print_centered("=" * (len(текуща_награда) + 10))
            print()
            print('\n'.join(frame))

            # TTS for the answer
            if speak and USE_TTS:
                bg_letter = LATIN_TO_BG_SPEECH.get(key, key)
                говори(f"{bg_letter}) {отговори[key]}")

def получи_отговор(отговори):
    while True:
        избор = input("\nВашият отговор (A, B, C или D): ").strip().upper()
        if избор in отговори:
            return избор
        print("Невалиден избор. Моля изберете A, B, C или D.")

def стартирай_игра():
    global USE_TTS
    load_sound_config()
    
    os.system('cls' if os.name == 'nt' else 'clear')
    print_centered("\nДОБРЕ ДОШЛИ В СТАНИ БОГАТ!")
    
    if USE_TTS:
        говори("Добре дошли на стола на богатството!")
    else:
        print("Режим без звук")

    защитено_ниво = None
    помощници = ПОМОЩНИЦИ.copy()

    for въпрос in предварителни_въпроси():
        текуща_награда = въпрос['награда']
        трудност = НИВА_НА_ТРУДНОСТ[текуща_награда]
        отговори = въпрос['отговори'].copy()
        initial_display = True

        while True:
            display_question(въпрос, текуща_награда, отговори, speak=initial_display)
            initial_display = False
            
            user_input = input("\nВъведете отговор или Enter за жокер: ").strip().upper()

            if user_input in отговори:
                избор = user_input
                break
            elif user_input == '' and помощници:
                използвай_помощник(помощници, въпрос['верен'], отговори, трудност)
                #display_question(въпрос, текуща_награда, отговори, speak=False)
            else:
                print("Невалиден избор, опитайте отново.")
                time.sleep(1)
                #display_question(въпрос, текуща_награда, отговори, speak=False)

        if избор == въпрос['верен']:
            print(f"\nВЯРНО! Печелите {текуща_награда}!")
            говори(f"Верен отговор! Печелите {текуща_награда}!")

            if текуща_награда in ЗАЩИТНИ_НИВА:
                защитено_ниво = текуща_награда
                print(f"\nДОСТИГНАХТЕ СИГУРНА СУМА: {защитено_ниво}!")
                говори(f"Поздравления! Достигнахте сигурна сума от {защитено_ниво}!")
        else:
            верен_отговор = въпрос['верен']
            bg_letter = LATIN_TO_BG_SPEECH.get(верен_отговор, верен_отговор)
            print(f"\nГРЕШКА! Верен отговор: {въпрос['отговори'][верен_отговор]}")
            говори(f"Съжалявам, верният отговор беше {bg_letter}) {въпрос['отговори'][верен_отговор]}")
            print(f"\nНапуснахте с {защитено_ниво if защитено_ниво else '0 лева'}!")
            говори(f"Напуснахте играта с {защитено_ниво if защитено_ниво else 'нищо'}!")
            return

        time.sleep(2)

    print_centered("\n!!! СПЕЧЕЛИХТЕ ГОЛЯМАТА НАГРАДА ОТ 100 000 ЛЕВА !!!")
    говори("Невероятно! Вие спечелихте 100000 лева!")

if __name__ == "__main__":
    load_sound_config()
    
    while True:
        #FACT_CHECK_CACHE.clear()
        os.system('cls' if os.name == 'nt' else 'clear')
        with open('splash.txt', 'r') as file:
            contents = file.read()
            print_centered(contents)
        
        print_centered("\n[Enter] Нова игра | [X] Нулирай въпроси | [C] Настройки | [Друг клавиш] Изход")
        избор = input().strip().upper()

        if избор == 'X':
            QUESTION_HISTORY.clear()
            save_history()
            GENERATED_QUESTIONS.clear()
            save_generated_questions()
            print_centered("\nВсички въпроси са нулирани!")
            FACT_CHECK_CACHE.clear()
            time.sleep(1.5)
        
        elif избор == 'C':
            print("\nНастройки:")
            print("[M] Преключване на звука")
            print("[Друг клавиш] Назад")
            sub_choice = input("Избор: ").strip().upper()
            
            if sub_choice == 'M':
                USE_TTS = not USE_TTS
                if USE_TTS:
                    FORCE_NETWORK_OFF = False
                else:
                    FORCE_NETWORK_OFF = True
                save_sound_config()
                status = "включен" if USE_TTS else "изключен"
                print_centered(f"\nЗвукът е {status}")
                if USE_TTS:
                    говори(f"Звукът е {status}")
                time.sleep(1)
        
        elif избор == '':
            стартирай_игра()
            print_centered("\n[Enter] Към меню | [Друг клавиш] Изход")
            game_choice = input().strip().upper()
            if game_choice != '':
                break
        
        else:
            print_centered("\nБлагодарим за участието! До скоро!")
            if USE_TTS:
                говори("Довиждане!")
            break
