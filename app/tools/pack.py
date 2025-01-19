import os
import zipfile

def pack_and_split(output_dir="output_chunks", chunk_size_mb=10, chunk_extension=".dat"):
    current_dir = os.getcwd()
    
    input_files = [f for f in os.listdir(current_dir) if f.endswith(".zip")]
    if not input_files:
        print("No zip files found in the current directory.")
        return
    
    os.makedirs(output_dir, exist_ok=True)
    
    archive_path = os.path.join(output_dir, "all_files.zip")
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for file in input_files:
            archive.write(file, os.path.basename(file))  # 
    
    chunk_size_bytes = chunk_size_mb * 1024 * 1024
    with open(archive_path, "rb") as f:
        chunk_index = 0
        while chunk := f.read(chunk_size_bytes):
            chunk_filename = os.path.join(output_dir, f"chunk_{chunk_index:03d}{chunk_extension}")
            with open(chunk_filename, "wb") as chunk_file:
                chunk_file.write(chunk)
            chunk_index += 1

    os.remove(archive_path)
    print(f"Chunks created in {output_dir}")

if __name__ == "__main__":
    pack_and_split()
