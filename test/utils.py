import os
import shutil


class TestUtils:
    "测试工具类"

    @staticmethod
    def generate_random_files(folder_path: str, file_count: int, index: int, filename: str, extension: str):
        """随机生成媒体文件"""
        # 检查文件夹是否存在，如果不存在则创建它
        folder_path += filename
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        for i in range(index, file_count + index):
            # Generate a random file name
            file_name = f"{filename}_{i}{extension}"
            file_path = os.path.join(folder_path, file_name)

            # Create an empty file with the generated name
            with open(file_path, "w"):
                pass

    @staticmethod
    def delete_folder(folderpath):
        """删除指定文件夹"""
        if os.path.exists(folderpath):
            shutil.rmtree(folderpath)
