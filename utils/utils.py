from typing import List, Dict, Any
from utils.logger import get_logger
logger = get_logger(__name__)

def merge_batch_responses(batch_responses: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Intelligently merge multiple batch responses into a single consolidated document
    
    Strategy:
    1. First non-null value wins for header/metadata fields
    2. Lists are concatenated and deduplicated
    3. Nested objects are merged recursively
    4. Preserve all unique information from all batches
    """
    try:
        logger.info(f"Merging {len(batch_responses)} batch responses")
        
        if not batch_responses:
            return {}
        
        if len(batch_responses) == 1:
            return batch_responses[0]["response"]
        
        # Initialize with first batch
        merged_result = {}
        
        # Process each batch response
        for batch in batch_responses:
            batch_data = batch.get("response", {})
            merged_result = deep_merge(merged_result, batch_data)
        
        logger.info("Batch responses merged successfully")
        return merged_result
        
    except Exception as e:
        logger.error(f"Error merging batch responses: {e}")
        raise


def deep_merge(base: Any, update: Any) -> Any:
    """
    Recursively merge two dictionaries/objects
    
    Rules:
    - If both are dicts: merge recursively
    - If both are lists: concatenate and deduplicate
    - If one is None: use the non-None value
    - Otherwise: prefer update if not None, else keep base
    """
    # Handle None cases
    if update is None:
        return base
    if base is None:
        return update
    
    # Handle dictionaries
    if isinstance(base, dict) and isinstance(update, dict):
        result = base.copy()
        for key, value in update.items():
            if key in result:
                result[key] = deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    
    # Handle lists - concatenate and deduplicate
    if isinstance(base, list) and isinstance(update, list):
        # For list of primitives
        if all(not isinstance(item, (dict, list)) for item in base + update):
            return list(dict.fromkeys(base + update))  # Preserve order, remove duplicates
        
        # For list of dicts/objects - concatenate all
        return base + update
    
    # For primitives: prefer non-None update, otherwise keep base
    return update if update is not None else base


def deduplicate_list_of_dicts(items: List[Dict]) -> List[Dict]:
    """
    Deduplicate list of dictionaries based on content
    """
    seen = []
    result = []
    for item in items:
        # Simple comparison - could be enhanced with more sophisticated logic
        if item not in seen:
            seen.append(item)
            result.append(item)
    return result