import hashlib
import os
import logging
import argparse
import time

def checksums(filepath, use_sha1=False):
    #check MD5 and SHA-1 checksums, md5 by default since its faster and colisions are rare if random, second argument toggles SHA-1 check on or off
    md5 = hashlib.md5()
    sha1 = hashlib.sha1() if use_sha1 else None
    
    with open(filepath, 'rb') as f:
        while chunk := f.read(4096):
            md5.update(chunk)
            if use_sha1:
                sha1.update(chunk)
                
    return md5.hexdigest(), sha1.hexdigest() if use_sha1 else None
    
def are_identical(file1, file2, use_sha1=False):
    md5_f1, sha1_f1 = checksums(file1, use_sha1)
    md5_f2, sha1_f2 = checksums(file2, use_sha1)
    
    if md5_f1 != md5_f2:
        return False
    
    if use_sha1 and sha1_f1 != sha1_f2:
        return False
    
    return True

def copy_file(source, target):
    target_directory = os.path.dirname(target)
    
    if not os.path.exists(target_directory):
        os.makedirs(target_directory)
        logging.info(f"Created directory: {target_directory}")
        print(f"Created directory: {target_directory}")
    
    if not os.path.exists(target):
        logging.info(f"Creating file: {target}")
        print(f"Creating file: {target}")
    else:
        logging.info(f"File: {source} and file: {target} differ, updating.")
        print(f"File: {source} and file: {target} differ, updating.")
    with open(source, 'rb') as src, open(target, 'wb') as tgt:
        while chunk := src.read(4096):
            tgt.write(chunk)
            
    stat = os.stat(source)
    
    os.chmod(target, stat.st_mode)
    
    os.utime(target, (stat.st_atime, stat.st_mtime))

def sync(source, target, use_sha1 = False):
        if not os.path.exists(source):
            logging.error(f"Trying to sync folder '{source}', but folder does not exist.")
            print(f"Trying to sync folder '{source}', but folder does not exist.")
            return
        if not os.path.exists(target):
            os.makedirs(target)
            logging.info(f"Target directory does not exist. Created")
            print(f"Target directory does not exist. Created")
        
        for root, dirs, files in os.walk(source):
            relative_path = os.path.relpath(root, source)
            target_path = os.path.join(target, relative_path)
            for file in files:
                source_file = os.path.join(root, file)
                target_file = os.path.join(target_path, file)
                if not os.path.exists(target_file) or not are_identical(source_file, target_file, use_sha1):
                    copy_file(source_file, target_file)
                #else:
                    #logging.info(f"{source_file} and {target_file} are identical.")
                    #Logging this leads to a lot of clutter in log file if folder contains a lot of files.
        #remove any files in target that are not in source
        cleanup(source, target)

#recursively cleanup extra files in target directory
def cleanup(source_dir, target_dir):
    for item in os.listdir(target_dir):
        tgt_path = os.path.join(target_dir, item)
        src_path = os.path.join(source_dir, item)
        
        if not os.path.exists(src_path):
            if os.path.islink(tgt_path) or os.path.isfile(tgt_path):
                #is file and doesnt exist, log to file and console and remove.
                print(f"File {tgt_path} does not exist in source. Removing.")
                logging.info(f"File {tgt_path} does not exist in source. Removing.")
                os.remove(tgt_path)
            if os.path.isdir(tgt_path):
                #is a directory, recursively go into directory and remove files, then delete directory.
                print(f"Directory {tgt_path} does not exist in source. Removing.")
                logging.info(f"Directory {tgt_path} does not exist in source. Removing.")
                cleanup(src_path, tgt_path)
                os.rmdir(tgt_path)
        elif os.path.isdir(src_path) and os.path.isdir(tgt_path):
            #directory exists in both source and target, go into both to check for files to remove.
            cleanup(src_path, tgt_path)
                
#executes sync with x seconds of interval.
def task(timer, source, target, use_sha1):
    while True:
        start = time.perf_counter()
        sync(source, target, use_sha1)
        end = time.perf_counter()
        elapsed = end - start
        print(f"Sync took {elapsed:.4f} seconds.")
        time.sleep(timer)

def main():
    #get arguments from console.
    parser = argparse.ArgumentParser()
    parser.add_argument("source_folder", help="Source folder to sync.")
    parser.add_argument("target_folder", help="Target folder to sync.")
    parser.add_argument("--log", type=str, help="Path to log file.")
    parser.add_argument("--interval", type=int, help="Time in seconds between folder synchronization.")
    parser.add_argument("--sha", type=bool, default=False, help="Enable or disable sha_1.")
    args = parser.parse_args()
    
    #Logging setup
    logging.basicConfig(filename=args.log, filemode="w", level=logging.INFO, format="%(asctime)s | %(levelname)s %(message)s")
    logging.info(f"Arguments: {args.source_folder}, {args.target_folder}, --log {args.log}, --interval {args.interval}")

    try:
        task(args.interval, args.source_folder, args.target_folder, args.sha)
    except KeyboardInterrupt:
        print(f"Operation Cancelled.")

if __name__ == "__main__":
    main()
    
