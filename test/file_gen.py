import os


def generate_random_files(folder_path, file_count, index, filename, extension):
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


def delete_files(folder_path):
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            os.remove(os.path.join(root, file))


# Example usage
if __name__ == "__main__":
    number = 12
    index = 1
    generate_random_files("./test/files/", number, index, "test", ".mp4")
    generate_random_files("./test/files/", number, index, "test", ".ass")
