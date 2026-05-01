from wall_designer.scorer import evaluate
import copy

def generate(wall, artworks, scoring_data):
    """
    Short Look-Ahead Greedy:
    Trials every candidate for the current slot, but selects the one 
    that results in the highest potential score after the NEXT placement.
    """
    remaining_candidates = [a for a in artworks if a.get('eligible', True)]
    placements = []
    
    wall_width = wall.get('width_ft', 0.0)
    constraints = scoring_data.get('scoring', {}).get('hard_constraints', {})
    min_gap = constraints.get('min_gap_ft', {}).get('value', 0.25)
    target_y = wall.get('default_hang_y_ft', 5.5)
    
    current_x = max(0.0, min_gap / 2.0)

    while remaining_candidates:
        best_candidate = None
        best_path_score = -1.0
        best_placement_obj = None

        # First Loop: Trial every candidate for the current slot
        for art1 in remaining_candidates:
            w1 = float(art1.get('width_ft', 0.0) or 0.0)
            
            # Position calculation for art1
            if art1.get('locked') and art1.get('locked_position', {}).get('x_ft') is not None:
                px1 = float(art1['locked_position']['x_ft'])
                py1 = float(art1['locked_position'].get('y_ft', target_y))
            else:
                px1 = current_x
                py1 = target_y - (float(art1.get('height_ft', 0.0) or 0.0) / 2.0)

            if px1 + w1 > wall_width:
                continue

            obj1 = {
                'artwork_id': art1['id'],
                'x_ft': round(px1, 2),
                'y_ft': round(py1, 2),
                'locked': bool(art1.get('locked', False)),
                'required': bool(art1.get('required', False)),
                'notes': 'Look-ahead: Current Slot'
            }
            
            # Baseline score of just this piece added
            trial_1 = placements + [obj1]
            score_1 = evaluate(wall, trial_1, artworks, scoring_data)['total']
            
            # Second Loop (Look-Ahead): Trial candidates for the next slot
            best_future_score = score_1
            next_x = obj1['x_ft'] + w1 + min_gap
            
            others = [a for a in remaining_candidates if a['id'] != art1['id']]
            for art2 in others:
                w2 = float(art2.get('width_ft', 0.0) or 0.0)
                
                if art2.get('locked') and art2.get('locked_position', {}).get('x_ft') is not None:
                    px2 = float(art2['locked_position']['x_ft'])
                    py2 = float(art2['locked_position'].get('y_ft', target_y))
                else:
                    px2 = next_x
                    py2 = target_y - (float(art2.get('height_ft', 0.0) or 0.0) / 2.0)
                
                if px2 + w2 > wall_width:
                    continue
                
                obj2 = {
                    'artwork_id': art2['id'],
                    'x_ft': round(px2, 2),
                    'y_ft': round(py2, 2),
                    'locked': bool(art2.get('locked', False)),
                    'required': bool(art2.get('required', False)),
                    'notes': 'Look-ahead: Projected Next'
                }
                
                # The Look-Ahead Check: Score the layout of (Current + art1 + art2)
                score_path = evaluate(wall, trial_1 + [obj2], artworks, scoring_data)['total']
                if score_path > best_future_score:
                    best_future_score = score_path
            
            # Comparison of whether art1 lead to the best overall next step?
            if best_future_score > best_path_score:
                best_path_score = best_future_score
                best_candidate = art1
                best_placement_obj = obj1

        # Commit the choice that set up the best possibility
        if best_candidate and best_path_score > 0:
            placements.append(best_placement_obj)
            remaining_candidates.remove(best_candidate)
            
            art_width = float(best_candidate.get('width_ft', 0.0) or 0.0)
            current_x = best_placement_obj['x_ft'] + art_width + min_gap
        else:
            break

    return placements