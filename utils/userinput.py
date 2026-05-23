def read_user_input() -> str:
    with open("user_input.txt", "r") as f:
        text = f.read()
    return text