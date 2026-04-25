from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

CENTRAL_MODULE = Path(__file__).resolve().parents[2] / "tnea_lib" / "raw_stream.py"
SPEC = spec_from_file_location("_central_raw_stream", CENTRAL_MODULE)
if SPEC is None or SPEC.loader is None:
    raise ImportError(f"Could not load central raw stream module at {CENTRAL_MODULE}")
MODULE = module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

decode_hex_string = MODULE.decode_hex_string
extract_blocks_from_pdf = MODULE.extract_blocks_from_pdf
text_quality_score = MODULE.text_quality_score

__all__ = ["decode_hex_string", "extract_blocks_from_pdf", "text_quality_score"]
