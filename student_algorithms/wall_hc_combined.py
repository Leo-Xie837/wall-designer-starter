import random
import copy
from wall_designer.scorer import evaluate
from student_algorithms.wall_multi_start_lookahead import generate as build_initial_layout
from student_algorithms.wall_hc_swap import apply_physical_packing

MAX_STEPS = 10000

def generate(wall, artworks, scoring_data):
    current_s = build_initial_layout(wall, artworks, scoring_data)
    current_score = evaluate(wall, current_s, artworks, scoring_data)['total']

    for _ in range(MAX_STEPS):
        move_type = random.choice(['swap', 'replace', 'add_remove'])
        neighbor = copy.deepcopy(current_s)
        on_wall_ids = {p['artwork_id'] for p in neighbor}
        candidates = [a for a in artworks if a['id'] not in on_wall_ids and a.get('eligible', True)]

        if move_type == 'swap' and len(neighbor) >= 2:
            i, j = sorted(random.sample(range(len(neighbor)), 2))
            neighbor[i:j+1] = list(reversed(neighbor[i:j+1]))
        elif move_type == 'replace' and candidates:
            neighbor[random.randrange(len(neighbor))]['artwork_id'] = random.choice(candidates)['id']
        elif move_type == 'add_remove':
            if random.random() > 0.5 and candidates: # Try Add
                neighbor.append({'artwork_id': random.choice(candidates)['id'], 'x_ft': 0, 'y_ft': 0})
            elif len(neighbor) > 1: # Try Remove
                neighbor.pop(random.randrange(len(neighbor)))

        neighbor = apply_physical_packing(neighbor, wall, artworks, scoring_data)
        score = evaluate(wall, neighbor, artworks, scoring_data)['total']
        
        if score > current_score:
            current_s, current_score = neighbor, score

    return current_s