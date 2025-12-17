from __future__ import annotations
from pathlib import Path
import re, subprocess, os, shutil, tempfile, textwrap, urllib.request
import shlex

def ensure_dir(p: str|Path):
    Path(p).mkdir(parents=True, exist_ok=True)

def sanitize_filename(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", name)

def download_if_http(src: str, dst: Path):
    if src.startswith("http://") or src.startswith("https://"):
        urllib.request.urlretrieve(src, dst.as_posix())
    else:
        # Si es ruta local, copia
        shutil.copy2(src, dst)

def build_drawtext(text: str, pos: str) -> str:
    if not text:
        return ""
    # tipografía default; si hay DejaVuSans en sistema, mejor
    # Usar valores numéricos fijos para evitar problemas con expresiones complejas
    y_offset = {"top":150, "center":960, "bottom":1770}.get(pos, 1770)
    # caja semitransparente con coordenadas numéricas
    escaped_text = text.replace(":", "\\:").replace("'", "\\'")
    return (
        f"drawbox=x=0:y={y_offset-40}:w=1080:h=80:color=black@0.35:t=fill,"
        f"drawtext=text='{escaped_text}':fontcolor=white:fontsize=48:"
        f"box=0:shadowx=2:shadowy=2:x=540:y={y_offset-24}"
    )

def kenburns_expr(mode: str) -> str:
    # zoompan para 30 fps; zoom suave aprox. 3%–5% sobre la duración
    if mode == "slow-zoom-in":
        return "zoompan=z='min(zoom+0.0015,1.2)':d=1:s=1080x1920"
    if mode == "slow-zoom-out":
        return "zoompan=z='max(zoom-0.0015,1.0)':d=1:s=1080x1920"
    if mode == "pan-left":
        return "zoompan=z='1.05':x='iw*(1-on/300)':y='(ih-oh)/2':d=1:s=1080x1920"
    if mode == "pan-right":
        return "zoompan=z='1.05':x='iw*(on/300)':y='(ih-oh)/2':d=1:s=1080x1920"
    return "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2"

def run_ffmpeg(cmd: list[str]):
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"FFmpeg error: {proc.stderr[-800:]}")
    return proc

def vf_with_polish(base_vf: str, *, lut_path: str|None, fade_in_ms: int, fade_out_ms: int, total_s: int) -> str:
    vf = base_vf
    # LUT opcional
    if lut_path:
        vf = f"{vf},lut3d=file='{lut_path}'"
    # Fades globales sobre el video concatenado (aplicaremos en fase final)
    # Nota: el fade final se aplica tras concat; aquí devolvemos base y en compose sumamos fade a la etapa final.
    return vf

def af_with_polish(*, loudnorm: bool) -> list[str]:
    if loudnorm:
        # Valores típicos EBU R128; segunda pasada no imprescindible para MVP
        return ["-af", "loudnorm=I=-14:TP=-1.5:LRA=11"]
    return []

def overlay_logo_filter(logo_path: str, margin: int, scale_w: int) -> list[str]:
    # devuelve cadena de filtros complejos para overlay sobre el video final
    # Escala logo y posición en top-right con margen
    filt = (
        f"[1][0:v]scale2ref=w={scale_w}:h=-1[lg][base];"
        f"[base][lg]overlay=x=W-w-{margin}:y={margin}"
    )
    return ["-filter_complex", filt]

def fade_filter_args(total_s: int, fade_in_ms: int, fade_out_ms: int) -> list[str]:
    # aplica fade al video final
    fi = max(0, fade_in_ms)
    fo = max(0, fade_out_ms)
    # tiempos en frames a 30fps
    fin_frames = int((fi/1000)*30)
    fout_frames = int((fo/1000)*30)
    # fade in desde 0; fade out empieza a total_s - fade_out
    start_out = max(0, int((total_s*30) - fout_frames))
    vf = f"fade=t=in:st=0:n={fin_frames},fade=t=out:st={start_out/30:.3f}:n={fout_frames}"
    return ["-vf", vf]