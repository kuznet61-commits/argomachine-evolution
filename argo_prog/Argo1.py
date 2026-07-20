import random
import string
from typing import List, Tuple

# ----------- те же операции, что и раньше -----------
def find_matches(w: str, tape: str) -> List[int]:
    return [i for i in range(len(tape) - len(w) + 1) if tape[i:i+len(w)] == w]

def cut_keep_markers(tape: str, matches: List[int], w: str) -> List[str]:
    fragments, prev = [], 0
    for m in sorted(matches):
        fragments.append(tape[prev:m])
        fragments.append(tape[m:m+len(w)])
        prev = m + len(w)
    fragments.append(tape[prev:])
    return [f for f in fragments if f]

def random_paste(frags: List[str]) -> str:
    random.shuffle(frags)
    return ''.join(frags)

# ----------- агент и машина без изменений -----------
class Argonaut:
    def __init__(self, tape: str):
        self.tape = tape
    def run(self, w: str, env: str) -> Tuple[str, str]:
        matches = find_matches(w, self.tape)
        if len(matches) < 2:
            return "reject", self.tape
        new_tape = random_paste(cut_keep_markers(self.tape, matches, w))
        if new_tape == env:          # жёсткое равенство
            return "accept", new_tape
        else:
            return "loop", new_tape

class ArgoMachine:
    def __init__(self, agents: List[Argonaut]):
        self.agents = agents
    def step(self, w: str, env: str) -> str:
        acceptors = []
        for ag in self.agents:
            st, tape = ag.run(w, env)
            if st == "accept":
                acceptors.append(ag)
        if acceptors:
            winner = random.choice(acceptors)
            for ag in self.agents:
                ag.tape = winner.tape
            return "accept"
        return "reject"

# ----------- эволюция oracle + среда -----------
def mutate(w: str, rate: float = 0.2) -> str:
    """Случайно заменяет/удаляет/добавляет один символ с вероятностью rate"""
    if random.random() > rate:
        return w
    op = random.choice(['ins', 'del', 'chg'])
    if op == 'ins':
        pos = random.randint(0, len(w))
        return w[:pos] + random.choice(string.ascii_letters + string.digits) + w[pos:]
    elif op == 'del' and len(w) > 1:
        pos = random.randint(0, len(w) - 1)
        return w[:pos] + w[pos+1:]
    else:  # chg
        pos = random.randint(0, len(w) - 1)
        return w[:pos] + random.choice(string.ascii_letters + string.digits) + w[pos+1:]

# ----------- фильтрация oracle -----------
ALPHABET = set("AB<~~>CD<~~>EF")   # тот же набор, что и в START_TAPE

def oracle_ok(w: str) -> bool:
    """True, если ВСЕ символы w принадлежат алфавиту ленты"""
    return set(w).issubset(ALPHABET)

def safe_mutate(w: str, rate: float = 0.2) -> str:
    """мутируем, пока не получим допустимое слово длиной ≥2"""
    while True:
        new = mutate(w, rate)
        if oracle_ok(new) and len(new) >= 2:
            return new

def random_environment(base_tape: str) -> str:
    """перемешиваем символы base_tape"""
    return ''.join(random.sample(base_tape, k=len(base_tape)))

# ----------- запуск эволюции -----------
if __name__ == "__main__":
    START_TAPE = "AB<~~>CD<~~>EF"
    oracle = "<~~>"
    machine = ArgoMachine([Argonaut(START_TAPE) for _ in range(3)])

    for epoch in range(20):                       # 20 катастроф
        env = random_environment(START_TAPE)
        print(f"\nEpoch {epoch+1} | oracle='{oracle}' | env='{env}'")

        for step in range(1000):                  # <-- должно быть здесь
            res = machine.step(oracle, env)
            if res == "accept":
                print(f"  adapted at step {step+1}")
                break
        else:
            print("  не адаптировалась за 1000 шагов")

        oracle = safe_mutate(oracle)              # катастрофа → новое слово

