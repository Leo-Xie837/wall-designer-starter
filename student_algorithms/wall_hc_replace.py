import random
import copy
from wall_designer.scorer import evaluate
from student_algorithms.wall_multi_start_lookahead import generate as build_initial_layout

MAX_STEPS = 5000

def generate(wall, artworks, scoring_data):
    current_s = build_initial_layout(wall, artworks, scoring_data)
    current_score = evaluate(wall, current_s, artworks, scoring_data)['total']
    
    on_wall_ids = {p['artwork_id'] for p in current_s}
    candidates = [a for a in artworks if a['id'] not in on_wall_ids and a.get('eligible', True)]

    for _ in range(MAX_STEPS):
        if not candidates: break
        # Propose Replacement
        neighbor = copy.deepcopy(current_s)
        idx = random.randrange(len(neighbor))
        new_art = random.choice(candidates)
        
        old_art_id = neighbor[idx]['artwork_id']
        neighbor[idx]['artwork_id'] = new_art['id']
        
        # apply_physical_packing
        from student_algorithms.wall_hc_swap import apply_physical_packing
        neighbor = apply_physical_packing(neighbor, wall, artworks, scoring_data)
        
        score = evaluate(wall, neighbor, artworks, scoring_data)['total']
        if score > current_score:
            current_s, current_score = neighbor, score
            candidates = [a for a in artworks if a['id'] not in {p['artwork_id'] for p in current_s}]
            
    return current_s