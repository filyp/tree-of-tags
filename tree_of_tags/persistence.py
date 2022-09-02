import pickle
from pathlib import Path

data_folder = Path(__file__).parent.parent / "data"


def save_object(object, name):
    filename = data_folder / f"{name}.pkl"
    with open(filename, "wb") as f:
        pickle.dump(object, f)


def load_object(name):
    """
    returns object with given name
    if it doesn't exist, return None
    """
    filename = data_folder / f"{name}.pkl"
    if not filename.exists():
        return None
    with open(filename, "rb") as f:
        return pickle.load(f)
