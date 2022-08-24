import pickle
from pathlib import Path

data_folder = Path(__file__).parent.parent / "data"


def save_forum_data(posts, tags):
    filename = data_folder / "forum_data.pkl"
    with open(filename, "wb") as f:
        pickle.dump((posts, tags), f)


def load_forum_data():
    """
    returns (posts, tags)
    if the data doesn't exist, return None
    """
    filename = data_folder / "forum_data.pkl"
    if not filename.exists():
        return None
    with open(filename, "rb") as f:
        return pickle.load(f)


def save_tree(tree, alpha):
    filename = data_folder / f"tree_{alpha}.pkl"
    with open(filename, "wb") as f:
        pickle.dump(tree, f)


def load_tree(alpha):
    """
    if tree doesn't exist, return None
    """
    filename = data_folder / f"tree_{alpha}.pkl"
    if not filename.exists():
        return None
    with open(filename, "rb") as f:
        return pickle.load(f)
