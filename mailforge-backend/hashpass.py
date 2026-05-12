import bcrypt

plain = "4463985@Med99"  # choose your dev password
hashed = bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(12)).decode("utf-8")
print(hashed)