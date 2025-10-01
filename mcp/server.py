import sys,json
from .tools import invoke, ctx
def send(o): sys.stdout.write(json.dumps(o,ensure_ascii=False)+"\n"); sys.stdout.flush()
def main():
    for line in sys.stdin:
        line=line.strip()
        if not line: continue
        try:
            req=json.loads(line); m=req.get("method")
            if m=="initialize":
                p=req.get("params",{})
                if "organization" in p: ctx.org=p["organization"]
                if "project" in p: ctx.project=p["project"]
                if "endpoint" in p: ctx.endpoint=p["endpoint"]
                send({"id":req.get("id"),"result":{"ready":True}}); continue
            if m=="list_tools":
                send({"id":req.get("id"),"result":{"tools":list(invoke.__globals__["TOOLS"].keys())}}); continue
            if m=="invoke_tool":
                t=req["params"]["name"]; pr=req["params"].get("arguments",{})
                
                # REPLACE WITH SIMPLE:
                result = invoke(t, pr)
                    
                send({"id":req.get("id"),"result":result}); continue
            send({"id":req.get("id"),"error":"unknown_method"})
        except Exception as e:
            send({"error":str(e)})
if __name__=="__main__": main()