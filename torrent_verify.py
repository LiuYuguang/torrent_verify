import torrent_parser as tp
import hashlib
from pathlib import Path
import argparse
from tqdm import tqdm

class TorrentVerify(object):
    def __init__(self, torrent_path: Path, path: Path):
        self._torrent_data = tp.parse_torrent_file(torrent_path.absolute())
        self._chunk_size = self._torrent_data['info']['piece length']
        self._path = path

    @staticmethod
    def _hash(data: bytes, hexdigest: str) -> bool:
        h = hashlib.sha1()
        h.update(data)
        return h.hexdigest() == hexdigest

    def verify(self) -> tuple:
        with tqdm(total=len(self._torrent_data['info']['pieces'])) as t:
            pieces = iter(self._torrent_data['info']['pieces'])
            data = b''
            base_path = self._path.joinpath(self._torrent_data['info']['name'])
            if base_path.is_file():
                files = [{'length': self._torrent_data['info']['length'], 'path': []}]
            else:
                files = self._torrent_data['info']['files']
            for file in files:
                p = base_path
                for name in file['path']:
                    p = p.joinpath(name)
                if p.stat().st_size != file['length']:
                    raise Exception("{} length {}, expect {}".format(p, p.stat().st_size, file['length']))
                with p.open('rb', buffering=1024*1024) as f:
                    for chunk in iter(lambda: f.read(self._chunk_size), b''):
                        data += chunk
                        if len(data) >= self._chunk_size:
                            if TorrentVerify._hash(data[:self._chunk_size], next(pieces)):
                                t.update(1)
                            data = data[self._chunk_size:]
            if data:
                if TorrentVerify._hash(data, next(pieces)):
                    t.update(1)
            return (t.n, t.total)

def __main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "file", nargs="?", help="torrent file"
    )
    parser.add_argument(
        "--dir",
        "-d",
        default=Path.cwd(),
        help="verify files path, default " + str(Path.cwd()),
    )
    args = parser.parse_args()
    print(TorrentVerify(Path(args.file), Path(args.dir)).verify())

if __name__ == '__main__':
    __main()