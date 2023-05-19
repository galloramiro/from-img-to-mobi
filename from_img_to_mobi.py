import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List
import xml.etree.ElementTree as ET


@dataclass
class Metadata:
    series: str
    volume: str
    writer: str
    genre: str
    publisher: str
    penciller: Optional[str] = None
    page_count: Optional[int] = None


class ImagesToMobiService:

    @classmethod
    def transform_one_folder_into_mobi(cls, folder_directory: Path, metadata: Metadata) -> Path:
        # Update metadata
        page_count = cls._get_page_count(directory=folder_directory)
        metadata.page_count = page_count
        volume = cls._get_and_clean_volume(directory=folder_directory)
        metadata.volume = volume

        # Create XML Info
        cls._create_xml_info(directory=folder_directory, metadata=metadata)

        # Create CBZ
        cbz_path = cls._create_cbz_from_path(directory=folder_directory, volume=metadata.volume)

        # Transform into MOBI
        file_path = cls._from_cbz_to_mobi(file_directory=cbz_path, metadata=metadata)
        cls._clean_cbz_file(file_path=cbz_path)

        return file_path

    @classmethod
    def transform_all_sub_directories_into_mobi(cls, base_directory: Path, metadata: Metadata) -> List[Path]:
        sub_directories = sorted([dir_name for dir_name in base_directory.iterdir() if dir_name.is_dir()])

        mobi_directories_list = []

        for directory in sub_directories:
            mobi_directory = cls.transform_one_folder_into_mobi(folder_directory=directory, metadata=metadata)
            mobi_directories_list.append(mobi_directory)

        return mobi_directories_list


    @staticmethod
    def _get_and_clean_volume(directory: Path) -> str:
        chapter = str(directory).split("/")[-1]
        chapter_is_a_middle_chapter = "." in chapter
        if chapter_is_a_middle_chapter:
            chapter = chapter.zfill(6)
        else:
            chapter = chapter.zfill(4)
        return f"{chapter}"

    @staticmethod
    def _create_xml_info(directory: Path, metadata: Metadata) -> Path:
        # https://github.com/ciromattia/kcc/wiki/Metadata
        # https://github.com/ciromattia/kcc/wiki/ComicRack-metadata
        # https://gist.github.com/vaemendis/9f3ed374f215532d12bda3e812a130e6
        print("Start composing metadata")

        comic_info_attributes = {
            "xmlns:xsd":"http://www.w3.org/2001/XMLSchema",
            "xmlns:xsi":"http://www.w3.org/2001/XMLSchema-instance",
        }
        comic_info = ET.Element('ComicInfo', attrib=comic_info_attributes)
        ET.SubElement(comic_info, "Series").text = metadata.series
        ET.SubElement(comic_info, "Volume").text = metadata.volume
        ET.SubElement(comic_info, "Writer").text = metadata.writer
        ET.SubElement(comic_info, "Genre").text = metadata.genre
        ET.SubElement(comic_info, "Publisher").text = metadata.publisher

        if metadata.penciller:
            ET.SubElement(comic_info, "Penciller").text = metadata.penciller

        if metadata.page_count:
            ET.SubElement(comic_info, "PageCount").text = str(metadata.page_count)

        tree = ET.ElementTree(comic_info)
        ET.indent(tree, space="\t", level=0)

        save_path_file = directory.joinpath("ComicInfo.xml")
        with open(save_path_file, "w") as f:
            tree.write(save_path_file, encoding="utf-8", )

        print("Finish composing metadata")
        print(f"{save_path_file}")
        print(f"{metadata.series} - {metadata.volume}")

        return save_path_file

    @staticmethod
    def _create_cbz_from_path(directory: Path, volume: str) -> Path:
        file_path = directory.parent.joinpath(f"{volume}.zip")
        command_list = ["7z", "a", file_path, f"{directory}"]
        subprocess.run(command_list)

        cbz_name = str(file_path).replace(".zip", ".cbz")
        os.rename(file_path, cbz_name)
        return Path(cbz_name)

    @staticmethod
    def _from_cbz_to_mobi(file_directory: Path, metadata: Metadata) -> Path:
        print(f"\n\nStart processing from cbz to mobi: {metadata.series} - {metadata.volume}")
        command_list = ["flatpak", "run", "--command=kcc-c2e", "io.github.ciromattia.kcc", "--profile=KPW", "--manga-style", "--format=MOBI", str(file_directory)]
        # command_list = ["kcc-c2e", "--profile=KPW", "--manga-style", "--format=MOBI", str(file_directory)]
        # " run --command=kcc-c2e io.github.ciromattia.kc"

        # command_list = [
        #     "docker", "run", "--rm", f"--volume=`{mangas_directory}:/app`", "ghcr.io/ciromattia/kcc:latest", "/bin/bash", "-c"
        #     f"--profile=KPW5 --manga-style --format=MOBI './{str(file_directory)}'"
        # ]
        print(" ".join(command_list))
        subprocess.run(command_list)
        print()
        return file_directory

    @staticmethod
    def _get_page_count(directory: Path) -> int:
        images = [image for image in directory.iterdir() if str(image).endswith(".jpg")]
        return len(images)

    @classmethod
    def _clean_cbz_file(cls, file_path: Path) -> None:
        os.remove(file_path)


