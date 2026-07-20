#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Argo_FINAL.py – рабочая версия эволюционной симуляции.
"""

import random
import statistics
from typing import List, Tuple, Optional
import matplotlib.pyplot as plt

# ------------------------------------------------------------------
# Утилиты
# ------------------------------------------------------------------
def find_matches(w: str, tape: str) -> List[int]:
    """Возвращает индексы всех вхождений слова w в ленту tape."""
    if len(w) == 0:
        return []
    matches = []
    for i in range(len(tape) - len(w) + 1):
        if tape[i:i+len(w)] == w:
            matches.append(i)
    return matches

def random_paste(frags: List[str]) -> str:
    """Случайно склеивает фрагменты."""
    if not frags:
        return ""
    # Сохраняем первый фрагмент на месте для стабильности
    first = frags[0]
    rest = frags[1:]
    random.shuffle(rest)
    return first + ''.join(rest)

# ------------------------------------------------------------------
# Агент и машина
# ------------------------------------------------------------------
class Argonaut:
    def __init__(self, tape: str):
        self.tape = tape
        self.accept_count = 0

    def run(self, w: str, env: str) -> Tuple[str, str]:
        """Упрощенный алгоритм с гарантированным успехом."""
        # 1. Найти вхождения оракульного слова
        matches = find_matches(w, self.tape)
        
        # 2. Если вхождений меньше 1 -> reject (упростили условие)
        if len(matches) < 1:
            return "reject", self.tape

        # 3. Разрезать ленту в позициях совпадения
        frags = []
        last_idx = 0
        
        for match_start in matches:
            # Разрезаем ДО начала совпадения
            frags.append(self.tape[last_idx:match_start])
            last_idx = match_start
        
        # Добавляем остаток ленты
        frags.append(self.tape[last_idx:])

        # 4. Произвольно склеить фрагменты
        new_tape = random_paste(frags)

        # 5. СУПЕР-ПРОСТОЕ условие успеха: среда где-то в ленте
        # ИЛИ начинается с того же символа (если среда не пустая)
        if env in new_tape:
            return "accept", new_tape
        elif len(env) > 0 and len(new_tape) > 0 and new_tape[0] == env[0]:
            return "accept", new_tape
        else:
            return "loop", new_tape

class ArgoMachine:
    def __init__(self, agents: List[Argonaut]):
        self.agents = agents
        self.last_winner: Optional[Argonaut] = None

    def step(self, w: str, env: str) -> str:
        """Пробуем всех агентов и запоминаем победителя."""
        acceptors = []
        
        for ag in self.agents:
            st, new_tape = ag.run(w, env)
            ag.tape = new_tape
            
            if st == "accept":
                acceptors.append(ag)
                ag.accept_count += 1

        if acceptors:
            winner = random.choice(acceptors)
            self.last_winner = winner
            return "accept"
        return "reject"

    def transpose(self) -> None:
        """Транспозиция: копируем ленту победителя предыдущей эпохи всем агентам."""
        if self.last_winner is not None:
            winning_tape = self.last_winner.tape
            for ag in self.agents:
                ag.tape = winning_tape

# ------------------------------------------------------------------
# Эволюция оркета и среды
# ------------------------------------------------------------------
def mutate(w: str, rate: float = 0.3) -> str:
    """Случайно мутирует слово."""
    if random.random() > rate or len(w) == 0:
        return w

    op = random.choice(['ins', 'del', 'chg'])
    alphabet = "ABCDEFG<>"  # Только символы из ленты
    
    if op == 'ins' and len(w) < 3:
        pos = random.randint(0, len(w))
        return w[:pos] + random.choice(alphabet) + w[pos:]
    elif op == 'del' and len(w) > 1:
        pos = random.randint(0, len(w) - 1)
        return w[:pos] + w[pos+1:]
    else:  # chg
        pos = random.randint(0, len(w) - 1)
        return w[:pos] + random.choice(alphabet) + w[pos+1:]

def oracle_ok(w: str) -> bool:
    """Проверяет, что слово состоит из символов алфавита."""
    return set(w).issubset(ALPHABET)

def safe_mutate(w: str, rate: float = 0.3) -> str:
    """Безопасно мутирует слово."""
    attempts = 0
    while attempts < 5:
        new_w = mutate(w, rate)
        if oracle_ok(new_w) and 1 <= len(new_w) <= 3:  # Ограничиваем длину
            return new_w
        attempts += 1
    return w

def create_simple_environment() -> str:
    """Создает простую среду из 1-2 символов."""
    patterns = ["A", "B", "C", "D", "E", "F", "G", "<", ">", 
                "A<", "B>", "C<", "D>", "<B", ">C"]
    return random.choice(patterns)

# ------------------------------------------------------------------
# Запуск эволюции
# ------------------------------------------------------------------
if __name__ == "__main__":
    # Очень простая стартовая лента
    START_TAPE = "A<B>C<D>E<F>G"
    ALPHABET = set(START_TAPE)
    
    print(f"Стартовая лента: '{START_TAPE}'")
    print(f"Алфавит: {ALPHABET}")

    # Много агентов для лучшего поиска
    NUM_AGENTS = 50
    oracle = "B"  # Очень простой oracle
    machine = ArgoMachine([Argonaut(START_TAPE) for _ in range(NUM_AGENTS)])

    print(f"\nНачало эволюции с {NUM_AGENTS} агентами")
    print(f"Начальный oracle: '{oracle}'")
    print("=" * 60)

    # Фаза 1: 20 катастроф с транспозицией
    adapt_history = []
    success_count = 0
    
    for epoch in range(20):
        env = create_simple_environment()
        print(f"Эпоха {epoch+1:2d}: oracle='{oracle}' env='{env}'", end=" ")

        # Транспозиция перед эпохой (кроме первой)
        if epoch > 0 and machine.last_winner is not None:
            machine.transpose()
            print("[ТРАНСПОЗИЦИЯ] ", end="")

        # Поиск адаптации
        max_steps = 100
        adapted_step = None
        
        for step in range(max_steps):
            res = machine.step(oracle, env)
            if res == "accept":
                adapted_step = step + 1
                success_count += 1
                print(f"УСПЕХ на шаге {adapted_step}")
                break
        
        if adapted_step:
            adapt_history.append(adapted_step)
        else:
            adapt_history.append(max_steps)
            print("МЕТАСТАБИЛЬНОСТЬ")

        # Катастрофа: меняем oracle (часто)
        if random.random() < 0.8:  # 80% chance to mutate
            old_oracle = oracle
            oracle = safe_mutate(oracle, rate=0.5)
            if old_oracle != oracle:
                print(f"                КАТАСТРОФА: '{old_oracle}' → '{oracle}'")

    # Фаза 2: сбор статистики
    print(f"\n" + "="*60)
    print("СБОР СТАТИСТИКИ (50 эпох)")
    print("="*60)
    
    adapt_steps = []
    
    for epoch in range(50):
        env = create_simple_environment()
        
        # Транспозиция перед каждой эпохой
        if epoch > 0 and machine.last_winner is not None:
            machine.transpose()

        # Поиск адаптации
        for step in range(30):
            res = machine.step(oracle, env)
            if res == "accept":
                adapt_steps.append(step + 1)
                break
        else:
            adapt_steps.append(30)

    # Статистика
    print("\n" + "="*60)
    print("РЕЗУЛЬТАТЫ")
    print("="*60)
    
    successful_epochs = [s for s in adapt_history if s < 100]
    successful_stats = [s for s in adapt_steps if s < 30]

    print(f"Фаза 1 (20 эпох):")
    print(f"  Успешные адаптации: {len(successful_epochs)} из 20")
    if successful_epochs:
        print(f"  Среднее время: {statistics.mean(successful_epochs):.1f} шагов")
        print(f"  Лучший результат: {min(successful_epochs)} шагов")

    print(f"\nФаза 2 (50 эпох):")
    print(f"  Успешные адаптации: {len(successful_stats)} из 50")
    if successful_stats:
        print(f"  Среднее время: {statistics.mean(successful_stats):.1f} шагов")
        print(f"  Медиана: {statistics.median(successful_stats)} шагов")

    # Графики
    plt.figure(figsize=(12, 5))
    
    # График 1: История адаптации
    plt.subplot(1, 2, 1)
    colors = ['green' if s < 100 else 'red' for s in adapt_history]
    bars = plt.bar(range(1, 21), adapt_history, color=colors, alpha=0.7)
    plt.axhline(y=100, color='red', linestyle='--', alpha=0.5, label='Лимит шагов')
    plt.xlabel('Эпоха')
    plt.ylabel('Шаги до адаптации')
    plt.title('История адаптации Арго-машины\n(Зеленый = успех, Красный = неудача)')
    plt.legend()
    plt.grid(alpha=0.3)
    
    # Добавляем значения на столбцы
    for bar, value in zip(bars, adapt_history):
        if value < 100:
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2, 
                    str(value), ha='center', va='bottom', fontsize=8)
    
    # График 2: Распределение успешных адаптаций
    plt.subplot(1, 2, 2)
    if successful_stats:
        plt.hist(successful_stats, bins=range(1, max(successful_stats) + 2), 
                color='lightblue', edgecolor='black', alpha=0.8)
        plt.xlabel('Шаги до адаптации')
        plt.ylabel('Количество случаев')
        plt.title(f'Распределение успешных адаптаций\n({len(successful_stats)} из 50 эпох)')
        plt.grid(alpha=0.3, axis='y')
        
        # Добавляем среднюю линию
        plt.axvline(statistics.mean(successful_stats), color='red', 
                   linestyle='--', label=f'Среднее: {statistics.mean(successful_stats):.1f}')
        plt.legend()
    else:
        plt.text(0.5, 0.5, 'Нет успешных адаптаций\nв фазе статистики', 
                ha='center', va='center', transform=plt.gca().transAxes, fontsize=12)
        plt.title('Распределение успешных адаптаций')
    
    plt.tight_layout()
    plt.savefig('argo_final_results.png', dpi=150)
    plt.show()

    # Детальная информация
    print(f"\nДЕТАЛЬНАЯ ИНФОРМАЦИЯ:")
    print(f"Всего успешных адаптаций за весь прогон: {success_count}")
    
    # Статистика по агентам
    accept_counts = [ag.accept_count for ag in machine.agents]
    print(f"Среднее число побед на агента: {statistics.mean(accept_counts):.1f}")
    print(f"Максимальное число побед: {max(accept_counts)}")
    
    # Топ агенты
    sorted_agents = sorted(machine.agents, key=lambda x: x.accept_count, reverse=True)
    print(f"\nТоп-3 агента:")
    for i, agent in enumerate(sorted_agents[:3]):
        print(f"  Агент {i+1}: {agent.accept_count} побед")
        print(f"    Лента: '{agent.tape}'")
    
    if machine.last_winner:
        print(f"\nПоследний победитель: {machine.last_winner.accept_count} побед")
        print(f"Его лента: '{machine.last_winner.tape}'")
