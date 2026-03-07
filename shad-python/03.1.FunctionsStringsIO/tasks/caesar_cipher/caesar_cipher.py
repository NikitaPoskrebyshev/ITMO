from string import punctuation


def caesar_encrypt(message: str, n: int) -> str:
    """Encrypt message using caesar cipher

    :param message: message to encrypt
    :param n: shift
    :return: encrypted message
    """
    words: list[str] = message.split()
    result: list[str] = []
    for word in words:
        letters: list[str] = list(word)
        for i in range(len(letters)):
            x: str = letters[i]
            if x in punctuation:
                continue
            if x.islower():
                letters[i] = chr(ord('a') + (ord(x) - ord('a') + n) % 26)
            else:
                letters[i] = chr(ord('A') + (ord(x) - ord('A') + n) % 26)
        result.append(''.join(letters))
    return ' '.join(result)
