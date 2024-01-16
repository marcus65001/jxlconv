from pyvips import Image
import os
from zipfile import ZipFile
import tarfile
import io
from pathlib import Path
from tqdm import tqdm
from multiprocessing import Pool
import argparse
import psutil


# vips
vips_path = os.environ['VIPS_PATH']
os.environ['PATH'] = vips_path + ';' + os.environ['PATH']


class Archive():
    def __init__(self) -> None:
        pass

    def process():
        pass

    def add():
        pass


class TarArchive(Archive):
    def __init__(self, fp, mode="w") -> None:
        super().__init__()
        self.file = tarfile.open(fp, mode)

    def add(self, buf, fname, size):
        tinf = tarfile.TarInfo(name=fname)
        tinf.size = size
        self.file.addfile(tinf, buf)
        del buf

    def addfile(self, fp: Path, root: Path):
        self.file.add(str(fp), str(fp.relative_to(root)))

    def close(self):
        self.file.close()


def encode_jxl(imgd, resize=None, **kwarg):
    img = Image.new_from_buffer(imgd, "")
    if resize:
        w, h = resize.split('x')
        w, h = int(w), int(h)
        iw, ih = img.width, img.height
        scale = max(iw/w, ih/h)
        if scale > 1:
            img = img.resize(1/scale)
    jbuf = img.jxlsave_buffer(**kwarg)
    buf = io.BytesIO(jbuf)
    return buf


def make_thumb(thumb, w=640, h=320):
    img = Image.new_from_buffer(thumb, "")
    iw, ih = img.width, img.height
    scale = max(iw/w, ih/h)
    if scale > 1:
        img = img.resize(1/scale)
    return img.webpsave_buffer(Q=60)


def process_zip(fp, f_encode, f_nxt, f_encode_param, encoder="jxl"):
    z = ZipFile(fp)
    linf = z.infolist()
    thumb = linf[0]
    for finfo in tqdm(linf):
        if finfo.is_dir():
            continue
        if finfo.file_size < 2**30:
            if os.path.splitext(finfo.filename)[-1] in {".jpg", ".png", ".bmp"}:
                with z.open(finfo) as f:
                    fcont = f.read()
                encoded = f_encode(fcont, **f_encode_param)
                del fcont
                f_nxt(
                    encoded, f"{os.path.splitext(finfo.filename)[0]}.{encoder}", encoded.getbuffer().nbytes)
                if finfo.file_size > thumb.file_size:
                    thumb = finfo
            else:
                with z.open(finfo) as fcont:
                    f_nxt(fcont, finfo.filename, finfo.file_size)
        else:
            raise f"Large file {finfo}"
    with z.open(thumb) as f:
        thumb_d = f.read()
    z.close()
    return make_thumb(thumb_d)


def write_thumb(thumb, out_path):
    with open(out_path.with_stem(f"{out_path.stem}.thumb").with_suffix(".webp"), "wb") as f:
        f.write(thumb)
        del thumb


def process_archive(fp, out_path, encode_param):
    print(f"{'-'*20} Processing archive \"{fp}\"")
    tar_ac = TarArchive(out_path)
    if fp.suffix == ".zip":
        thumb = process_zip(fp, encode_jxl, tar_ac.add, encode_param)
    elif fp.suffix == ".rar":
        thumb = process_rar()
    write_thumb(thumb, out_path)
    tar_ac.close()


def process_dir(path: Path, out_path, encode_param):
    tar_ac = TarArchive(out_path)
    print(f"{'-'*20} Processing directory \"{path}\"")
    thumb = (0, None)
    for fp in tqdm(path.glob("**/*")):
        if fp.suffix in source_image_types:
            if (ts := fp.stat().st_size) > thumb[0]:
                thumb = (ts, fp)
            with open(fp, "rb") as f:
                ibuf = f.read()
            encoded = encode_jxl(ibuf, **encode_param)
            del ibuf
            tar_ac.add(encoded, str(fp.relative_to(path).with_suffix(
                ".jxl")), encoded.getbuffer().nbytes)
        elif fp.is_file():
            tar_ac.addfile(fp, path)
    if thumb[1]:
        with open(thumb[1], "rb") as thumbf:
            thumbd = make_thumb(thumbf.read())
        write_thumb(thumbd, out_path)
    tar_ac.close()


source_archive_types = {".zip", ".rar"}
source_image_types = {".jpg", ".jpeg", ".png", ".bmp"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog='JXLConv',
        description='Convert jpeg to jpeg-xl')
    parser.add_argument("input", type=Path)
    parser.add_argument("--output_dir", type=Path)
    parser.add_argument("--temp_dir", type=Path)
    # general
    parser.add_argument("--verify", type=bool, default=True)
    parser.add_argument("--enc", type=str, default="jxl")
    parser.add_argument("--thumbnail", type=bool, default=True)
    # subroutine
    parser.add_argument("--thread", type=int, default=16)
    # resize
    parser.add_argument("--resize", type=str, default=None)
    # compression
    parser.add_argument("--level", type=int, default=7)
    # jxl parameter
    parser.add_argument("--effort", type=int)
    parser.add_argument("--distance", type=float)
    args = parser.parse_args()

    proc = psutil.Process(os.getpid())
    proc.nice(psutil.HIGH_PRIORITY_CLASS)

    encode_param = {"distance": args.distance, "effort": args.effort,
                    "lossless": (args.distance == 0), "resize": args.resize}
    if args.input.is_dir():
        out_path = args.output_dir or args.input
        for fp in args.input.iterdir():
            if fp.suffix in source_archive_types:
                process_archive(
                    fp, out_path/(fp.with_suffix(".tar").name), encode_param)
            if fp.is_dir():
                process_dir(fp, fp.absolute().with_suffix(
                    ".tar"), encode_param)
    else:
        assert args.input.suffix in source_archive_types
        out_path = args.output_dir or args.input.parent
        out_archive_path = out_path/(args.input.with_suffix(".tar").name)
        process_archive(args.input, out_archive_path, encode_param)
