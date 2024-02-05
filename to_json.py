chars_dict = {"'": '"', 'False': 'false', 'True': 'true', 'None': 'null'}


def replace_chars(text):
    for char, new_char in chars_dict.items():
        text = text.replace(char, new_char)

    return text
