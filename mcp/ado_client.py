import time, requests
import concurrent.futures
from typing import List, Dict, Any, Optional
from AzureAPI import get_az_access_token, API_VERSION, DEFAULT_ORGANIZATION, DEFAULT_PROJECT
from mcp.config import WIQL_DEFAULT_TOP, WIQL_MAX_RETRIES

class AdoClient:
    def __init__(self, organization=DEFAULT_ORGANIZATION, project=DEFAULT_PROJECT):
        self.org=organization; self.project=project
        self._token=None; self._acquired=0; self._ttl=55*60
    def _ensure(self):
        if (not self._token) or (time.time()-self._acquired>self._ttl):
            self._token=get_az_access_token(); self._acquired=time.time()
    def _headers(self):
        self._ensure()
        return {"Authorization":f"Bearer {self._token}","Accept":"application/json","Content-Type":"application/json"}
    def wiql_ids(self, where: str, top: int = WIQL_DEFAULT_TOP, max_retries: int = WIQL_MAX_RETRIES) -> List[int]:
        """Execute WIQL query and return work item IDs with retry logic."""
        import time
        import random
        
        url = f"https://dev.azure.com/{self.org}/{self.project}/_apis/wit/wiql?$top={min(top, 1000)}&api-version={API_VERSION}"
        
        # Build proper WIQL query structure
        if where.strip().upper().startswith("SELECT"):
            # Full query provided
            query = where
        else:
            # WHERE clause only - build complete SELECT statement
            query = f"""SELECT [System.Id]
FROM WorkItems
WHERE [System.TeamProject] = @Project AND {where}
ORDER BY [System.ChangedDate] DESC"""
        
        body = {"query": query}
        
        for attempt in range(max_retries + 1):
            try:
                r = requests.post(url, headers=self._headers(), json=body, timeout=30)
                r.raise_for_status()
                return [e["id"] for e in r.json().get("workItems", [])][:top]
                
            except (requests.Timeout, requests.ConnectionError, requests.HTTPError) as e:
                if attempt == max_retries:
                    # Final attempt failed
                    raise RuntimeError(f"WIQL query failed after {max_retries + 1} attempts: {e}")
                
                # Check if this is a retryable error
                if isinstance(e, requests.HTTPError):
                    status_code = e.response.status_code
                    if status_code < 500 and status_code != 429:  # Don't retry 4xx errors except rate limiting
                        raise RuntimeError(f"WIQL query failed: {status_code} {e.response.reason}")
                
                # Exponential backoff with jitter
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                print(f"⚠️ WIQL query attempt {attempt + 1} failed, retrying in {wait_time:.1f}s...")
                time.sleep(wait_time)
    def batch(self, ids:List[int], expand="All"):
        if not ids: return []
        url=f"https://dev.azure.com/{self.org}/_apis/wit/workitemsbatch?api-version={API_VERSION}"
        r=requests.post(url,headers=self._headers(),json={"ids":ids,"$expand":expand},timeout=30); r.raise_for_status()
        return r.json().get("value", [])
    def comments(self,wid:int, top: int = None, verbose: bool = True):
        """Load comments for a single work item with optional limit."""
        url=f"https://dev.azure.com/{self.org}/{self.project}/_apis/wit/workItems/{wid}/comments?api-version=7.1-preview.4"
        
        # Add top parameter if specified
        if top is not None:
            url += f"&$top={top}"
            
        if verbose:
            print(f"🔍 Comments API URL: {url}")
        
        r=requests.get(url,headers=self._headers(),timeout=30)
        
        if r.status_code==404: 
            if verbose:
                print(f"❌ Work item {wid} not found")
            return []
            
        if verbose:
            print(f"✅ Comments API Response: {r.status_code}")
            print(f"📄 Response content length: {len(r.text)}")
        
        if r.status_code != 200:
            if verbose:
                print(f"❌ API Error: {r.status_code} - {r.text}")
            
        r.raise_for_status()
        
        data = r.json()
        comments = data.get("comments", [])
        total_count = data.get("totalCount", 0)
        
        if verbose:
            print(f"📊 Comments found: {len(comments)}/{total_count}")
        
            if comments:
                print(f"📝 Sample comment: '{comments[0].get('text', 'No text')[:100]}...'")
            else:
                print("❓ No comments in response - possible work item has no comments")
            
        return comments
    
    def comments_parallel(self, work_item_ids: List[int], max_workers: int = 5, verbose: bool = False, top: int = None) -> Dict[int, List]:
        """Load comments for multiple work items in parallel.
        
        Args:
            work_item_ids: List of work item IDs to load comments for
            max_workers: Maximum number of parallel requests (default: 5)
            verbose: Enable detailed logging (default: False)
            top: Maximum number of comments to load per work item (default: unlimited)
            
        Returns:
            Dictionary mapping work item ID to list of comments
        """
        if not work_item_ids:
            return {}
            
        if verbose:
            print(f"🔄 Loading comments for {len(work_item_ids)} work items in parallel...")
            
        comments_by_id = {}
        
        def load_single_comments(wid: int) -> tuple:
            """Load comments for a single work item. Returns (wid, comments)."""
            try:
                comments = self.comments(wid, top=top, verbose=False)  # Disable individual logging
                return wid, comments
            except Exception as e:
                if verbose:
                    print(f"❌ Failed to load comments for work item {wid}: {e}")
                return wid, []
        
        # Use ThreadPoolExecutor for parallel HTTP requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all comment loading tasks
            future_to_id = {executor.submit(load_single_comments, wid): wid for wid in work_item_ids}
            
            # Collect results as they complete
            completed = 0
            for future in concurrent.futures.as_completed(future_to_id):
                wid, comments = future.result()
                comments_by_id[wid] = comments
                completed += 1
                
                if verbose:
                    print(f"✅ Progress: {completed}/{len(work_item_ids)} - Work item {wid}: {len(comments)} comments")
        
        if verbose:
            total_comments = sum(len(comments) for comments in comments_by_id.values())
            print(f"🎯 Parallel loading complete: {total_comments} total comments loaded")
            
        return comments_by_id
    
    def comments_conditional(self, work_items: List[Dict], verbose: bool = False, top: int = None) -> Dict[int, List]:
        """Load comments only for work items that likely have comments.
        
        Args:
            work_items: List of work item dictionaries from batch() call
            verbose: Enable detailed logging
            top: Maximum number of comments to load per work item
            
        Returns:
            Dictionary mapping work item ID to list of comments
        """
        # Filter work items that likely have comments
        items_with_comments = []
        items_without_comments = []
        
        for item in work_items:
            wid = item["id"]
            
            # Check various indicators that work item might have comments
            fields = item.get("fields", {})
            
            # Primary indicator: System.CommentCount
            comment_count = fields.get("System.CommentCount", 0)
            if comment_count > 0:
                items_with_comments.append(wid)
                continue
            elif comment_count == 0:
                items_without_comments.append(wid)
                continue
            
            # Secondary indicators if CommentCount not available
            history_count = fields.get("System.HistoryCount", 0)
            revision_count = fields.get("System.Rev", 1)
            
            # If there's been activity beyond initial creation
            if history_count > 1 or revision_count > 1:
                # Check if there have been recent changes
                changed_date = fields.get("System.ChangedDate")
                created_date = fields.get("System.CreatedDate")
                
                if changed_date and created_date and changed_date != created_date:
                    items_with_comments.append(wid)
                else:
                    items_without_comments.append(wid)
            else:
                # Likely no comments
                items_without_comments.append(wid)
        
        if verbose:
            print(f"📊 Conditional analysis:")
            print(f"   • {len(items_with_comments)} work items likely have comments")
            print(f"   • {len(items_without_comments)} work items likely have no comments")
        
        # Initialize results
        comments_by_id = {}
        
        # Set empty comments for items without comments (skip API calls)
        for wid in items_without_comments:
            comments_by_id[wid] = []
            
        # Load comments in parallel for items that likely have comments
        if items_with_comments:
            if verbose:
                print(f"🔄 Loading comments for {len(items_with_comments)} work items...")
                
            comments_loaded = self.comments_parallel(
                items_with_comments, 
                max_workers=20,  # INCREASE from 10 to 20
                verbose=verbose,
                top=top
            )
            comments_by_id.update(comments_loaded)
        
        if verbose:
            total_comments = sum(len(comments) for comments in comments_by_id.values())
            items_with_actual_comments = sum(1 for comments in comments_by_id.values() if len(comments) > 0)
            print(f"🎯 Conditional loading complete:")
            print(f"   • {total_comments} total comments loaded")
            print(f"   • {items_with_actual_comments} work items actually had comments")
            
        return comments_by_id
    
    def updates_parallel(self, work_item_ids: List[int], max_workers: int = 10) -> Dict[int, List]:
        """Load updates for multiple work items in parallel.
        
        Args:
            work_item_ids: List of work item IDs to load updates for
            max_workers: Maximum number of parallel requests
            
        Returns:
            Dictionary mapping work item ID to list of updates
        """
        if not work_item_ids:
            return {}
            
        updates_by_id = {}
        
        def load_single_updates(wid: int) -> tuple:
            """Load updates for a single work item. Returns (wid, updates)."""
            try:
                updates = self.updates(wid)
                return wid, updates
            except Exception as e:
                return wid, []
        
        # Use ThreadPoolExecutor for parallel HTTP requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all update loading tasks
            future_to_id = {executor.submit(load_single_updates, wid): wid for wid in work_item_ids}
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_id):
                wid, updates = future.result()
                updates_by_id[wid] = updates
            
        return updates_by_id
    
    def updates(self,wid:int):
        url=f"https://dev.azure.com/{self.org}/_apis/wit/workItems/{wid}/updates?api-version={API_VERSION}"
        r=requests.get(url,headers=self._headers(),timeout=30); r.raise_for_status()
        return r.json().get("value", [])