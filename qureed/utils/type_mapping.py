type_mapping = {
    "int": int,
    "float": float,
    "bool": bool,
    "cmplx": complex,
    "str": str,
    "char": lambda v: v if len(v) == 1 else ValueError("Value must be a single character")
}
