#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Argo10_final_full.py – полная исправленная версия с фиксированным пулом в Фазе 2
и ограничением роста оракулов.
"""

import random
import statistics
import math
from typing import List, Tuple, Optional
import matplotlib.pyplot as plt

# ------------------------------------------------------------------
# Базовые утилиты
# ------------------------------------------------------------------
def find_matches(w: str, tape: str) -> List[int]:
    if len(w) == 0:
        return []
    matches = []
    for i in range(len(tape) - len(w) + 1):
        if tape[i:i+len(w)] == w:
            matches.append(i)
    return matches

def random_paste(frags: List[str]) -> str:
    if not frags:
        return ""
    first = frags[0]
    rest = frags[1:]
    random.shuffle(rest)
    processed_rest = []
    for frag in rest:
        if random.random() < 0.3 and len(frag) > 1:
            processed_rest.append(frag[::-1])
        else:
            processed_rest.append(frag)
    return first + ''.join(processed_rest)

# ------------------------------------------------------------------
# Семантический вектор
# ------------------------------------------------------------------
def compute_semantic_vector(word: str) -> List[float]:
    if not word:
        return [0.0] * 8
    vowels = set('AEIOU')
    consonants = set('BCDFG')
    structural = set('<>')
    features = []
    features.append(len(word))
    features.append(len(set(word)) / len(word) if len(word) > 0 else 0)
    v_count = sum(1 for c in word if c in vowels)
    c_count = sum(1 for c in word if c in consonants)
    features.append(v_count / (c_count + 1))
    features.append(sum(1 for c in word if c in structural) / len(word))
    features.append(1.0 if word == word[::-1] else 0.0)
    alphabet = "ABCDEFG<>"
    freq = [word.count(c) / len(word) for c in alphabet]
    features.extend(freq)
    return features

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    if not v1 or not v2:
        return 0.0
    if len(v1) < len(v2):
        v1 = v1 + [0.0] * (len(v2) - len(v1))
    elif len(v2) < len(v1):
        v2 = v2 + [0.0] * (len(v1) - len(v2))
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)

# ------------------------------------------------------------------
# Эволюционирующий оракул
# ------------------------------------------------------------------
class EvolutionaryOracle:
    def __init__(self, word: str):
        self.word = word
        self.fitness = 0.5
        self.success_count = 0
        self.usage_count = 0
        self.specialization = ""
        self.generation = 0
        self.semantic_vector = compute_semantic_vector(word)
        self.age = 0

    def update_fitness(self):
        if self.usage_count > 0:
            self.fitness = self.success_count / self.usage_count
        else:
            self.fitness = 0.5

    def increment_usage(self, success: bool):
        self.usage_count += 1
        if success:
            self.success_count += 1
        self.update_fitness()
        self.age += 1

    def get_specialization_bonus(self, env: str) -> float:
        if self.specialization == env:
            return 1.0
        return 0.0

    def __repr__(self):
        return f"Oracle('{self.word}', fitness={self.fitness:.2f}, usage={self.usage_count})"

# ------------------------------------------------------------------
# Мутации и кроссовер оракулов
# ------------------------------------------------------------------
def mutate_oracle(word: str, rate: float = 0.3) -> str:
    if random.random() > rate or len(word) == 0:
        return word
    alphabet = "ABCDEFG<>"
    op = random.choice(['ins', 'del', 'chg', 'extend'])
    if op == 'ins' and len(word) < 5:
        pos = random.randint(0, len(word))
        return word[:pos] + random.choice(alphabet) + word[pos:]
    elif op == 'del' and len(word) > 1:
        pos = random.randint(0, len(word) - 1)
        return word[:pos] + word[pos+1:]
    elif op == 'extend' and len(word) < 5:
        return word + random.choice(alphabet)
    else:
        pos = random.randint(0, len(word) - 1)
        return word[:pos] + random.choice(alphabet) + word[pos+1:]

def crossover_oracles(w1: str, w2: str) -> str:
    if len(w1) < 2 or len(w2) < 2:
        return random.choice([w1, w2])
    pos1 = random.randint(1, len(w1) - 1)
    pos2 = random.randint(1, len(w2) - 1)
    child1 = w1[:pos1] + w2[pos2:]
    child2 = w2[:pos2] + w1[pos1:]
    return random.choice([child1, child2])

def oracle_ok(w: str) -> bool:
    return set(w).issubset(set("ABCDEFG<>")) and 1 <= len(w) <= 5

def safe_mutate_oracle(w: str, rate: float = 0.3) -> str:
    attempts = 0
    while attempts < 10:
        new_w = mutate_oracle(w, rate)
        if oracle_ok(new_w):
            return new_w
        attempts += 1
    return w

def safe_crossover_oracles(w1: str, w2: str) -> str:
    attempts = 0
    while attempts < 10:
        new_w = crossover_oracles(w1, w2)
        if oracle_ok(new_w):
            return new_w
        attempts += 1
    return random.choice([w1, w2])

# ------------------------------------------------------------------
# Агент Argonaut (исправленный критерий успеха)
# ------------------------------------------------------------------
class Argonaut:
    def __init__(self, tape: str):
        self.tape = tape
        self.accept_count = 0
        self.generation = 0

    def run(self, w: str, env: str) -> Tuple[str, str]:
        # 1. Найти вхождения оракульного слова
        matches = find_matches(w, self.tape)
        # 2. Если вхождений меньше 1 -> reject (ослабленный критерий)
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

        # 5. Ограничение длины
        if len(new_tape) > 50:
            new_tape = new_tape[:50]

        # 6. УСПЕХ: после перестановки лента содержит оракульное слово w
        if w in new_tape:
            self.generation += 1
            return "accept", new_tape
        else:
            return "loop", new_tape

# ------------------------------------------------------------------
# ArgoMachine (с исправленным evolve_oracles)
# ------------------------------------------------------------------
class ArgoMachine:
    def __init__(self, agents: List[Argonaut], oracle_pool: List[EvolutionaryOracle]):
        self.agents = agents
        self.oracle_pool = oracle_pool
        self.last_winner: Optional[Argonaut] = None
        self.last_oracle: Optional[EvolutionaryOracle] = None
        self.current_env = ""

    def select_oracle(self, env: str) -> EvolutionaryOracle:
        env_vector = compute_semantic_vector(env)
        best = None
        best_score = -1
        for oracle in self.oracle_pool:
            sim_score = cosine_similarity(oracle.semantic_vector, env_vector)
            fitness_score = oracle.fitness
            freshness_score = 1.0 / (oracle.age + 1)
            spec_score = oracle.get_specialization_bonus(env)
            score = (0.4 * sim_score +
                     0.3 * fitness_score +
                     0.2 * freshness_score +
                     0.1 * spec_score)
            if score > best_score:
                best_score = score
                best = oracle
        return best

    def step(self, env: str) -> str:
        oracle = self.select_oracle(env)
        self.last_oracle = oracle
        self.current_env = env
        if oracle is None:
            return "reject"
        w = oracle.word
        acceptors = []
        for ag in self.agents:
            st, new_tape = ag.run(w, env)
            ag.tape = new_tape
            if st == "accept":
                acceptors.append(ag)
                ag.accept_count += 1
                oracle.increment_usage(success=True)
            else:
                oracle.increment_usage(success=False)
        if acceptors:
            winner = max(acceptors, key=lambda x: x.generation)
            self.last_winner = winner
            return "accept"
        return "reject"

    def transpose(self) -> None:
        if self.last_winner is not None:
            winning_tape = self.last_winner.tape
            for ag in self.agents:
                if random.random() < 0.8:
                    ag.tape = winning_tape
                else:
                    ag.tape = self._mutate_tape(winning_tape)

    def _mutate_tape(self, tape: str) -> str:
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
        else:
            if len(tape) >= 2:
                pos = random.randint(0, len(tape) - 2)
                return tape[:pos] + tape[pos+1] + tape[pos] + tape[pos+2:]
        return tape

    def evolve_oracles(self, max_pool_size: int = 50) -> None:
        """Эволюция пула оракулов с ограничением максимального размера."""
        # Обновляем пригодность
        for oracle in self.oracle_pool:
            oracle.update_fitness()
        
        # Удаляем очень плохих (fitness < 0.1 и usage > 5)
        self.oracle_pool = [o for o in self.oracle_pool 
                            if o.fitness >= 0.1 or o.usage_count <= 5]
        
        # Если пул слишком мал, добавляем новые случайные
        while len(self.oracle_pool) < 10:
            new_word = random.choice(["A", "B", "C", "D", "E", "F", "<", ">"])
            self.oracle_pool.append(EvolutionaryOracle(new_word))
        
        # Успешные оракулы
        successful = [o for o in self.oracle_pool if o.fitness > 0.6]
        
        # Кроссовер между успешными (добавляем не более 5 новых)
        added = 0
        if len(successful) >= 2:
            for i in range(min(len(successful)//2, 5)):
                p1 = successful[i]
                p2 = successful[-(i+1)]
                child_word = safe_crossover_oracles(p1.word, p2.word)
                child = EvolutionaryOracle(child_word)
                child.generation = max(p1.generation, p2.generation) + 1
                child.specialization = p1.specialization if p1.fitness > p2.fitness else p2.specialization
                self.oracle_pool.append(child)
                added += 1
        
        # Мутация некоторых оракулов (не более 3 новых)
        mutated = 0
        for i, oracle in enumerate(self.oracle_pool):
            if i % 5 == 0 and oracle.fitness > 0.3 and mutated < 3:
                new_word = safe_mutate_oracle(oracle.word, rate=0.4)
                if new_word != oracle.word:
                    child = EvolutionaryOracle(new_word)
                    child.specialization = oracle.specialization
                    self.oracle_pool.append(child)
                    mutated += 1
        
        # Ограничиваем размер пула: оставляем только лучшие max_pool_size оракулов
        if len(self.oracle_pool) > max_pool_size:
            self.oracle_pool.sort(key=lambda o: o.fitness, reverse=True)
            self.oracle_pool = self.oracle_pool[:max_pool_size]

    def enrich_tapes(self, env: str) -> None:
        num_to_enrich = max(1, len(self.agents) // 5)
        indices = random.sample(range(len(self.agents)), min(num_to_enrich, len(self.agents)))
        for idx in indices:
            pos = random.randint(0, len(self.agents[idx].tape))
            self.agents[idx].tape = (self.agents[idx].tape[:pos] + env + self.agents[idx].tape[pos:])
            if len(self.agents[idx].tape) > 50:
                self.agents[idx].tape = self.agents[idx].tape[:50]

# ------------------------------------------------------------------
# Генерация начального пула
# ------------------------------------------------------------------
def create_initial_oracle_pool(size: int = 15) -> List[EvolutionaryOracle]:
    alphabet = "ABCDEFG<>"
    pool = []
    initial_words = ["A", "B", "C", "D", "E", "F", "<", ">", "AB", "BC", "CD", 
                     "DE", "EF", "FG", "A<", ">B", "<B", "B>", "A>B", "D<E"]
    for _ in range(size):
        if initial_words and random.random() < 0.7:
            word = random.choice(initial_words)
        else:
            word = ''.join(random.choices(alphabet, k=random.randint(1, 3)))
        pool.append(EvolutionaryOracle(word))
    return pool

# ------------------------------------------------------------------
# Функция run_single_experiment с разделением фаз
# ------------------------------------------------------------------
def run_single_experiment(seed: int, verbose: bool = False) -> dict:
    random.seed(seed)
    
    START_TAPE = "A<B>C<D>E<F>G"
    NUM_AGENTS = 12
    INITIAL_ORACLES = 15
    ENVIRONMENTS = ["cat", "dog", "bird", "fish", "tree", "house"]
    MAX_POOL_SIZE = 50  # ограничение размера пула
    
    # Создаём агентов и начальный пул
    agents = [Argonaut(START_TAPE) for _ in range(NUM_AGENTS)]
    oracle_pool = create_initial_oracle_pool(INITIAL_ORACLES)
    machine = ArgoMachine(agents, oracle_pool)
    
    # --- Фаза 1: обучение (30 эпох) ---
    phase1_success = 0
    phase1_times = []
    
    for epoch in range(30):
        env = ENVIRONMENTS[epoch % len(ENVIRONMENTS)]
        machine.enrich_tapes(env)
        if epoch > 0 and machine.last_winner is not None:
            machine.transpose()
        
        for step in range(50):
            res = machine.step(env)
            if res == "accept":
                phase1_success += 1
                phase1_times.append(step + 1)
                break
        
        # Эволюция оракулов только в фазе 1
        machine.evolve_oracles(max_pool_size=MAX_POOL_SIZE)
    
    # Сохраняем состояние пула после фазы 1
    frozen_oracle_pool = machine.oracle_pool[:]  # копия списка
    
    # --- Фаза 2: тестирование (50 эпох) с замороженным пулом ---
    # Заменяем пул на замороженный
    machine.oracle_pool = frozen_oracle_pool
    
    phase2_success = 0
    phase2_times = []
    
    for epoch in range(50):
        env = ENVIRONMENTS[epoch % len(ENVIRONMENTS)]
        # В фазе 2 обогащение не применяем
        # machine.enrich_tapes(env)  # закомментируем
        if epoch > 0 and machine.last_winner is not None:
            machine.transpose()
        
        for step in range(50):
            res = machine.step(env)
            if res == "accept":
                phase2_success += 1
                phase2_times.append(step + 1)
                break
        # НЕ вызываем evolve_oracles() в фазе 2
    
    # Собираем статистику
    oracle_words = [o.word for o in machine.oracle_pool]
    oracle_fitness = [o.fitness for o in machine.oracle_pool]
    perfect_oracles = [o.word for o in machine.oracle_pool if o.fitness >= 1.0]
    
    return {
        'seed': seed,
        'phase1_success': phase1_success,
        'phase1_times': phase1_times,
        'phase2_success': phase2_success,
        'phase2_times': phase2_times,
        'oracle_pool_size': len(machine.oracle_pool),
        'oracle_words': oracle_words,
        'oracle_fitness': oracle_fitness,
        'perfect_oracles': perfect_oracles,
        'last_winner_tape': machine.last_winner.tape if machine.last_winner else None
    }

# ------------------------------------------------------------------
# Статистика и визуализация
# ------------------------------------------------------------------
def mean_ci(data, confidence=0.95):
    if not data:
        return None, None, (None, None)
    n = len(data)
    mean = statistics.mean(data)
    stdev = statistics.stdev(data) if n > 1 else 0.0
    z = 1.96
    margin = z * stdev / (n ** 0.5) if n > 1 else 0
    return mean, stdev, (mean - margin, mean + margin)

def main():
    import sys
    NUM_RUNS = 50
    BASE_SEED = 42
    print(f"Запуск {NUM_RUNS} независимых экспериментов (базовый seed = {BASE_SEED})")
    print("=" * 70)
    results = []
    for i in range(NUM_RUNS):
        seed = BASE_SEED + i
        res = run_single_experiment(seed, verbose=False)
        results.append(res)
        sys.stdout.write(f"\rЗапуск {i+1}/{NUM_RUNS} ...")
        sys.stdout.flush()
    print("\nГотово.\n")

    phase1_success_rates = [r['phase1_success'] / 30 * 100 for r in results]
    phase2_success_rates = [r['phase2_success'] / 50 * 100 for r in results]
    phase1_times_all = [t for r in results for t in r['phase1_times']]
    phase2_times_all = [t for r in results for t in r['phase2_times']]
    oracle_pool_sizes = [r['oracle_pool_size'] for r in results]
    perfect_oracles_count = [len(r['perfect_oracles']) for r in results]

    print("РЕЗУЛЬТАТЫ:")
    print("-" * 50)
    m1, sd1, ci1 = mean_ci(phase1_success_rates)
    print(f"Фаза 1 (30 эпох):")
    print(f"  Успешность: {m1:.2f}% ± {sd1:.2f}%")
    print(f"  95% ДИ: [{ci1[0]:.2f}%, {ci1[1]:.2f}%]")
    m2, sd2, ci2 = mean_ci(phase2_success_rates)
    print(f"\nФаза 2 (50 эпох):")
    print(f"  Успешность: {m2:.2f}% ± {sd2:.2f}%")
    print(f"  95% ДИ: [{ci2[0]:.2f}%, {ci2[1]:.2f}%]")
    if phase1_times_all:
        mt1, sdt1, cit1 = mean_ci(phase1_times_all)
        print(f"\nВремя адаптации (Фаза 1): {mt1:.2f} ± {sdt1:.2f} шагов")
        if cit1[0] is not None:
            print(f"  95% ДИ: [{cit1[0]:.2f}, {cit1[1]:.2f}]")
    if phase2_times_all:
        mt2, sdt2, cit2 = mean_ci(phase2_times_all)
        print(f"\nВремя адаптации (Фаза 2): {mt2:.2f} ± {sdt2:.2f} шагов")
        if cit2[0] is not None:
            print(f"  95% ДИ: [{cit2[0]:.2f}, {cit2[1]:.2f}]")
    mo, sdo, cio = mean_ci(oracle_pool_sizes)
    print(f"\nРазмер пула оракулов: {mo:.1f} ± {sdo:.1f}")
    if cio[0] is not None:
        print(f"  95% ДИ: [{cio[0]:.1f}, {cio[1]:.1f}]")
    print(f"\nСреднее число совершенных оракулов (fitness=1.0): {statistics.mean(perfect_oracles_count):.2f}")
    print(f"  Максимум: {max(perfect_oracles_count)}")

    # Рисунок
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle(f"Статистика Argo10 (финальная версия) по {NUM_RUNS} запускам", fontsize=14)
    ax = axes[0, 0]
    ax.hist(phase1_success_rates, bins=10, color='skyblue', edgecolor='black', alpha=0.7)
    ax.axvline(m1, color='red', linestyle='--', label=f'Среднее: {m1:.1f}%')
    ax.set_xlabel('Успешность в Фазе 1 (%)')
    ax.set_ylabel('Частота')
    ax.set_title('Фаза 1 (30 эпох)')
    ax.legend()
    ax = axes[0, 1]
    ax.hist(phase2_success_rates, bins=10, color='lightgreen', edgecolor='black', alpha=0.7)
    ax.axvline(m2, color='red', linestyle='--', label=f'Среднее: {m2:.1f}%')
    ax.set_xlabel('Успешность в Фазе 2 (%)')
    ax.set_ylabel('Частота')
    ax.set_title('Фаза 2 (50 эпох)')
    ax.legend()
    ax = axes[1, 0]
    if phase2_times_all:
        ax.boxplot([phase2_times_all], vert=True, patch_artist=True,
                   boxprops=dict(facecolor='lightblue'))
        ax.set_ylabel('Шаги до адаптации')
        ax.set_title('Время адаптации в Фазе 2')
        ax.set_xticklabels(['Все успешные эпохи'])
    else:
        ax.text(0.5, 0.5, 'Нет данных', ha='center', va='center')
        ax.set_title('Время адаптации в Фазе 2')
    ax = axes[1, 1]
    ax.scatter(phase1_success_rates, phase2_success_rates, alpha=0.6)
    ax.set_xlabel('Успешность Фазы 1 (%)')
    ax.set_ylabel('Успешность Фазы 2 (%)')
    ax.set_title('Корреляция между фазами')
    plt.tight_layout()
    plt.savefig('argo10_final_results.png', dpi=150, bbox_inches='tight')
    print(f"\nРисунок сохранён как argo10_final_results.png")

    last = results[-1]
    print(f"\nИтоговый пул оракулов (последний запуск, seed={last['seed']}):")
    print(f"  Размер пула: {last['oracle_pool_size']}")
    print(f"  Совершенные оракулы (fitness=1.0): {last['perfect_oracles']}")
    print(f"  Лента победителя: {last['last_winner_tape']}")
    return results

if __name__ == "__main__":
    results = main()