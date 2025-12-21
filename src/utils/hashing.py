import hashlib
def plan_hash(prompt:str, negative:str, seed:int, ar:str)->str:
    src = f"{prompt}|{negative}|{seed}|{ar}"
    return hashlib.sha256(src.encode("utf-8")).hexdigest()