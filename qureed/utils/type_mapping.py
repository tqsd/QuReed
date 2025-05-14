type_mapping = {
    "int": ((int,), int),
    "float": ((int, float), float),  # Accepts int/float, coerce to float
    "bool": ((bool,), bool),
    "cmplx": ((int, float, complex), complex),
    "str": ((str,), str),
}
