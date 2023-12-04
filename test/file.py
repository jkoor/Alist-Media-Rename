import os


def generate_test_files(folder_path, file_count):
    """生成测试文件"""
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    for i in range(file_count):
        file_name = f"{i+1}.mp4"
        file_path = os.path.join(folder_path, file_name)
        with open(file_path, "w", encoding="UTF-8") as file:
            # 写入文件内容
            file.write("This is a test file.")


folder_path = "./test/aaa"
file_count = 10

generate_test_files(folder_path, file_count)
