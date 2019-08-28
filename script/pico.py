def check(text):
    if "picoCTF" in text or "Score: " in text:
        clean = text.split(" ")
        out = 0
        for word in clean:
            try:
                out = int(word)
            except:
                pass
        if not out == 0:
            return ["picoCTF", out]