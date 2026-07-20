#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Argo14.py – улучшенная версия с более сложными условиями адаптации.
"""

import random
import statistics
import re
from typing import List, Tuple, Optional
import matplotlib.pyplot as plt

# ------------------------------------------------------------------
# Улучшенные утилиты
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

def mutate_tape_slightly(tape: str) -> str:
    """Легкие мутации ленты"""
    if len(tape) <= 3:
        return tape
        
    op = random.choice(['swap', 'del', 'ins'])
    pos = random.randint(0, len(tape) - 2)
    
    if op == 'swap' and len(tape) > 1:
        chars = list(tape)
        chars[pos], chars[pos+1] = chars[pos+1], chars[pos]
        return ''.join(chars)
    elif op == 'del' and len(tape) > 4:
        return tape[:pos] + tape[pos+1:]
    elif op == 'ins' and len(tape) < 25:
        alphabet = "ABCDEFG<>"
        return tape[:pos] + random.choice(alphabet) + tape[pos:]
    
    return tape

def random_paste(frags: List[str]) -> str:
    """Менее успешная склейка фрагментов с мутациями."""
    if not frags:
        return ""
    
    first = frags[0]
    rest = frags[1:]
    random.shuffle(rest)
    
    processed_rest = []
    for frag in rest:
        # Увеличим вероятность инверсии
        if random.random() < 0.3 and len(frag) > 1:
            processed_rest.append(frag[::-1])
        else:
            processed_rest.append(frag)
    
    result = first + ''.join(processed_rest)
    
    # Добавим случайные мутации при склейке
    if random.random() < 0.4:
        result = mutate_tape_slightly(result)
    
    return result

# ------------------------------------------------------------------
# Улучшенные агент и машина
# ------------------------------------------------------------------
class Argonaut:
    def __init__(self, tape: str):
        self.tape = tape
        self.accept_count = 0
        self.generation = 0

    def run(self, w: str, env: str) -> Tuple[str, str]:
        """Улучшенный алгоритм с более сложными условиями успеха."""
        # 1. Найти вхождения оракульного слова
        matches = find_matches(w, self.tape)
        
        # 2. Условие: хотя бы 1 вхождение
        if len(matches) < 1:
            return "reject", self.tape

        # 3. Разрезать ленту в позициях совпадения
        frags = []
        last_idx = 0
        
        for match_start in matches:
            frags.append(self.tape[last_idx:match_start])
            last_idx = match_start
        
        frags.append(self.tape[last_idx:])

        # 4. Произвольно склеить фрагменты
        new_tape = random_paste(frags)
        
        # 5. Ограничение длины ленты
        if len(new_tape) > 35:
            new_tape = new_tape[:35]
        
        # 6. БОЛЕЕ СЛОЖНЫЕ УСЛОВИЯ УСПЕХА
        success = self._check_strict_success(new_tape, env, w)
        
        if success:
            self.generation += 1
            return "accept", new_tape
        else:
            return "loop", new_tape

    def _check_strict_success(self, tape: str, env: str, oracle: str) -> bool:
        """Проверяет более строгие условия успеха."""
        
        # Условие 1: точное соответствие среды (только для простых сред)
        if len(env) <= 2 and env in tape:
            return True
            
        # Условие 2: первый символ + минимальная длина
        if (len(env) > 0 and len(tape) > 3 and 
            tape[0] == env[0] and len(tape) >= len(env)):
            return True
            
        # Условие 3: структурные требования должны быть строже
        if env == "STRUCT" and self._check_structure(tape):
            return tape.count('<') >= 2 and tape.count('>') >= 2
            
        if env == "BALANCED" and self._check_structure(tape):
            return tape.count('<') == tape.count('>') and tape.count('<') >= 2
            
        # Условие 4: паттерны должны быть сложнее
        patterns = {
            "ABC_ORDER": any(pattern in tape for pattern in ["ABC", "BCD", "CDE", "DEF"]),
            "BRACKET_PAIRS": len(re.findall(r'<[A-G]>', tape)) >= 2,
            "ALTERNATING": len(re.findall(r'[A-G]<[A-G]>', tape)) >= 1,
            "SEQUENTIAL": sum(1 for sub in ["AB", "BC", "CD", "DE", "EF"] if sub in tape) >= 2,
            "SYMMETRY": tape.count('<') > 0 or tape.count('>') > 0,
        }
        
        if env in patterns and patterns[env]:
            return True
            
        # Условие 5: оракульные условия должны быть строже
        oracle_count = tape.count(oracle)
        if env == "ORACLE_START" and tape.startswith(oracle) and len(tape) > len(oracle):
            return True
        elif env == "ORACLE_END" and tape.endswith(oracle) and len(tape) > len(oracle):
            return True
        elif env == "ORACLE_PAIRS" and oracle_count >= 2:
            return True
        elif env == "ORACLE_MANY" and oracle_count >= 3:
            return True
            
        # Условие 6: разнообразие должно быть настоящим
        if env == "COMPLEX" and len(set(tape)) >= 5 and len(tape) >= 8:
            return True
        elif env == "DIVERSE" and len(set(tape)) >= 4 and len(tape) >= 10:
            return True
            
        # Условие 7: для сложных комбинаций
        if env == "ABC" and "ABC" in tape:
            return True
        elif env == "A<B>C" and "A<B>C" in tape:
            return True
            
        return False

    def _check_structure(self, tape: str) -> bool:
        """Проверяет структурные условия."""
        # Наличие скобок
        has_brackets = '<' in tape and '>' in tape
        return has_brackets

    def _check_patterns(self, tape: str, env: str) -> bool:
        """Проверяет достижимые паттерны."""
        patterns = {
            "ABC_ORDER": 'A' in tape and 'B' in tape,
            "BRACKET_PAIRS": len(re.findall(r'<[A-G]', tape)) >= 1,
            "ALTERNATING": len(re.findall(r'[A-G][<>]', tape)) >= 1,
            "SEQUENTIAL": any(sub in tape for sub in ["AB", "BC", "CD", "DE", "EF"]),
            "SYMMETRY": tape.count('<') > 0 or tape.count('>') > 0,
        }
        return patterns.get(env, False)

    def _check_oracle_conditions(self, tape: str, oracle: str, env: str) -> bool:
        """Проверяет условия, связанные с оракулом."""
        oracle_count = tape.count(oracle)
        
        if env == "ORACLE_START" and tape.startswith(oracle):
            return True
        elif env == "ORACLE_END" and tape.endswith(oracle):
            return True
        elif env == "ORACLE_PAIRS" and oracle_count >= 1:
            return True
        elif env == "ORACLE_MANY" and oracle_count >= 2:
            return True
            
        return False

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
        """Транспозиция с улучшенным разнообразием."""
        if self.last_winner is not None:
            winning_tape = self.last_winner.tape
            for ag in self.agents:
                if random.random() < 0.9:  # 90% получают точную копию
                    ag.tape = winning_tape
                else:  # 10% получают мутированную версию
                    ag.tape = self._mutate_tape(winning_tape)
    
    def _mutate_tape(self, tape: str) -> str:
        """Добавляет случайные мутации в ленту."""
        if len(tape) <= 1:
            return tape
            
        op = random.choice(['ins', 'del'])
        alphabet = "ABCDEFG<>"
        
        if op == 'ins' and len(tape) < 30:
            pos = random.randint(0, len(tape))
            return tape[:pos] + random.choice(alphabet) + tape[pos:]
        elif op == 'del' and len(tape) > 5:
            pos = random.randint(0, len(tape) - 1)
            return tape[:pos] + tape[pos+1:]
        
        return tape

# ------------------------------------------------------------------
# Улучшенная эволюция оракула и среды
# ------------------------------------------------------------------
def mutate_oracle(w: str) -> str:
    """Мутирует оракульное слово."""
    if len(w) == 0:
        return "A"  # Минимальный оракул
    
    op = random.choice(['ins', 'del', 'chg'])
    alphabet = "ABCDEFG<>"
    
    if op == 'ins' and len(w) < 3:
        pos = random.randint(0, len(w))
        return w[:pos] + random.choice(alphabet) + w[pos:]
    elif op == 'del' and len(w) > 1:
        pos = random.randint(0, len(w) - 1)
        return w[:pos] + w[pos+1:]
    else:  # chg
        pos = random.randint(0, len(w) - 1)
        return w[:pos] + random.choice(alphabet) + w[pos+1:]

def create_improved_environment() -> str:
    """Создает более сложные среды"""
    env_types = [
        # Простые среды (30%) 
        "A", "B", "C", 
        
        # Средней сложности (40%)
        "AB", "BC", "CD", "A<", "B>", "STRUCT", "BALANCED",
        
        # Сложные среды (30%)
        "ABC_ORDER", "BRACKET_PAIRS", "ALTERNATING", "SEQUENTIAL",
        "ORACLE_START", "ORACLE_END", "ORACLE_PAIRS", "ORACLE_MANY",
        "COMPLEX", "DIVERSE", "ABC", "A<B>C"
    ]
    
    return random.choice(env_types)

# ------------------------------------------------------------------
# Улучшенный запуск эволюции
# ------------------------------------------------------------------
if __name__ == "__main__":
    # Стартовая лента
    START_TAPE = "A<B>C<D>E<F>G"
    
    print(f"Стартовая лента: '{START_TAPE}'")
    print("УЛУЧШЕННАЯ ВЕРСИЯ - более сложные условия адаптации")
    print("=" * 70)

    NUM_AGENTS = 30  # Больше агентов
    oracle = "B"  # Простой начальный oracle
    machine = ArgoMachine([Argonaut(START_TAPE) for _ in range(NUM_AGENTS)])

    print(f"\nНачало эволюции с {NUM_AGENTS} агентами")
    print(f"Начальный oracle: '{oracle}'")
    print("=" * 70)

    adapt_history = []
    success_count = 0
    oracle_history = [oracle]
    
    for epoch in range(30):
        env = create_improved_environment()
        print(f"Эпоха {epoch+1:2d}: oracle='{oracle}' env='{env}'", end=" ")

        # Транспозиция перед эпохой (кроме первой)
        if epoch > 0 and machine.last_winner is not None:
            machine.transpose()
            print("[ТРАНСПОЗИЦИЯ] ", end="")

        # Поиск адаптации с увеличенным лимитом шагов
        max_steps = 100  # Увеличили лимит шагов
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

        # Катастрофа: меняем oracle (реже)
        if random.random() < 0.4:  # 40% chance to mutate
            old_oracle = oracle
            oracle = mutate_oracle(oracle)
            oracle_history.append(oracle)
            if old_oracle != oracle:
                print(f"                КАТАСТРОФА: '{old_oracle}' → '{oracle}'")

    # Фаза 2: сбор статистики
    print(f"\n" + "="*70)
    print("СБОР СТАТИСТИКИ (50 эпох)")
    print("="*70)
    
    adapt_steps = []
    
    for epoch in range(50):
        env = create_improved_environment()
        
        # Транспозиция перед каждой эпохой
        if epoch > 0 and machine.last_winner is not None:
            machine.transpose()

        # Поиск адаптации
        for step in range(100):  # Увеличили лимит шагов
            res = machine.step(oracle, env)
            if res == "accept":
                adapt_steps.append(step + 1)
                break
        else:
            adapt_steps.append(100)

    # Статистика с исправлением ошибок
    print("\n" + "="*70)
    print("РЕЗУЛЬТАТЫ УЛУЧШЕННОЙ ВЕРСИИ")
    print("="*70)
    
    successful_epochs = [s for s in adapt_history if s < 100]
    successful_stats = [s for s in adapt_steps if s < 100]

    print(f"Фаза 1 (30 эпох):")
    print(f"  Успешные адаптации: {len(successful_epochs)} из 30")
    if successful_epochs:
        print(f"  Среднее время: {statistics.mean(successful_epochs):.1f} шагов")
        print(f"  Медиана: {statistics.median(successful_epochs)} шагов")
        if len(successful_epochs) > 1:
            print(f"  Стандартное отклонение: {statistics.stdev(successful_epochs):.1f} шагов")
        print(f"  Лучший результат: {min(successful_epochs)} шагов")
        print(f"  Худший успешный: {max(successful_epochs)} шагов")

    print(f"\nФаза 2 (50 эпох):")
    print(f"  Успешные адаптации: {len(successful_stats)} из 50")
    if successful_stats:
        print(f"  Среднее время: {statistics.mean(successful_stats):.1f} шагов")
        print(f"  Медиана: {statistics.median(successful_stats)} шагов")
        if len(successful_stats) > 1:
            print(f"  Стандартное отклонение: {statistics.stdev(successful_stats):.1f} шагов")

    # Графика
    plt.style.use('default')

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))

    # График 1: История адаптации
    colors = ['#2E8B57' if s < 100 else '#DC143C' for s in adapt_history]
    ax1.bar(range(1, 31), adapt_history, color=colors, alpha=0.8, edgecolor='black')
    ax1.axhline(y=100, color='red', linestyle='--', alpha=0.7, label='Лимит шагов')
    ax1.set_xlabel('Эпоха')
    ax1.set_ylabel('Шаги до адаптации')
    ax1.set_title('История адаптации (30 эпох обучения)', fontweight='bold')
    ax1.legend(loc='upper right', bbox_to_anchor=(1, 1))
    ax1.grid(alpha=0.3)

    # График 2: Распределение успешных адаптаций
    if successful_stats:
        ax2.hist(successful_stats, bins=15, color='#4682B4', 
                edgecolor='black', alpha=0.8)
        ax2.set_xlabel('Шаги до адаптации')
        ax2.set_ylabel('Количество случаев')
        ax2.set_title(f'Распределение ({len(successful_stats)} из 50 эпох)', fontweight='bold')
        ax2.grid(alpha=0.3, axis='y')
    
        if len(successful_stats) > 1:
            mean_val = statistics.mean(successful_stats)
            median_val = statistics.median(successful_stats)
            ax2.axvline(mean_val, color='red', linestyle='--', linewidth=2, 
                       label=f'Среднее: {mean_val:.1f}')
            ax2.axvline(median_val, color='orange', linestyle='-.', linewidth=2,
                       label=f'Медиана: {median_val}')
            ax2.legend(loc='upper right', bbox_to_anchor=(1, 1))
    else:
        ax2.text(0.5, 0.5, 'Нет успешных адаптаций', 
                ha='center', va='center', transform=ax2.transAxes, fontsize=12)
        ax2.set_title('Распределение успешных адаптаций', fontweight='bold')

    # График 3: Эволюция времени адаптации
    ax3.plot(range(1, 51), adapt_steps, linewidth=2, color='#8A2BE2', 
            marker='o', markersize=3, alpha=0.7)
    ax3.set_xlabel('Эпоха')
    ax3.set_ylabel('Шаги до адаптации')
    ax3.set_title('Эволюция времени адаптации (50 эпох)', fontweight='bold')
    ax3.grid(alpha=0.3)
    ax3.set_ylim(bottom=0)

    # График 4: Эволюция оракула
    ax4.plot(range(len(oracle_history)), [len(o) for o in oracle_history], 
            linewidth=2, color='#FF4500', marker='s', markersize=4)
    ax4.set_xlabel('Катастрофа')
    ax4.set_ylabel('Длина оракула')
    ax4.set_title('Эволюция сложности оракула', fontweight='bold')
    ax4.grid(alpha=0.3)

    # Увеличенные отступы между графиками
    plt.tight_layout(pad=4.0, h_pad=4.0, w_pad=3.0)
    plt.savefig('argo_improved_results.png', dpi=200, bbox_inches='tight')
    plt.show()

    # Детальная информация
    print(f"\nДЕТАЛЬНАЯ ИНФОРМАЦИЯ:")
    print(f"Всего успешных адаптаций за весь прогон: {success_count}")
    
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
    
    if machine.last_winner:
        print(f"\nПоследний победитель: {machine.last_winner.accept_count} побед")
        print(f"Его лента: '{machine.last_winner.tape}'")

    print(f"\nГрафики сохранены: argo_improved_results.png")
