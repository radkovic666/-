import random
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

# Initialize NLTK components
lemmatizer = WordNetLemmatizer()
try:
    from nltk.corpus import wordnet
except:
    import nltk
    nltk.download('wordnet')
    nltk.download('omw-1.4')
    from nltk.corpus import wordnet

# Game Constants
НАГРАДИ = [
    "100 лева", "200 лева", "300 лева", "400 лева", "500 лева",
    "1000 лева", "1500 лева", "2000 лева", "3000 лева", "5000 лева",
    "10000 лева", "20000 лева", "30000 лева", "50000 лева", "100000 лева"
]

НИВА_НА_ТРУДНОСТ = {
    "100 лева": "лесна", "200 лева": "лесна",
    "300 лева": "лесна", "400 лева": "средна",
    "500 лева": "средна", "1000 лева": "средна",
    "1500 лева": "умерена", "2000 лева": "умерена",
    "3000 лева": "предизвикателна", "5000 лева": "предизвикателна",
    "10000 лева": "трудна", "20000 лева": "много трудна",
    "30000 лева": "експертна", "50000 лева": "експертна", 
    "100000 лева": "най-висока"
}

ЗАЩИТНИ_НИВА = ["500 лева", "5000 лева"]
КАТЕГОРИИ = [
    "Българска история", "Световна история", "Физика и Астрономия", "Арт","Mузика","Световна литература",
    "Биология","Информационни технологии", "Математика","Медицина", "Българска политика", "Българска литература", "Граматика",
    "Други Религии", "Български традиции и обичаи", "Световна политика", "Спорт", "Мода и лайфстайл", "География","Пари и Финанси", "Чужди Езици"
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

USED_QUESTIONS = set()
USE_TTS = True

def check_internet():
    """Check internet connectivity"""
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False

def говори(текст):
    """Генерира и възпроизвежда говор от подаден текст в паметта."""
    global USE_TTS
    
    if not USE_TTS:
#        print(f"{текст}")
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
        print(f"Режим без звук: {текст}")
        USE_TTS = False

def нормализирай_въпрос(въпрос, отговори):
    def process_text(text):
        words = re.findall(r'\w+', text.lower())
        return ' '.join([lemmatizer.lemmatize(word) for word in words])
    
    q_norm = process_text(въпрос)
    a_norm = ' '.join([process_text(ans) for ans in sorted(отговори.values())])
    return q_norm + ' ' + a_norm

def генерирай_въпрос(трудност, категория):
    заявка = f"""
Генерирай въпрос в стил от телевизионното предаване „Стани Богат“ от категория {категория}, който да е с {трудност} трудност.
Ако категорията е Математика, напиши правилна задача може и текстова и да има истински логически изправен правилен отговор.
Не задавай въпрос "Кой български владетел е известен с прозвището "Цар Освободител"?" или "Кой български цар е известен с прозвището "Цар Освободител""
Примерен формат:
На колко е равно две плюс две умножено по две 2+2*2?

A) 12
B) 6
C) 16
D) 8
Отговор: B

или 

Коя европейска столица носи името на един от най-известните магистри от ордена на йоанитите?
А. Дъблин
В. Валета
С. Вадуц
D. Мадрид
Отговор: B
"""

    отговор = ollama.chat(
        model="todorov/bggpt:latest",
        messages=[{"role": "user", "content": заявка}],
        options={
            'temperature': random.uniform(0.1, 0.2),
            'num_predict': 200,
            'seed': random.randint(1, 1000)
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
            "категория": категория
        }
        
        fingerprint = hashlib.md5(
            нормализирай_въпрос(question_data['въпрос'], question_data['отговори']).encode()
        ).hexdigest()
        
        question_data['fingerprint'] = fingerprint
        return question_data
    return None

def предварителни_въпроси():
    въпроси = []
    shuffled_categories = random.sample(КАТЕГОРИИ, len(КАТЕГОРИИ))
    
    print("\nКомпютърът подготвя въпросите...")
    
    for i, награда in enumerate(НАГРАДИ):
        трудност = НИВА_НА_ТРУДНОСТ[награда]
        original_category = shuffled_categories[i % len(shuffled_categories)]
        current_category = original_category
        question_generated = False
        category_attempts = 0

        while not question_generated:
            опити = 0
            while опити < 10:
                въпрос = генерирай_въпрос(трудност, current_category)
                if въпрос and въпрос['fingerprint'] not in USED_QUESTIONS:
                    USED_QUESTIONS.add(въпрос['fingerprint'])
                    въпрос['награда'] = награда
                    въпроси.append(въпрос)
                    question_generated = True
                    break
                опити += 1

            if not question_generated:
                current_category = random.choice(КАТЕГОРИИ)
                category_attempts += 1
                if category_attempts > 3:
                    raise Exception(f"Неуспешно генериране на въпрос за {награда}")

            progress = (i + 1) / len(НАГРАДИ)
            print(f"\r[{'▓' * int(30*progress)}{'░' * (30-int(30*progress))}] {int(100*progress)}%", end='')

    print()
    return въпроси

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
                print("Избрахте жокер 50:50")
                for к, т in отговори.items():
                    print(f"{к}) {т}")
                говори("Избрахте жокер 50 на 50, а отговорите които остават са: ")
                for к, т in отговори.items():
                    bg_letter = LATIN_TO_BG_SPEECH.get(к, к)
                    говори(f"{bg_letter}) {т}")
                return
                
            elif използван == "Обади се на приятел":
                print("Избрахте жокер - Обади се на приятел.")
                говори("Избрахте жокер - oбади се на приятел.")
                bg_letter = LATIN_TO_BG_SPEECH.get(верен_отговор, верен_отговор)
                print(f"\nМисля, че верният отговор е {отговори[верен_отговор]}")
                говори(f"Вашият приятел предложи {bg_letter} като верен отговор")

            elif използван == "Помощ от публиката":
                print("Избрахте жокер - Помощ от публиката.")
                говори("Избрахте жокер - Помощ от публиката.")
                difficulty_probs = {
                    "най-лесно": 70, "лесно": 60, "средно": 50,
                    "умерено": 40, "предизвикателно": 35, "трудно": 20,
                    "много трудно": 15, "експертно": 10, "най-високо": 5
                }
                base_prob = difficulty_probs.get(трудност, 50)
                
                remaining = 100 - base_prob
                wrong_answers = [k for k in отговори if k != верен_отговор]
                
                if not wrong_answers:
                    print(f"Публиката 100% подкрепя {верен_отговор}) {отговори[верен_отговор]}")
                    говори(f"Публиката смята, че {LATIN_TO_BG_SPEECH.get(верен_отговор, верен_отговор)} е верен отговор със 100% увереност.")
                    continue
                
                weights = [random.random() for _ in wrong_answers]
                total_weight = sum(weights) or 1
                
                percentages = {верен_отговор: base_prob}
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
            time.sleep(3)
            break
        else:
            print(f"/nНевалиден избор, опитайте отново.")

def display_question(въпрос, текуща_награда, отговори, speak):
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"\nВъпрос за {текуща_награда} | Категория: {въпрос['категория']}")
    if speak:
        говори(f"Въпрос за {текуща_награда}")
    print("\n" + въпрос['въпрос'])
    if speak:
        говори(въпрос['въпрос'])
    for буква, текст in отговори.items():
        print(f"{буква}) {текст}")
        if speak:
            bg_letter = LATIN_TO_BG_SPEECH.get(буква, буква)
            говори(f"{bg_letter}) {текст}")

def получи_отговор(отговори):
    while True:
        избор = input("Вашият отговор (A, B, C или D): ").strip().upper()
        if избор in отговори:
            return избор
        print("Невалиден избор. Моля изберете A, B, C или D.")

def стартирай_игра():
    global USE_TTS
    USE_TTS = check_internet()
    
    os.system('cls' if os.name == 'nt' else 'clear')
    print("\nДОБРЕ ДОШЛИ В СТАНИ БОГАТ!")
    
    if USE_TTS:
        говори("Добре дошли на стола на богатството!")
    else:
        print("Режим без интернет връзка - звуковите ефекти са деактивирани")

    time.sleep(1)

    въпроси = предварителни_въпроси()

    защитено_ниво = None
    помощници = ПОМОЩНИЦИ.copy()

    for индекс, въпрос in enumerate(въпроси):
        текуща_награда = въпрос['награда']
        трудност = НИВА_НА_ТРУДНОСТ[текуща_награда]
        отговори = въпрос['отговори'].copy()
        initial_display = True

        while True:
            display_question(въпрос, текуща_награда, отговори, speak=initial_display)
            initial_display = False

            user_input = input("\nВъведете A,B,C или D (или натиснете Enter за да изберете жокер): ").strip().upper()

            if user_input in отговори:
                избор = user_input
                break
            elif user_input == '' and помощници:
                използвай_помощник(помощници, въпрос['верен'], отговори, трудност)
                display_question(въпрос, текуща_награда, отговори, speak=False)
            else:
                print("Невалиден избор, моля опитайте отново.")
                time.sleep(1)
                display_question(въпрос, текуща_награда, отговори, speak=False)

        if избор == въпрос['верен']:
            print(f"\nВЯРНО! Печелите {текуща_награда}!")
            говори(f"Верен отговор! Печелите {текуща_награда}!")

            if текуща_награда in ЗАЩИТНИ_НИВА:
                защитено_ниво = текуща_награда
                print(f"\nДОСТИГНАХТЕ СИГУРНА СУМА: {защитено_ниво}!")
                говори(f"Достигнахте сигурна сума {защитено_ниво}!")
        else:
            верен_отговор = въпрос['верен']
            bg_letter = LATIN_TO_BG_SPEECH.get(верен_отговор, верен_отговор)
            print(f"\nГРЕШКА! Верен отговор: {въпрос['отговори'][верен_отговор]}")
            говори(f"Съжалявам, верният отговор беше {bg_letter}) {въпрос['отговори'][верен_отговор]}")
            print(f"\nНапуснахте с {защитено_ниво if защитено_ниво else '0 лева'}!")
            говори(f"Напуснахте играта с {защитено_ниво if защитено_ниво else 'нищо'}!")
            return

        time.sleep(2)

    print("\n !!! СПЕЧЕЛИХТЕ ГОЛЯМАТА НАГРАДА ОТ 100 000 ЛЕВА !!!")
    говори("Невероятно! Вие спечелихте 100000 лева!")

if __name__ == "__main__":
    while True:
        стартирай_игра()
        print("\nНатиснете: [Enter] нова игра | [X] нулирай въпроси | [Друг клавиш] изход")
        избор = input().strip().upper()
        
        if избор == 'X':
            USED_QUESTIONS.clear()
            print("\nВсички въпроси са нулирани!")
            говори("Въпросите са изчистени, започваме отначало!")
        elif избор == '':
            continue
        else:
            print("\nБлагодарим за участието! До скоро!")
            говори("Благодарим ви, че играхте! Довиждане!")
            break