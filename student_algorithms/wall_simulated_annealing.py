import math
import random
import copy
from wall_designer.scorer import evaluate
from student_algorithms.wall_multi_start_lookahead import generate as build_initial_layout

# Initial Configuration of Annealing
T0 = 1.0            # Initial temperature
ALPHA = 0.9999     # Cooling rate (temperature multiplier per step)
TMIN = 0.0001       # Minimum stopping temperature
MAX_PROPOSALS = 200000 

def apply_physical_packing(placements, wall, artworks, scoring_data):
    """
    Gallery Physics: Resets coordinates after swaps to handle varying 
    artwork widths and centers the final arrangement.
    """
    packed = []
    constraints = scoring_data.get('scoring', {}).get('hard_constraints', {})
    min_gap = constraints.get('min_gap_ft', {}).get('value', 0.6) + 0.02
    wall_width = wall.get('width_ft', 40.0)
    target_y = wall.get('default_hang_y_ft', 5.5)
    
    # Sequential Packing
    current_x = max(0.0, min_gap / 2.0)
    for p in placements:
        art = next(a for a in artworks if a['id'] == p['artwork_id'])
        w, h = float(art.get('width_ft', 0)), float(art.get('height_ft', 0))
        packed.append({
            'artwork_id': p['artwork_id'],
            'x_ft': current_x,
            'y_ft': round(target_y - (h / 2.0), 2)
        })
        current_x += w + min_gap

    # Centering Logic
    if packed:
        first_x = packed[0]['x_ft']
        target_id = packed[-1]['artwork_id']

        # Find width of the last piece for centering math
        last_w = 0.0
        for a in artworks:
            if a['id'] == target_id:
                last_w = float(a.get('width_ft', 0.0))
                break

        wall_width = wall.get('width_ft', 40.0)
        group_width = (packed[-1]['x_ft'] + last_w) - first_x
        shift_amount = ((wall_width - group_width) / 2.0) - first_x

        for p in packed:
            p['x_ft'] = round(p['x_ft'] + shift_amount, 2)
            
    return packed

def anneal_accept(delta, T):
    """
    Metropolis Acceptance Logic.
    Accepts improvements immediately; accepts worse moves with P = e^(-delta/T).
    """
    if delta <= 0: # Neighbor is better or equal (higher score)
        return True
    if T <= 1e-12: # Avoid division by zero at ultra-low T
        return False
    return random.random() < math.exp(-delta / T)

def generate(wall, artworks, scoring_data):
    """
    Integrated Optimizer from construction to Annealing refinement.
    """
    # Generate Initial Layout (Greedy Nearest-Neighbor equivalent)
    tour = build_initial_layout(wall, artworks, scoring_data) #
    cur_score = evaluate(wall, tour, artworks, scoring_data)['total']
    
    best_tour = copy.deepcopy(tour)
    best_score = cur_score
    
    T = T0
    proposed = 0
    accepted = 0

    # Main Annealing Loop
    # proposed < MAX_PROPOSALS and T > TMIN
    while proposed < MAX_PROPOSALS and T > TMIN:
        proposed += 1
        
        # Propose a 2-opt neighbor
        if len(tour) >= 2:
            i, k = sorted(random.sample(range(len(tour)), 2))
            neighbor_tour = copy.deepcopy(tour)
            # Reversing the segment between i and k
            neighbor_tour[i:k+1] = list(reversed(neighbor_tour[i:k+1]))
            
            # Recalculate physics (Gallery-specific 'reconnection')
            neighbor_tour = apply_physical_packing(neighbor_tour, wall, artworks, scoring_data)
            neighbor_score = evaluate(wall, neighbor_tour, artworks, scoring_data)['total']
            
            # Delta calculation (current - neighbor for maximization)
            delta = cur_score - neighbor_score 
            
            # Acceptance decision
            if anneal_accept(delta, T):
                tour = neighbor_tour
                cur_score = neighbor_score
                accepted += 1
                
                # Track best solution seen so far
                if cur_score > best_score:
                    best_score = cur_score
                    best_tour = copy.deepcopy(tour)
        
        # Cooling Schedule: T = T * ALPHA
        T = T * ALPHA

    return best_tour