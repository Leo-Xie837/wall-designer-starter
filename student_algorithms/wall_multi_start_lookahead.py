from wall_designer.scorer import evaluate
import copy

def run_lookahead_from_start(wall, initial_art, other_candidates, scoring_data):
    """Helper function to complete a wall given a fixed first piece."""
    placements = []
    remaining = copy.copy(other_candidates)
    
    wall_width = wall.get('width_ft', 0.0)
    constraints = scoring_data.get('scoring', {}).get('hard_constraints', {})
    min_gap = constraints.get('min_gap_ft', {}).get('value', 0.25)
    target_y = wall.get('default_hang_y_ft', 5.5)
    
    # Place the forced first piece
    w0 = float(initial_art.get('width_ft', 0.0) or 0.0)
    px0 = max(0.0, min_gap / 2.0)
    py0 = target_y - (float(initial_art.get('height_ft', 0.0) or 0.0) / 2.0)
    
    placements.append({
        'artwork_id': initial_art['id'],
        'x_ft': round(px0, 2), 'y_ft': round(py0, 2),
        'locked': False, 'required': False, 'notes': 'Multi-start: Forced First'
    })
    
    current_x = px0 + w0 + min_gap

    # Fill the rest of the wall using Look-Ahead logic
    while remaining:
        best_candidate = None
        best_path_score = -1.0
        best_placement_obj = None

        for art1 in remaining:
            w1 = float(art1.get('width_ft', 0.0) or 0.0)
            px1 = current_x
            py1 = target_y - (float(art1.get('height_ft', 0.0) or 0.0) / 2.0)

            if px1 + w1 > wall_width: continue

            obj1 = {'artwork_id': art1['id'], 'x_ft': round(px1, 2), 'y_ft': round(py1, 2), 'notes': 'Look-ahead loop'}
            trial_1 = placements + [obj1]
            
            # Look one step further
            best_future = evaluate(wall, trial_1, other_candidates + [initial_art], scoring_data)['total']
            next_x = obj1['x_ft'] + w1 + min_gap
            
            for art2 in [a for a in remaining if a['id'] != art1['id']]:
                w2 = float(art2.get('width_ft', 0.0) or 0.0)
                if next_x + w2 <= wall_width:
                    obj2 = {'artwork_id': art2['id'], 'x_ft': round(next_x, 2), 'y_ft': py1}
                    path_score = evaluate(wall, trial_1 + [obj2], other_candidates + [initial_art], scoring_data)['total']
                    if path_score > best_future: best_future = path_score
            
            if best_future > best_path_score:
                best_path_score = best_future
                best_candidate = art1
                best_placement_obj = obj1

        if best_candidate and best_path_score > 0:
            placements.append(best_placement_obj)
            remaining.remove(best_candidate)
            current_x = best_placement_obj['x_ft'] + float(best_candidate.get('width_ft', 0.0)) + min_gap
        else:
            break 

    return placements, evaluate(wall, placements, other_candidates + [initial_art], scoring_data)['total']

def generate(wall, artworks, scoring_data):
    """Multi-start coordinator using Look-Ahead"""
    eligible = [a for a in artworks if a.get('eligible', True)]
    # Pick the top 3 candidates (by focal weight) to start with
    initial_works = sorted(eligible, key=lambda x: float(x.get('focal_weight', 0)), reverse=True)[:3]
    
    best_overall_placements = []
    best_overall_score = -1.0

    for initial_work in initial_works:
        others = [a for a in eligible if a['id'] != initial_work['id']]
        layout, score = run_lookahead_from_start(wall, initial_work, others, scoring_data)
        
        if score > best_overall_score:
            best_overall_score = score
            best_overall_placements = layout
    
    # Centering Logic
    if best_overall_placements:
        first_x = best_overall_placements[0]['x_ft']
        target_id = best_overall_placements[-1]['artwork_id']
        
        # Find width of the last piece for centering math
        last_w = 0.0
        for a in artworks:
            if a['id'] == target_id:
                last_w = float(a.get('width_ft', 0.0))
                break
        
        wall_width = wall.get('width_ft', 40.0)
        group_width = (best_overall_placements[-1]['x_ft'] + last_w) - first_x
        shift_amount = ((wall_width - group_width) / 2.0) - first_x
        
        for p in best_overall_placements:
            p['x_ft'] = round(p['x_ft'] + shift_amount, 2)

    return best_overall_placements