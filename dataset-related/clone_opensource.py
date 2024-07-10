import os
import sys
import subprocess

def clone_repos(file_path, dest_dir):
    # Check if the text file exists
    if not os.path.isfile(file_path):
        print(f"The file {file_path} does not exist.")
        return

    # Check if the destination directory exists, create if not
    if not os.path.isdir(dest_dir):
        print(f"The directory {dest_dir} does not exist. Creating it now.")
        os.makedirs(dest_dir)

    # Read the file line by line and clone each repository
    with open(file_path, 'r') as file:
        for line in file:
            repo_url = line.strip()
            if repo_url:
                full_url = f"{repo_url}.git"
                print(f"Cloning {full_url} into {dest_dir}")
                subprocess.run(['git', 'clone', full_url], cwd=dest_dir)

    print(f"All repositories have been cloned to {dest_dir}.")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python clone_repos.py <path_to_txt_file> <destination_directory>")
        sys.exit(1)

    file_path = sys.argv[1]
    dest_dir = sys.argv[2]

    clone_repos(file_path, dest_dir)

