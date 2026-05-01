import random
import copy
from wall_designer.scorer import evaluate
from student_algorithms.wall_multi_start_lookahead import generate as build_initial_layout

MAX_STEPS = 5000

def apply_physical_packing(placements, wall, artworks, scoring_data):
    """Helper to reset coordinates and center the wall."""
    packed = []
    min_gap = scoring_data.get('scoring', {}).get('hard_constraints', {}).get('min_gap_ft', {}).get('value', 0.6) + 0.02
    current_x = max(0.0, min_gap / 2.0)
    for p in placements:
        art = next(a for a in artworks if a['id'] == p['artwork_id'])
        h = float(art.get('height_ft', 0))
        packed.append({'artwork_id': p['artwork_id'], 'x_ft': current_x, 'y_ft': round(wall.get('default_hang_y_ft', 5.5) - (h / 2.0), 2)})
        current_x += float(art.get('width_ft', 0)) + min_gap
    # Centering Logic
    if packed:
        last_w = float(next(a for a in artworks if a['id'] == packed[-1]['artwork_id']).get('width_ft', 0))
        shift = ((wall.get('width_ft', 40.0) - (packed[-1]['x_ft'] + last_w - packed[0]['x_ft'])) / 2.0) - packed[0]['x_ft']
        for p in packed: p['x_ft'] = round(p['x_ft'] + shift, 2)
    return packed

def generate(wall, artworks, scoring_data):
    current_s = build_initial_layout(wall, artworks, scoring_data)
    current_score = evaluate(wall, current_s, artworks, scoring_data)['total']
    
    for _ in range(MAX_STEPS):
        if len(current_s) < 2: break
        # Propose Swap
        i, j = sorted(random.sample(range(len(current_s)), 2))
        neighbor = copy.deepcopy(current_s)
        neighbor[i:j+1] = list(reversed(neighbor[i:j+1]))
        neighbor = apply_physical_packing(neighbor, wall, artworks, scoring_data)
        
        score = evaluate(wall, neighbor, artworks, scoring_data)['total']
        if score > current_score: # Hill Climbing: Accept only improvements
            current_s, current_score = neighbor, score
            
    return current_s