#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Argo10.py – усложненная версия эволюционной симуляции с реалистичными условиями адаптации.
Соответствует теоретическим принципам из Argo.pdf
"""

import random
import statistics
import re
from typing import List, Tuple, Optional
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# ------------------------------------------------------------------
# Усложненные утилиты
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
    """Случайно склеивает фрагменты с возможностью инверсии."""
    if not frags:
        return ""
    
    # Сохраняем первый фрагмент на месте для стабильности
    first = frags[0]
    rest = frags[1:]
    random.shuffle(rest)
    
    # Добавляем случайные инверсии (соответствует теории из Argo.pdf)
    processed_rest = []
    for frag in rest:
        if random.random() < 0.3 and len(frag) > 1:  # 30% chance to invert
            processed_rest.append(frag[::-1])
        else:
            processed_rest.append(frag)
    
    return first + ''.join(processed_rest)

# ------------------------------------------------------------------
# Усложненные агент и машина
# ------------------------------------------------------------------
class Argonaut:
    def __init__(self, tape: str):
        self.tape = tape
        self.accept_count = 0
        self.generation = 0  # Отслеживаем поколение агента

    def run(self, w: str, env: str) -> Tuple[str, str]:
        """Усложненный алгоритм с нетривиальными условиями успеха."""
        # 1. Найти вхождения оракульного слова
        matches = find_matches(w, self.tape)
        
        # 2. Если вхождений меньше 2 -> reject (соответствует теории)
        if len(matches) < 2:
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

        # 4. Произвольно склеить фрагменты (возможно с инверсией)
        new_tape = random_paste(frags)
        
        # 5. Ограничение длины ленты (предотвращает бесконечный рост)
        if len(new_tape) > 50:
            new_tape = new_tape[:50]
        
        # 6. УСЛОЖНЕННЫЕ УСЛОВИЯ УСПЕХА (соответствуют теории)
        success = self._check_complex_success(new_tape, env, w)
        
        if success:
            self.generation += 1
            return "accept", new_tape
        else:
            return "loop", new_tape

    def _check_complex_success(self, tape: str, env: str, oracle: str) -> bool:
        """Проверяет сложные условия успеха, соответствующие теории Argo."""
        
        # Условие 1: Структурное соответствие - сбалансированные скобки
        if self._check_balanced_structure(tape) and env in ["STRUCT", "BALANCED"]:
            return True
            
        # Условие 2: Паттерн последовательности - определенный порядок символов
        if self._check_sequence_pattern(tape, env):
            return True
            
        # Условие 3: Оракульная зависимость - успех зависит от самого оракула
        if self._check_oracle_dependency(tape, oracle, env):
            return True
            
        # Условие 4: Статистическая сложность - разнообразие символов
        if len(set(tape)) >= 6 and env in ["COMPLEX", "DIVERSE"]:
            return True
            
        # Условие 5: Простое вхождение (резервное условие, но с ограничениями)
        if env in tape and len(env) >= 3:  # Только для сред длиной >= 3
            return True
            
        return False

    def _check_balanced_structure(self, tape: str) -> bool:
        """Проверяет сбалансированность структурных элементов."""
        open_count = tape.count('<')
        close_count = tape.count('>')
        return open_count == close_count and open_count > 0

    def _check_sequence_pattern(self, tape: str, env: str) -> bool:
        """Проверяет сложные паттерны последовательностей."""
        patterns = {
            "ABC_ORDER": re.search(r'A.*B.*C', tape) is not None,
            "BRACKET_PAIRS": len(re.findall(r'<[A-Z]>', tape)) >= 2,
            "ALTERNATING": len(re.findall(r'[A-Z]<[A-Z]>[A-Z]', tape)) >= 1,
        }
        return patterns.get(env, False)

    def _check_oracle_dependency(self, tape: str, oracle: str, env: str) -> bool:
        """Проверяет условия, зависящие от оракульного слова."""
        # Успех, если лента содержит оракул в определенном контексте
        oracle_pos = tape.find(oracle)
        if oracle_pos == -1:
            return False
            
        # Разные условия для разных сред
        if env == "ORACLE_START" and oracle_pos == 0:
            return True
        elif env == "ORACLE_MIDDLE" and 0 < oracle_pos < len(tape) - len(oracle):
            return True
        elif env == "ORACLE_PAIRS" and tape.count(oracle) >= 2:
            return True
            
        return False

class ArgoMachine:
    def __init__(self, agents: List[Argonaut]):
        self.agents = agents
        self.last_winner: Optional[Argonaut] = None
        self.epoch_count = 0

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
            # Выбираем наиболее "опытного" агента
            winner = max(acceptors, key=lambda x: x.generation)
            self.last_winner = winner
            return "accept"
        return "reject"

    def transpose(self) -> None:
        """Транспозиция: копируем ленту победителя предыдущей эпохи всем агентам."""
        if self.last_winner is not None:
            winning_tape = self.last_winner.tape
            for ag in self.agents:
                # Сохраняем некоторое разнообразие - не все агенты получают точную копию
                if random.random() < 0.8:  # 80% получают точную копию
                    ag.tape = winning_tape
                else:  # 20% получают мутированную версию
                    ag.tape = self._mutate_tape(winning_tape)
    
    def _mutate_tape(self, tape: str) -> str:
        """Добавляет случайные мутации в ленту для поддержания разнообразия."""
        if len(tape) <= 1:
            return tape
            
        op = random.choice(['ins', 'del', 'swap'])
        alphabet = "ABCDEFG<>"
        
        if op == 'ins' and len(tape) < 40:
            pos = random.randint(0, len(tape))
            return tape[:pos] + random.choice(alphabet) + tape[pos:]
        elif op == 'del' and len(tape) > 10:
            pos = random.randint(0, len(tape) - 1)
            return tape[:pos] + tape[pos+1:]
        else:  # swap
            if len(tape) >= 2:
                pos = random.randint(0, len(tape) - 2)
                return tape[:pos] + tape[pos+1] + tape[pos] + tape[pos+2:]
        
        return tape

# ------------------------------------------------------------------
# Усложненная эволюция оркета и среды
# ------------------------------------------------------------------
def mutate(w: str, rate: float = 0.3) -> str:
    """Случайно мутирует оракульное слово."""
    if random.random() > rate or len(w) == 0:
        return w

    op = random.choice(['ins', 'del', 'chg', 'extend'])
    alphabet = "ABCDEFG<>"
    
    if op == 'ins' and len(w) < 4:
        pos = random.randint(0, len(w))
        return w[:pos] + random.choice(alphabet) + w[pos:]
    elif op == 'del' and len(w) > 1:
        pos = random.randint(0, len(w) - 1)
        return w[:pos] + w[pos+1:]
    elif op == 'extend' and len(w) < 4:
        return w + random.choice(alphabet)
    else:  # chg
        pos = random.randint(0, len(w) - 1)
        return w[:pos] + random.choice(alphabet) + w[pos+1:]

def oracle_ok(w: str) -> bool:
    """Проверяет, что слово состоит из символов алфавита."""
    return set(w).issubset(set("ABCDEFG<>"))

def safe_mutate(w: str, rate: float = 0.3) -> str:
    """Безопасно мутирует слово."""
    attempts = 0
    while attempts < 5:
        new_w = mutate(w, rate)
        if oracle_ok(new_w) and 1 <= len(new_w) <= 4:
            return new_w
        attempts += 1
    return w

def create_complex_environment() -> str:
    """Создает сложные среды с различными типами условий."""
    env_types = [
        # Простые строковые среды (30%)
        "A<B", "C>D", "E<F", "A>B<C", "D<E>F",
        
        # Структурные среды (25%)
        "STRUCT", "BALANCED", "PAIRS", "NESTED",
        
        # Паттерн-ориентированные среды (25%)
        "ABC_ORDER", "BRACKET_PAIRS", "ALTERNATING",
        
        # Оракул-зависимые среды (20%)
        "ORACLE_START", "ORACLE_MIDDLE", "ORACLE_PAIRS",
        
        # Статистические среды (20%)
        "COMPLEX", "DIVERSE", "UNIQUE"
    ]
    
    return random.choice(env_types)

# ------------------------------------------------------------------
# Усложненный запуск эволюции
# ------------------------------------------------------------------
if __name__ == "__main__":
    # Стартовая лента
    START_TAPE = "A<B>C<D>E<F>G"
    ALPHABET = set(START_TAPE)
    
    print(f"Стартовая лента: '{START_TAPE}'")
    print(f"Алфавит: {ALPHABET}")
    print("УСЛОЖНЕННАЯ ВЕРСИЯ - реалистичные условия адаптации")
    print("=" * 70)

    # Меньше агентов для более реалистичной симуляции
    NUM_AGENTS = 20
    oracle = "<B"  # Более сложный начальный oracle
    machine = ArgoMachine([Argonaut(START_TAPE) for _ in range(NUM_AGENTS)])

    print(f"\nНачало эволюции с {NUM_AGENTS} агентами")
    print(f"Начальный oracle: '{oracle}'")
    print("=" * 70)

    adapt_history = []
    success_count = 0
    oracle_history = [oracle]
    
    for epoch in range(30):  # Увеличили число эпох
        env = create_complex_environment()
        print(f"Эпоха {epoch+1:2d}: oracle='{oracle}' env='{env}'", end=" ")

        # Транспозиция перед эпохой (кроме первой)
        if epoch > 0 and machine.last_winner is not None:
            machine.transpose()
            print("[ТРАНСПОЗИЦИЯ] ", end="")

        # Поиск адаптации с увеличенным лимитом шагов
        max_steps = 200
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

        # Катастрофа: меняем oracle (реже, но с большими изменениями)
        if random.random() < 0.6:  # 60% chance to mutate
            old_oracle = oracle
            oracle = safe_mutate(oracle, rate=0.6)  # Более агрессивные мутации
            oracle_history.append(oracle)
            if old_oracle != oracle:
                print(f"                КАТАСТРОФА: '{old_oracle}' → '{oracle}'")

    # Фаза 2: сбор статистики с усложненными условиями
    print(f"\n" + "="*70)
    print("СБОР СТАТИСТИКИ (50 эпох)")
    print("="*70)
    
    adapt_steps = []
    
    for epoch in range(50):
        env = create_complex_environment()
        
        # Транспозиция перед каждой эпохой
        if epoch > 0 and machine.last_winner is not None:
            machine.transpose()

        # Поиск адаптации
        for step in range(50):  # Увеличили лимит шагов
            res = machine.step(oracle, env)
            if res == "accept":
                adapt_steps.append(step + 1)
                break
        else:
            adapt_steps.append(50)

    # Статистика
    print("\n" + "="*70)
    print("РЕЗУЛЬТАТЫ УСЛОЖНЕННОЙ ВЕРСИИ")
    print("="*70)
    
    successful_epochs = [s for s in adapt_history if s < 200]
    successful_stats = [s for s in adapt_steps if s < 50]

    print(f"Фаза 1 (30 эпох):")
    print(f"  Успешные адаптации: {len(successful_epochs)} из 30")
    if successful_epochs:
        print(f"  Среднее время: {statistics.mean(successful_epochs):.1f} шагов")
        print(f"  Медиана: {statistics.median(successful_epochs):.1f} шагов")
        print(f"  Стандартное отклонение: {statistics.stdev(successful_epochs):.1f} шагов")
        print(f"  Лучший результат: {min(successful_epochs)} шагов")
        print(f"  Худший успешный: {max(successful_epochs)} шагов")

    print(f"\nФаза 2 (50 эпох):")
    print(f"  Успешные адаптации: {len(successful_stats)} из 50")
    if successful_stats:
        print(f"  Среднее время: {statistics.mean(successful_stats):.1f} шагов")
        print(f"  Медиана: {statistics.median(successful_stats)} шагов")
        print(f"  Стандартное отклонение: {statistics.stdev(successful_stats):.1f} шагов")

    # УЛУЧШЕННАЯ ГРАФИКА С РЕАЛИСТИЧНЫМИ ДАННЫМИ
    plt.style.use('seaborn-v0_8')
    
    # 1. Комплексный график результатов
    fig_complex = plt.figure(figsize=(15, 10))
    
    # График 1: История адаптации (30 эпох)
    ax1 = plt.subplot(2, 2, 1)
    colors = ['#2E8B57' if s < 200 else '#DC143C' for s in adapt_history]
    bars = ax1.bar(range(1, 31), adapt_history, color=colors, alpha=0.8, edgecolor='black')
    ax1.axhline(y=200, color='red', linestyle='--', alpha=0.7, label='Лимит шагов (200)')
    ax1.set_xlabel('Эпоха')
    ax1.set_ylabel('Шаги до адаптации')
    ax1.set_title('История адаптации Арго-машины\n(30 эпох обучения, усложненные условия)', fontweight='bold')
    ax1.legend()
    ax1.grid(alpha=0.3)
    
    # График 2: Распределение успешных адаптаций (50 эпох)
    ax2 = plt.subplot(2, 2, 2)
    if successful_stats:
        n, bins, patches = ax2.hist(successful_stats, bins=15, 
                                   color='#4682B4', edgecolor='black', alpha=0.8)
        ax2.set_xlabel('Шаги до адаптации')
        ax2.set_ylabel('Количество случаев')
        ax2.set_title(f'Распределение успешных адаптаций\n({len(successful_stats)} из 50 эпох)', fontweight='bold')
        ax2.grid(alpha=0.3, axis='y')
        
        # Статистические линии
        mean_val = statistics.mean(successful_stats)
        median_val = statistics.median(successful_stats)
        ax2.axvline(mean_val, color='red', linestyle='--', linewidth=2, 
                   label=f'Среднее: {mean_val:.1f}')
        ax2.axvline(median_val, color='orange', linestyle='-.', linewidth=2,
                   label=f'Медиана: {median_val}')
        ax2.legend()
    else:
        ax2.text(0.5, 0.5, 'Нет успешных адаптаций\nв фазе статистики', 
                ha='center', va='center', transform=ax2.transAxes, fontsize=12)
        ax2.set_title('Распределение успешных адаптаций', fontweight='bold')

    # График 3: Эволюция времени адаптации (50 эпох)
    ax3 = plt.subplot(2, 2, 3)
    ax3.plot(range(1, 51), adapt_steps, linewidth=2, color='#8A2BE2', marker='o', 
            markersize=3, alpha=0.7)
    ax3.set_xlabel('Эпоха')
    ax3.set_ylabel('Шаги до адаптации')
    ax3.set_title('Эволюция времени адаптации\n(50 эпох тестирования)', fontweight='bold')
    ax3.grid(alpha=0.3)
    ax3.set_ylim(bottom=0)

    # График 4: Эволюция оракула
    ax4 = plt.subplot(2, 2, 4)
    oracle_lengths = [len(o) for o in oracle_history]
    ax4.plot(range(len(oracle_history)), oracle_lengths, linewidth=2, color='#FF4500')
    ax4.set_xlabel('Катастрофа (изменение оракула)')
    ax4.set_ylabel('Длина оракула')
    ax4.set_title('Эволюция сложности оракула', fontweight='bold')
    ax4.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig('argo_complex_results.png', dpi=200, bbox_inches='tight')
    plt.show()

    # Детальная информация
    print(f"\nДЕТАЛЬНАЯ ИНФОРМАЦИЯ:")
    print(f"Всего успешных адаптаций за весь прогон: {success_count}")
    
    # Статистика по агентам
    accept_counts = [ag.accept_count for ag in machine.agents]
    generations = [ag.generation for ag in machine.agents]
    
    print(f"Среднее число побед на агента: {statistics.mean(accept_counts):.1f}")
    print(f"Максимальное число побед: {max(accept_counts)}")
    print(f"Среднее поколение агентов: {statistics.mean(generations):.1f}")
    
    # Топ агенты
    sorted_agents = sorted(machine.agents, key=lambda x: x.accept_count, reverse=True)
    print(f"\nТоп-3 агента:")
    for i, agent in enumerate(sorted_agents[:3]):
        print(f"  Агент {i+1}: {agent.accept_count} побед, поколение {agent.generation}")
        print(f"    Лента: '{agent.tape}'")
        print(f"    Длина ленты: {len(agent.tape)}, уникальных символов: {len(set(agent.tape))}")
    
    if machine.last_winner:
        print(f"\nПоследний победитель: {machine.last_winner.accept_count} побед")
        print(f"Его лента: '{machine.last_winner.tape}'")
        print(f"Поколение: {machine.last_winner.generation}")

    print(f"\nИстория оракула: {oracle_history}")

    print(f"\nГрафики сохранены:")
    print("  - argo_complex_results.png (комплексный анализ)")
