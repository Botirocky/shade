import json
import os
from pathlib import Path

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

FEJ = b"ARNYEK-KJ1"


class RosszJelszo(Exception):
    pass


def _kulcs(jelszo: str, so: bytes) -> bytes:
    return Scrypt(salt=so, length=32, n=2**15, r=8, p=1).derive(jelszo.encode())


class Szef:
    def __init__(self, fajl: Path):
        self.fajl = fajl
        self.kulcs: bytes | None = None
        self.so = b""
        self.lista: list[dict] = []

    def letezik(self) -> bool:
        return self.fajl.exists()

    def nyitva(self) -> bool:
        return self.kulcs is not None

    def felold(self, jelszo: str):
        if not self.letezik():
            self.so = os.urandom(16)
            self.kulcs = _kulcs(jelszo, self.so)
            self.lista = []
            return
        adat = self.fajl.read_bytes()
        if not adat.startswith(FEJ):
            raise RosszJelszo("Ismeretlen fájlformátum")
        so, nonce, titkos = adat[len(FEJ):len(FEJ) + 16], adat[len(FEJ) + 16:len(FEJ) + 28], adat[len(FEJ) + 28:]
        kulcs = _kulcs(jelszo, so)
        try:
            self.lista = json.loads(AESGCM(kulcs).decrypt(nonce, titkos, FEJ))
        except InvalidTag:
            raise RosszJelszo("Rossz jelszó") from None
        self.so, self.kulcs = so, kulcs

    def zar(self):
        self.kulcs, self.lista = None, []

    def ment(self):
        assert self.kulcs is not None
        nonce = os.urandom(12)
        titkos = AESGCM(self.kulcs).encrypt(nonce, json.dumps(self.lista, ensure_ascii=False).encode(), FEJ)
        self.fajl.parent.mkdir(parents=True, exist_ok=True)
        ideiglenes = self.fajl.with_suffix(".uj")
        fd = os.open(ideiglenes, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "wb") as f:
            f.write(FEJ + self.so + nonce + titkos)
        ideiglenes.replace(self.fajl)

    def hozzaad(self, cim: str, url: str) -> bool:
        if any(k["url"] == url for k in self.lista):
            return False
        self.lista.append({"cim": cim or url, "url": url})
        self.ment()
        return True

    def torol(self, i: int):
        del self.lista[i]
        self.ment()


if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "kj.bin"
        s = Szef(f)
        s.felold("titok")
        assert s.hozzaad("Telex", "https://telex.hu")
        assert not s.hozzaad("Telex", "https://telex.hu")
        assert b"telex" not in f.read_bytes()
        assert oct(f.stat().st_mode)[-3:] == "600"
        s.zar()
        try:
            s.felold("rossz")
            raise AssertionError("rossz jelszóval nyílt")
        except RosszJelszo:
            pass
        assert not s.nyitva()
        s.felold("titok")
        assert s.lista == [{"cim": "Telex", "url": "https://telex.hu"}]
        s.torol(0)
        s.zar()
        s.felold("titok")
        assert s.lista == []
    print("konyvjelzo: minden teszt ok")
