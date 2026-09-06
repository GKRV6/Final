import os

dataset_path = r"C:\Users\NATHISH KRISHNA\Downloads\wafer_images_defects\wafer_images_defects"

classes = os.listdir(dataset_path)

print("Classes found:")
print()

total = 0

for class_name in classes:
    class_path = os.path.join(dataset_path, class_name)

    if os.path.isdir(class_path):
        count = len(os.listdir(class_path))
        print(class_name, ":", count)
        total += count

print()
print("Total images:", total)