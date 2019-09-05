def check(text):
    if "csaw" in text.lower() or " points" in text.lower():
        clean = text.split(" ")
        out = 0
        for word in clean:
            try:
                out = int(word)
            except:
                pass
        if not out == 0:
            return ["CSAW", out]
        else: 
            return ""