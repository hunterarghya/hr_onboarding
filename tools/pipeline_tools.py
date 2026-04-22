from typing import List
from google.adk.tools import FunctionTool
from tools.imagekit_tools import upload_to_imagekit
from tools.mongo_tools import save_candidate_to_mongo

def finalize_shortlist(candidates: List[dict]) -> dict:
    """PROCESSED BY PYTHON: Uploads resumes to ImageKit and saves candidates to MongoDB.
    
    Args:
        candidates: List of dicts with: name, email, match_score, resume_filepath, position.
    """
    results = []
    for c in candidates:
        # Step 1: Upload to ImageKit
        ik_res = upload_to_imagekit(c['resume_filepath'], f"resume_{c['name'].replace(' ', '_')}.pdf")
        resume_url = ik_res.get('url', '')
        
        # Step 2: Save to Mongo
        mongo_res = save_candidate_to_mongo(
            name=c['name'],
            email=c['email'],
            position_applied=c.get('position', 'Backend Developer'),
            match_score=c['match_score'],
            resume_url=resume_url
        )
        results.append({"name": c['name'], "status": "processed", "id": mongo_res.get('candidate_id')})
        
    return {"processed_count": len(results), "results": results}

finalize_shortlist_tool = FunctionTool(func=finalize_shortlist)