def get_directory_by_name(sub_directories: List[Path], directory_name: str):
    return list(filter(lambda dir_name: str(dir_name).endswith(directory_name), sub_directories))[0]


def transform_only_one_directory(manga_directory: Path, metadata: Metadata, subdirectory_name: str):
    sub_directories = sorted([dir_name for dir_name in manga_directory.iterdir() if dir_name.is_dir()])
    manga_directory = get_directory_by_name(sub_directories=sub_directories, directory_name=subdirectory_name)

    ImagesToMobiService.transform_one_folder_into_mobi(
        folder_directory=manga_directory,
        metadata=metadata,
    )


def transform_one_punch_man(mangas_directory: Path):
    one_punch_man_directory = mangas_directory.joinpath("One Punch-Man")
    one_punch_man_metadata = Metadata(
        series="One Punch Man",
        volume="",
        writer="One",
        genre="Manga",
        publisher="Jump Comics",
        penciller="Yusuke Murata"
    )
    # ImagesToMobiService.transform_all_sub_directories_into_mobi(
    #     base_directory=one_punch_man_directory,
    #     metadata=one_punch_man_metadata,
    # )

    transform_only_one_directory(
        manga_directory=one_punch_man_directory,
        metadata=one_punch_man_metadata,
        subdirectory_name="229"
    )

def transform_one_piece(mangas_directory: Path):
    one_piece_directory = mangas_directory.joinpath("One Piece")
    one_piece_metadata = Metadata(
        series="One Piece",
        volume="",
        writer="Eiichirō Oda",
        genre="Manga",
        publisher="Jump Comics"
    )
    # ImagesToMobiService.transform_all_sub_directories_into_mobi(
    #     base_directory=one_piece_directory,
    #     metadata=one_piece_metadata,
    # )

    transform_only_one_directory(
        manga_directory=one_piece_directory,
        metadata=one_piece_metadata,
        subdirectory_name="1084 :                     Intento de asesinato de un Tenryuubito"
    )

def transform_hunter_x_hunter(mangas_directory: Path):
    hunter_x_hunter_directory = mangas_directory.joinpath("Hunter x Hunter")
    hunter_x_hunter_metadata = Metadata(
        series="Hunter x Hunter",
        volume="",
        writer="Yoshihiro Togashi",
        genre="Manga",
        publisher="Jump Comics"
    )
    ImagesToMobiService.transform_all_sub_directories_into_mobi(
        base_directory=hunter_x_hunter_directory,
        metadata=hunter_x_hunter_metadata,
    )

    # transform_only_one_directory(
    #     manga_directory=hunter_x_hunter_directory,
    #     metadata=hunter_x_hunter_metadata,
    #     subdirectory_name="224"
    # )


def transform_sakamoto_days(mangas_directory: Path):
    sakamoto_days_directory = mangas_directory.joinpath("Sakamoto Days")
    sakamoto_days_metadata = Metadata(
        series="Sakamoto Days",
        volume="",
        writer="Yuuto Suzuki",
        genre="Manga",
        publisher="Jump Comics"
    )
    # ImagesToMobiService.transform_all_sub_directories_into_mobi(
    #     base_directory=sakamoto_days_directory,
    #     metadata=sakamoto_days_metadata,
    # )

    transform_only_one_directory(
        manga_directory=sakamoto_days_directory,
        metadata=sakamoto_days_metadata,
        subdirectory_name="114"
    )

if __name__ == "__main__":
    mangas_directory = Path(__file__).parent
    # mangas_directory = Path("./")
    # import ipdb; ipdb.set_trace()

    # transform_one_punch_man(mangas_directory)
    transform_one_piece(mangas_directory)
    # transform_hunter_x_hunter(mangas_directory)
    # transform_sakamoto_days(mangas_directory)