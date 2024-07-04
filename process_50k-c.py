# pip install zipfile36
import os
import zipfile
import shutil

def unzip_files(source_dir, dest_dir):
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
    
    skipped_files = 0

    for root, dirs, files in os.walk(source_dir):
        for dir in dirs:
            subfolder_path = os.path.join(root, dir)
            for file in os.listdir(subfolder_path):
                if file.endswith(".zip"):
                    file_path = os.path.join(subfolder_path, file)
                    try:
                        with zipfile.ZipFile(file_path, 'r') as zip_ref:
                            for member in zip_ref.namelist():
                                extracted_path = os.path.join(dest_dir, member)
                                if os.path.exists(extracted_path) and os.path.isdir(extracted_path):
                                    continue
                                zip_ref.extract(member, dest_dir)
                        print(f"Unzipped: {file_path}")
                    except zipfile.BadZipFile:
                        print(f"Bad zip file: {file_path}")
                        skipped_files += 1
                    except IsADirectoryError:
                        print(f"Is a directory error for file: {file_path}")
                        skipped_files += 1
                    except Exception as e:
                        print(f"Error unzipping {file_path}: {e}")
                        skipped_files += 1
            
            # Permanently delete the subfolder
            try:
                shutil.rmtree(subfolder_path, ignore_errors=True)
                print(f"Deleted the subfolder: {subfolder_path}")
            except Exception as e:
                print(f"Error deleting the subfolder: {e}")

    print(f"Total skipped ZIP files: {skipped_files}")

if __name__ == "__main__":
    source_directory = "/Users/philippsommerhalter/sig/java-corpus/50K-c-zipped"
    destination_directory = "/Users/philippsommerhalter/sig/java-corpus/50K-c"
    unzip_files(source_directory, destination_directory)
