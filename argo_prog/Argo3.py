import random
import string
import statistics
from typing import List, Tuple

# ----------- те же операции, что и раньше -----------
def find_matches(w: str, tape: str) -> List[int]:
    return [i for i in range(len(tape) - len(w) + 1) if tape[i:i+len(w)] == w]

def true_random_perm(tape: str, w: str) -> str:
    """really uniform permutation of the entire tape"""
    return ''.join(random.sample(tape, k=len(tape)))

def random_paste(frags: List[str]) -> str:
    random.shuffle(frags)
    return ''.join(frags)

# ----------- агент и машина без изменений -----------
class Argonaut:
    def __init__(self, tape: str):
        self.tape = tape
    def run(self, w: str, env: str) -> Tuple[str, str]:
        # --- 1.  uniform permutation --------------
        new_tape = ''.join(random.sample(self.tape, k=len(self.tape)))
        # --- 2.  soft condition -------------------
        if sorted(new_tape) == sorted(env):
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
    # -----------  put this FIRST  -----------
    START_TAPE = "A<~"
    ALPHABET   = set(START_TAPE)    # тот же набор, что и в START_TAPE
    # ----------------------------------------
    oracle = "<~~>"
    machine = ArgoMachine([Argonaut(START_TAPE) for _ in range(3)])

    for epoch in range(20):                       # 20 катастроф
        env = random_environment(START_TAPE)
        print(f"\nEpoch {epoch+1} | oracle='{oracle}' | env='{env}'")

        for step in range(30):            # was 1000
            res = machine.step(oracle, env)
            if res == "accept":
                print(f"  adapted at step {step+1}")
                break
        else:
            print("  metastable (30 steps)")

        oracle = safe_mutate(oracle)              # катастрофа → новое слово

adapt_steps = []               # новый список
for epoch in range(1000):      # было 20
    env = random_environment(START_TAPE)
    if epoch % 100 == 0:
        print(f"\nEpoch {epoch} ...")   # чтобы видеть, что не завис
    for step in range(30):
        res = machine.step(oracle, env)
        if res == "accept":
            adapt_steps.append(step + 1)
            break
    else:
        adapt_steps.append(30)          # метастабильные записываем как 30

print("\n------ статистика ------")
print("среднее :", statistics.mean(adapt_steps))
print("макс    :", max(adapt_steps))
print("метаст  :", sum(1 for s in adapt_steps if s == 30), "из", len(adapt_steps))
