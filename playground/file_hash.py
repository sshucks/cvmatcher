import io, hashlib, hmac

if __name__ == "__main__":

    with open("./FBW-WebServices (HVD) Schnittstellenbeschreibung.pdf", "rb") as f:
        digest1 = hashlib.file_digest(f, "sha256")

    with open("./Tset.pdf", "rb") as f:
        digest2 = hashlib.file_digest(f, "sha256")
    
    hex1 = digest1.hexdigest()
    hex2 = digest2.hexdigest()
    
    print("not equal" if hex1 != hex2 else "equal")
    print(hex1)
    print(hex2)
    
    

