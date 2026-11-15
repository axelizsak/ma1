"""
Many posts in the data are built on the same sentence with a different product,
city or emoji. template_of() gives such posts the same key, so we can spot them.
"""
import re

STOCK_OPENERS = (r"^(breaking|psa|not a drill|hot take|quiet reminder|field note|gear check|from the trail|today)\s*:\s*"
                 r"|^ok so+\s+|^reminder that\s+")


def template_of(text):
    """First six words of a post, without stock openers, links, hashtags and @names."""
    t = re.sub(r"https?://\S+|[#@]\w+", " ", text.lower().replace("’", "'"))
    t = " ".join(re.findall(r"[a-zà-ÿ0-9':]+", t))
    t = re.sub(STOCK_OPENERS, "", t)
    return " ".join(re.findall(r"[a-zà-ÿ']+", t)[:6])
