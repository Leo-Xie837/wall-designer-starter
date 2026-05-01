from wall_designer.scorer import evaluate
import copy

def generate(wall, artworks, scoring_data):
    """
    Score-Guided Selection (Hill Climbing Construction):
    At each slot, trial every available candidate and pick the one 
    that yields the highest total score from the Scorer.
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
        best_score = -1.0
        best_placement_obj = None

        # Trial every remaining candidate for the next available slot
        for art in remaining_candidates:
            width = float(art.get('width_ft', 0.0) or 0.0)
            
            # Use specific locked position if defined
            if art.get('locked') and art.get('locked_position', {}).get('x_ft') is not None:
                px = float(art['locked_position']['x_ft'])
                py = float(art['locked_position'].get('y_ft', target_y))
            else:
                px = current_x
                py = target_y - (float(art.get('height_ft', 0.0) or 0.0) / 2.0)

            # Check if it physically fits before even scoring
            if px + width > wall_width:
                continue

            # Create a temporary placement to test
            temp_placement = {
                'artwork_id': art['id'],
                'x_ft': round(px, 2),
                'y_ft': round(py, 2),
                'locked': bool(art.get('locked', False)),
                'required': bool(art.get('required', False)),
                'notes': 'Hill climbing trial'
            }
            trial_placements = placements + [temp_placement]

            # The Score-Guided Decision: Call the judge
            result = evaluate(wall, trial_placements, artworks, scoring_data)
            
            # Choose the "best improvement"
            if result['total'] > best_score:
                best_score = result['total']
                best_candidate = art
                best_placement_obj = temp_placement

        # Commit the winner and advance the x-position
        if best_candidate and best_score > 0:
            placements.append(best_placement_obj)
            remaining_candidates.remove(best_candidate)
            
            art_width = float(best_candidate.get('width_ft', 0.0) or 0.0)
            current_x = best_placement_obj['x_ft'] + art_width + min_gap
        else:
            # Either no pieces fit or all remaining pieces fail constraints
            break

    return placements