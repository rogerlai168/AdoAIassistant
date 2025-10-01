from typing import Dict, Any, List
import re
FIELD_MAP={"System.Id":"id","System.Title":"title","System.WorkItemType":"type","System.State":"state","System.AssignedTo":"assigned_to","System.AreaPath":"area_path","System.IterationPath":"iteration_path","System.Tags":"tags","Microsoft.VSTS.Common.Priority":"priority","Microsoft.VSTS.TCM.ReproSteps":"repro_steps","Microsoft.VSTS.Common.ResolvedDate":"resolved_date","Microsoft.VSTS.Common.ClosedDate":"closed_date","System.ChangedDate":"changed_date","System.CreatedDate":"created_date"}
INTERNAL_DOMAINS={"microsoft.com","contoso.com"}
TAG_SPLIT=re.compile(r"\s*;\s*"); HTML=re.compile(r"<[^>]+>")
def strip_html(s): return HTML.sub("",s)
def partner_comments(cs):
    out=[]
    for c in cs or []:
        a=c.get("createdBy") or {}; u=a.get("uniqueName","")
        if "@" in u and u.split("@")[-1].lower() not in INTERNAL_DOMAINS: out.append(c)
    return out
def state_transitions(upds):
    ts=[]
    for u in upds or []:
        f=u.get("fields",{}).get("System.State")
        if f and "oldValue" in f and "newValue" in f: ts.append({"from":f["oldValue"],"to":f["newValue"],"date":u.get("revisedDate")})
    return ts
def change_dates(upds,created,changed):
    ds=[]; 
    if created: ds.append(created)
    for u in upds or []:
        d=u.get("revisedDate"); 
        if d: ds.append(d)
    if changed and (not ds or ds[-1]!=changed): ds.append(changed)
    seen=set(); out=[]
    for d in ds:
        if d and d not in seen: seen.add(d); out.append(d)
    return out
def normalize(raw,comments=None,updates=None):
    f=raw.get("fields",{}); o={}
    for ref,a in FIELD_MAP.items(): o[a]=f.get(ref)
    if isinstance(o.get("assigned_to"),dict): o["assigned_to"]=o["assigned_to"].get("displayName") or o["assigned_to"].get("uniqueName")
    if o.get("tags"): o["tags"]=[t for t in TAG_SPLIT.split(o["tags"]) if t]
    if o.get("repro_steps"): o["repro_steps"]=strip_html(o["repro_steps"])
    allc=comments or []; pc=partner_comments(allc)
    o.update({"comments":allc,"partner_comments":pc,"comment_count":len(allc),"partner_comment_count":len(pc),"revision_count":len(updates) if updates else 0,"state_transitions":state_transitions(updates),"change_dates":change_dates(updates,o.get("created_date"),o.get("changed_date")),"last_update_author":(updates[-1].get("revisedBy",{}) if updates else {}).get("displayName"),"url":raw.get("url")})
    return o