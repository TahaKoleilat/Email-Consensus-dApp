import gnupg
import os

path = os.path.join(os.getcwd(), "PGP FILE")

gpg = gnupg.GPG(gnupghome=path)
gpg.encoding = 'utf-8'
#Used to create a PGP Public and Private Key
input_data = gpg.gen_key_input(name_email = "",key_type="RSA", key_length=1024,passphrase = "")
key = gpg.gen_key(input_data)
print(key)