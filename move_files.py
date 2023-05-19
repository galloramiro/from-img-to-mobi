import os
import shutil
from pathlib import Path, PosixPath


def get_path_directories(directory: str):
    mangas_directory = Path(__file__).parent
    base_directory_name =  mangas_directory.joinpath(directory)
    sub_directories_list = [
        sub_directory_name for sub_directory_name
        in base_directory_name.iterdir()
        if sub_directory_name.is_dir()
    ]
    return sub_directories_list


def move_images_to_base_dir(directory: PosixPath):
    relative_images_directory_str = "OEBPS/img/"
    images_directory = directory.joinpath(relative_images_directory_str)

    for image_full_path in images_directory.iterdir():
        try:
            shutil.copy2(image_full_path, directory)
        except shutil.SameFileError:
            continue

def remove_unused_folders(directory: PosixPath):
    sub_directories_list = [
        sub_directory_name for sub_directory_name
        in directory.iterdir()
        if sub_directory_name.is_dir()
    ]

    for sub_directory in sub_directories_list:
        shutil.rmtree(sub_directory)

    os.remove(directory.joinpath("mimetype"))

if __name__ == "__main__":
    one_punch_man_directory = "One Punch-Man"
    hunter_x_hunter_directory = "Hunter x Hunter"
    sub_directories = get_path_directories(directory=hunter_x_hunter_directory)

    for directory in sub_directories:
        move_images_to_base_dir(directory)
        remove_unused_folders(directory)